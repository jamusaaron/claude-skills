#!/usr/bin/env python3
"""Analyze recency/freshness and coverage gaps in a research package.

Usage:
    python coverage_gap_analyzer.py notes.json --as-of 2026-08-27
    python coverage_gap_analyzer.py notes.json --freshness-days 540 --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional


DEFAULT_REQUIRED_TYPES = [
    "primary",
    "government",
    "academic",
    "statistics",
]


def parse_as_of(value: Optional[str]) -> date:
    if not value:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    text = str(value)[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def load_notes(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Expected a research notes object.")
    return data


def analyze(notes: Dict[str, Any], as_of: date, freshness_days: int) -> Dict[str, Any]:
    questions = notes.get("research_questions") or notes.get("questions") or []
    sources = notes.get("sources") or []
    claims = notes.get("claims") or []
    required_types = notes.get("required_source_types") or DEFAULT_REQUIRED_TYPES
    required_geos = notes.get("required_geographies") or []

    q_ids: List[str] = []
    q_text: Dict[str, str] = {}
    for q in questions:
        if isinstance(q, str):
            qid = f"q{len(q_ids) + 1}"
            q_text[qid] = q
        else:
            qid = str(q.get("id") or f"q{len(q_ids) + 1}")
            q_text[qid] = q.get("question") or q.get("text") or qid
        q_ids.append(qid)

    covered: Dict[str, List[str]] = {qid: [] for qid in q_ids}
    for claim in claims:
        qid = str(claim.get("question_id") or "")
        if qid in covered:
            for sid in claim.get("source_ids") or claim.get("supports") or []:
                covered[qid].append(str(sid))

    cutoff = as_of - timedelta(days=freshness_days)
    stale = []
    undated = []
    type_present = set()
    geos_present = set()
    vintage_buckets = {"0-12m": 0, "1-3y": 0, "3-8y": 0, "8y+": 0, "undated": 0}

    for src in sources:
        stype = str(src.get("type") or src.get("source_type") or src.get("host_class") or "").lower()
        if stype:
            type_present.add(stype)
        if src.get("primary"):
            type_present.add("primary")
        geo = str(src.get("geography") or src.get("geo") or "").lower()
        if geo:
            geos_present.add(geo)
        pub = parse_date(src.get("date") or src.get("published"))
        sid = src.get("id") or src.get("url") or src.get("title")
        if not pub:
            undated.append(sid)
            vintage_buckets["undated"] += 1
            continue
        age = (as_of - pub).days
        if age > freshness_days and not src.get("foundational"):
            stale.append({
                "id": sid,
                "date": pub.isoformat(),
                "age_days": age,
                "title": src.get("title"),
            })
        if age <= 365:
            vintage_buckets["0-12m"] += 1
        elif age <= 365 * 3:
            vintage_buckets["1-3y"] += 1
        elif age <= 365 * 8:
            vintage_buckets["3-8y"] += 1
        else:
            vintage_buckets["8y+"] += 1

    question_gaps = []
    for qid in q_ids:
        ids = sorted(set(covered.get(qid) or []))
        status = "covered" if len(ids) >= 2 else ("thin" if len(ids) == 1 else "gap")
        if status != "covered":
            question_gaps.append({
                "id": qid,
                "question": q_text[qid],
                "source_ids": ids,
                "status": status,
            })

    missing_types = [t for t in required_types if t.lower() not in type_present]
    missing_geos = [g for g in required_geos if str(g).lower() not in geos_present]

    recommendations = []
    for gap in question_gaps:
        recommendations.append(
            f"Acquire {'a second independent source' if gap['status'] == 'thin' else 'any high-integrity source'} for {gap['id']}."
        )
    for t in missing_types:
        recommendations.append(f"Add a {t} source type; none present in the ledger.")
    if stale:
        recommendations.append(
            f"Rebase {len(stale)} stale source(s) older than {freshness_days} days unless marked foundational."
        )
    if undated:
        recommendations.append(f"Date-stamp {len(undated)} undated source(s) before using them as current.")
    if vintage_buckets["0-12m"] == 0 and sources:
        recommendations.append("No source from the last 12 months; run a recency-focused search round.")

    return {
        "as_of": as_of.isoformat(),
        "freshness_days": freshness_days,
        "cutoff": cutoff.isoformat(),
        "source_count": len(sources),
        "question_count": len(q_ids),
        "vintage_buckets": vintage_buckets,
        "stale_sources": stale,
        "undated_sources": undated,
        "question_gaps": question_gaps,
        "types_present": sorted(type_present),
        "missing_source_types": missing_types,
        "missing_geographies": missing_geos,
        "gap_score": round(
            (
                len(question_gaps) * 2
                + len(missing_types)
                + len(stale) * 0.5
                + (1 if vintage_buckets["0-12m"] == 0 and sources else 0)
            ),
            2,
        ),
        "recommendations": recommendations,
    }


def format_text(report: Dict[str, Any]) -> str:
    lines = [
        "COVERAGE & FRESHNESS GAP ANALYSIS",
        "=" * 72,
        f"As of {report['as_of']}   freshness window {report['freshness_days']}d   "
        f"gap_score={report['gap_score']}",
        f"Sources: {report['source_count']}   Questions: {report['question_count']}",
        "",
        "Vintage mix: " + ", ".join(f"{k}={v}" for k, v in report["vintage_buckets"].items()),
        "Types present: " + (", ".join(report["types_present"]) or "(none)"),
        "",
    ]
    if report["question_gaps"]:
        lines.append("Question gaps")
        for gap in report["question_gaps"]:
            lines.append(f"  [{gap['status']}] {gap['id']}: {gap['question']}")
        lines.append("")
    if report["stale_sources"]:
        lines.append("Stale sources")
        for src in report["stale_sources"]:
            lines.append(f"  {src['id']}  {src['date']}  age={src['age_days']}d  {src.get('title') or ''}")
        lines.append("")
    if report["missing_source_types"]:
        lines.append("Missing source types: " + ", ".join(report["missing_source_types"]))
    if report["missing_geographies"]:
        lines.append("Missing geographies: " + ", ".join(report["missing_geographies"]))
    if report["undated_sources"]:
        lines.append("Undated: " + ", ".join(map(str, report["undated_sources"])))
    lines.append("")
    lines.append("Recommendations")
    if report["recommendations"]:
        for rec in report["recommendations"]:
            lines.append(f"  - {rec}")
    else:
        lines.append("  - No material coverage or freshness gaps detected.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find uncovered questions, stale sources, and missing source types."
    )
    parser.add_argument("notes_file", help="JSON research notes")
    parser.add_argument("--as-of", dest="as_of", help="As-of date YYYY-MM-DD")
    parser.add_argument(
        "--freshness-days",
        type=int,
        default=730,
        help="Sources older than this (and not foundational) are stale (default: 730)",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        notes = load_notes(args.notes_file)
        report = analyze(notes, parse_as_of(args.as_of), args.freshness_days)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
