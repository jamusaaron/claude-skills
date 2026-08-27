#!/usr/bin/env python3
"""Research gap and coverage analyzer.

Compares declared research questions (from a plan) against an evidence store
and claim matrix. Reports thin coverage, missing source types, recency holes,
geographic skew, and recommended next queries.

Usage:
    python coverage_analyzer.py --plan plan.json --store store.json
    python coverage_analyzer.py --questions Q1,Q2,Q3 --store store.jsonl --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


SOURCE_CLASSES = [
    "primary", "government", "academic", "dataset", "news", "think-tank",
    "filing", "legislation", "judgment", "preprint", "social", "blog", "other",
]
CLASS_ALIASES = {
    "gov": "government",
    "official": "government",
    "paper": "academic",
    "journal": "academic",
    "meta-analysis": "academic",
    "rct": "academic",
    "webpage": "other",
    "document": "other",
    "opinion": "blog",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_any(path: str) -> Any:
    text = open(path, "r", encoding="utf-8").read().strip()
    if path.endswith(".jsonl"):
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def records_from(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("evidence", "records", "items", "sources", "results", "matrix"):
            if isinstance(data.get(key), list):
                return [x for x in data[key] if isinstance(x, dict)]
        return [data]
    return []


def questions_from_plan(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    qs = plan.get("questions") or []
    out = []
    for q in qs:
        if isinstance(q, str):
            out.append({"id": q, "text": q, "priority": "supporting"})
        else:
            out.append({
                "id": q.get("id") or q.get("qid"),
                "text": q.get("text") or "",
                "priority": q.get("priority") or "supporting",
                "evidence_types": q.get("evidence_types") or [],
            })
    return out


def classify(rec: Dict[str, Any]) -> str:
    raw = (rec.get("source_type") or rec.get("type") or rec.get("band") or "").lower()
    raw = CLASS_ALIASES.get(raw, raw)
    if raw in SOURCE_CLASSES:
        return raw
    url = rec.get("url") or ""
    host = ""
    try:
        host = urlparse(url if "://" in url else f"https://{url}").netloc.lower()
    except ValueError:
        host = ""
    if host.startswith("www."):
        host = host[4:]
    if host.endswith(".gov") or host.endswith(".gov.au") or host.endswith(".gov.uk") or ".europa.eu" in host:
        return "government"
    if "arxiv.org" in host or "ssrn.com" in host:
        return "preprint"
    if any(x in host for x in ("nature.com", "nih.gov", "who.int", "jstor.org", "ieee.org", "acm.org")):
        return "academic"
    if any(x in host for x in ("sec.gov", "asic.gov.au")):
        return "filing"
    return "other"


def year_of(rec: Dict[str, Any]) -> Optional[int]:
    for key in ("published", "year", "date"):
        val = rec.get(key)
        if not val:
            continue
        text = str(val)
        for i, ch in enumerate(text):
            if ch.isdigit() and i + 4 <= len(text) and text[i:i + 4].isdigit():
                year = int(text[i:i + 4])
                if 1900 <= year <= 2100:
                    return year
    return None


def question_ids_of(rec: Dict[str, Any]) -> List[str]:
    ids = []
    if rec.get("question_id"):
        ids.append(str(rec["question_id"]))
    if rec.get("question_ids"):
        ids.extend(str(x) for x in rec["question_ids"])
    claims = rec.get("claims") or []
    if isinstance(claims, list):
        for c in claims:
            if isinstance(c, dict) and c.get("question_id"):
                ids.append(str(c["question_id"]))
    return list(dict.fromkeys(ids))


def analyze(
    questions: List[Dict[str, Any]],
    records: List[Dict[str, Any]],
    as_of_year: int,
    min_sources: int,
) -> Dict[str, Any]:
    by_q: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    unmapped = []
    classes = Counter()
    years = Counter()
    hosts = Counter()
    bands = Counter()

    for rec in records:
        klass = classify(rec)
        classes[klass] += 1
        y = year_of(rec)
        if y:
            years[y] += 1
        url = rec.get("url") or ""
        try:
            host = urlparse(url if "://" in url else f"https://{url}").netloc.lower()
        except ValueError:
            host = ""
        if host.startswith("www."):
            host = host[4:]
        if host:
            hosts[host] += 1
        band = ((rec.get("credibility") or {}).get("band") or rec.get("band") or "unknown")
        bands[str(band).lower()] += 1
        qids = question_ids_of(rec)
        if not qids:
            unmapped.append(rec.get("id") or rec.get("title") or rec.get("url") or "unknown")
        for qid in qids:
            by_q[qid].append(rec)

    q_rows = []
    gaps = []
    for q in questions:
        qid = q["id"]
        attached = by_q.get(qid, [])
        n = len(attached)
        types_present = sorted({classify(r) for r in attached})
        needed = q.get("evidence_types") or []
        missing_types = []
        for need in needed:
            token = need.split()[0].lower()
            token = CLASS_ALIASES.get(token, token)
            if token in SOURCE_CLASSES and token not in types_present:
                missing_types.append(need)
        recent = sum(1 for r in attached if (year_of(r) or 0) >= as_of_year - 3)
        highish = sum(
            1
            for r in attached
            if str((r.get("credibility") or {}).get("band") or r.get("band") or "").lower()
            in {"high", "medium-high"}
        )
        coverage_pct = min(100, int(round(100 * n / max(min_sources, 1)))) if min_sources else 0
        if n == 0:
            status = "empty"
        elif n < min_sources or highish == 0:
            status = "thin"
        elif missing_types:
            status = "imbalanced"
        else:
            status = "adequate"
        row = {
            "id": qid,
            "text": q.get("text"),
            "priority": q.get("priority"),
            "source_count": n,
            "high_integrity_count": highish,
            "recent_count": recent,
            "types_present": types_present,
            "missing_types": missing_types,
            "coverage_pct_vs_min": min(100, int(round(100 * min(n, min_sources) / max(min_sources, 1)))),
            "status": status,
        }
        q_rows.append(row)
        if status != "adequate":
            gaps.append({
                "question_id": qid,
                "status": status,
                "why": (
                    "No sources mapped"
                    if status == "empty"
                    else f"Fewer than {min_sources} sources or no high-integrity source"
                    if status == "thin"
                    else f"Missing source classes: {', '.join(missing_types)}"
                ),
                "next_actions": next_actions(q, row),
            })

    declared_ids = {q["id"] for q in questions}
    orphan_q = sorted(set(by_q) - declared_ids)

    diversity = 0.0
    if records:
        # Inverse-Herfindahl on hosts as a simple diversity proxy
        total = sum(hosts.values()) or 1
        hhi = sum((c / total) ** 2 for c in hosts.values())
        diversity = round(1.0 - hhi, 3)

    stale = [y for y in years if y < as_of_year - 7]
    recs_needed = {
        "primary_or_gov": classes["primary"] + classes["government"] + classes["legislation"] + classes["judgment"] + classes["dataset"] + classes["filing"],
        "academic": classes["academic"] + classes["preprint"],
        "secondary": classes["news"] + classes["think-tank"] + classes["blog"] + classes["social"],
    }

    return {
        "skill": "deep-research",
        "artifact": "coverage_report",
        "generated_at": utc_now(),
        "as_of_year": as_of_year,
        "min_sources_per_question": min_sources,
        "summary": {
            "questions": len(questions),
            "records": len(records),
            "unmapped_records": len(unmapped),
            "empty_questions": sum(1 for r in q_rows if r["status"] == "empty"),
            "thin_questions": sum(1 for r in q_rows if r["status"] == "thin"),
            "adequate_questions": sum(1 for r in q_rows if r["status"] == "adequate"),
            "publisher_diversity": diversity,
            "source_classes": dict(classes),
            "band_mix": dict(bands),
            "mix": recs_needed,
        },
        "questions": q_rows,
        "gaps": gaps,
        "unmapped_record_ids": unmapped[:50],
        "orphan_question_ids": orphan_q,
        "year_histogram": dict(sorted(years.items())),
        "stale_year_buckets": stale,
        "top_hosts": hosts.most_common(12),
        "recommendations": global_recs(q_rows, classes, diversity, unmapped),
    }


def next_actions(question: Dict[str, Any], row: Dict[str, Any]) -> List[str]:
    actions = []
    qtext = question.get("text") or question["id"]
    if row["status"] == "empty":
        actions.append(f"Run query_expander.py on: {qtext}")
        actions.append("Search a government pack and an academic pack before news.")
    if row["high_integrity_count"] == 0:
        actions.append("Locate a primary document, dataset, or official statistic.")
    if row["recent_count"] == 0 and row["source_count"]:
        actions.append("Add a source from the last 3 years to catch recency shifts.")
    for missing in row["missing_types"][:3]:
        actions.append(f"Acquire evidence type: {missing}")
    return actions or ["Targeted verification browse of the best current lead."]


def global_recs(rows: List[Dict[str, Any]], classes: Counter, diversity: float, unmapped: List[str]) -> List[str]:
    recs = []
    if any(r["status"] == "empty" for r in rows):
        recs.append("Empty questions remain — do not synthesize a confident answer yet.")
    if classes["social"] + classes["blog"] > (classes["government"] + classes["academic"] + classes["primary"]):
        recs.append("Secondary/social sources dominate; rebalance toward primary and official sources.")
    if diversity < 0.45:
        recs.append("Publisher concentration is high; expand site: packs to reduce shared provenance.")
    if unmapped:
        recs.append("Some evidence is not mapped to a question — tag question_id before synthesis.")
    if not recs:
        recs.append("Coverage is adequate on declared questions; proceed to skeptic/challenge pass.")
    return recs


def format_text(payload: Dict[str, Any]) -> str:
    s = payload["summary"]
    lines = [
        "=" * 72,
        "RESEARCH COVERAGE REPORT",
        "=" * 72,
        f"Generated: {payload['generated_at']}   as_of_year={payload['as_of_year']}",
        f"Questions: {s['questions']}  Records: {s['records']}  Unmapped: {s['unmapped_records']}",
        f"Adequate={s['adequate_questions']}  Thin={s['thin_questions']}  Empty={s['empty_questions']}",
        f"Publisher diversity: {s['publisher_diversity']}",
        "",
        f"{'QID':6} {'STAT':12} {'N':>3} {'HI':>3}  TEXT",
        "-" * 72,
    ]
    for q in payload["questions"]:
        text = (q.get("text") or "")[:52]
        lines.append(f"{str(q['id'])[:6]:6} {q['status']:12} {q['source_count']:3} {q['high_integrity_count']:3}  {text}")
    if payload["gaps"]:
        lines += ["", "GAPS"]
        for g in payload["gaps"]:
            lines.append(f"  [{g['question_id']}] {g['why']}")
            for a in g["next_actions"][:3]:
                lines.append(f"      → {a}")
    lines += ["", "RECOMMENDATIONS"]
    for r in payload["recommendations"]:
        lines.append(f"  - {r}")
    lines += ["", "=" * 72]
    return "\n".join(lines)


def emit(payload: Dict[str, Any], fmt: str, output: Optional[str]) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False) if fmt == "json" else format_text(payload)
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(text + ("" if text.endswith("\n") else "\n"))
    else:
        print(text)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze research-question coverage against an evidence store.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python coverage_analyzer.py --plan plan.json --store ../assets/sample_evidence_store.json
  python coverage_analyzer.py --questions Q1,Q2 --store store.jsonl --format json
""",
    )
    parser.add_argument("--plan", help="research_planner.py JSON output")
    parser.add_argument("--store", required=True, help="Evidence store JSON/JSONL")
    parser.add_argument("--questions", help="Comma-separated question ids if no plan file")
    parser.add_argument("--min-sources", type=int, default=2, help="Minimum sources per question")
    parser.add_argument("--as-of-year", type=int, default=datetime.now().year)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", "-o")
    args = parser.parse_args(argv)
    try:
        questions: List[Dict[str, Any]] = []
        if args.plan:
            questions = questions_from_plan(load_any(args.plan))
        if args.questions:
            for qid in args.questions.split(","):
                qid = qid.strip()
                if qid and qid not in {q["id"] for q in questions}:
                    questions.append({"id": qid, "text": qid, "priority": "supporting"})
        records = records_from(load_any(args.store))
        if not questions:
            found = sorted({qid for rec in records for qid in question_ids_of(rec)})
            questions = [{"id": q, "text": q, "priority": "supporting"} for q in found]
            if not questions:
                raise ValueError("No questions found — pass --plan or --questions")
        payload = analyze(questions, records, args.as_of_year, args.min_sources)
        emit(payload, args.format, args.output)
        return 0
    except FileNotFoundError as exc:
        print(f"error: file not found: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
