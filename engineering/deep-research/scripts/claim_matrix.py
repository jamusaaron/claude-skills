#!/usr/bin/env python3
"""Claim–evidence matrix builder.

Maps claims to supporting and contradicting sources, flags shared provenance,
identifies pivotal claims that lack independent high-integrity backing, and
emits a weighted matrix for synthesis.

Usage:
    python claim_matrix.py --input store.jsonl
    python claim_matrix.py --input claims.json --sources sources.json --format json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


WEIGHT = {"high": 3, "medium-high": 3, "medium": 2, "medium-low": 1, "low": 1, "unknown": 1}
FAMILY_ALIASES = {
    "twitter.com": "x.com",
    "x.com": "x.com",
    "reuters.com": "reuters",
    "wired.com": "conde_nast",
    "arxiv.org": "arxiv",
    "pubmed.ncbi.nlm.nih.gov": "nih",
    "nih.gov": "nih",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_any(path: str) -> Any:
    text = open(path, "r", encoding="utf-8").read().strip()
    if path.endswith(".jsonl"):
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def as_list(data: Any, keys: Tuple[str, ...]) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in keys:
            if isinstance(data.get(key), list):
                return [x for x in data[key] if isinstance(x, dict)]
        if any(k in data for k in ("text", "claim", "title", "url")):
            return [data]
    return []


def host_family(url: str) -> str:
    if not url:
        return "unknown"
    raw = url if "://" in url else "https://" + url
    try:
        host = urlparse(raw).netloc.lower()
    except ValueError:
        return "unknown"
    if host.startswith("www."):
        host = host[4:]
    if host in FAMILY_ALIASES:
        return FAMILY_ALIASES[host]
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host or "unknown"


def claim_id(text: str, explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit
    digest = hashlib.sha1(re.sub(r"\s+", " ", text.lower()).strip().encode("utf-8")).hexdigest()[:10]
    return f"C-{digest}"


def normalize_claim_text(text: str) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    return t.rstrip(".")


def extract_from_evidence(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    sources = []
    claims = []
    for rec in records:
        sid = rec.get("id") or rec.get("url") or rec.get("title") or claim_id(json.dumps(rec, sort_keys=True)[:80])
        band = (
            (rec.get("credibility") or {}).get("band")
            or rec.get("band")
            or rec.get("credibility_band")
            or "unknown"
        )
        src = {
            "id": sid,
            "title": rec.get("title"),
            "url": rec.get("url"),
            "band": str(band).lower(),
            "family": host_family(rec.get("url") or ""),
            "source_type": rec.get("source_type") or rec.get("type"),
            "question_id": rec.get("question_id"),
        }
        sources.append(src)
        rec_claims = rec.get("claims") or []
        if isinstance(rec_claims, str):
            rec_claims = [{"text": rec_claims}]
        for c in rec_claims:
            if isinstance(c, str):
                c = {"text": c}
            text = c.get("text") or c.get("claim") or ""
            if not text:
                continue
            claims.append({
                "id": c.get("id") or claim_id(text),
                "text": normalize_claim_text(text),
                "polarity": (c.get("polarity") or "supports").lower(),
                "question_id": c.get("question_id") or rec.get("question_id"),
                "source_id": sid,
                "band": src["band"],
            })
        if not rec_claims and rec.get("title"):
            # Treat title as a weak claim so empty stores still produce a matrix skeleton.
            claims.append({
                "id": claim_id(rec.get("title")),
                "text": normalize_claim_text(rec["title"]),
                "polarity": "neutral",
                "question_id": rec.get("question_id"),
                "source_id": sid,
                "band": src["band"],
            })
    return sources, claims


def cluster_claims(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group near-duplicate claims by normalized token overlap."""
    clusters: List[Dict[str, Any]] = []

    def tokens(text: str) -> set:
        stop = {"the", "a", "an", "of", "to", "and", "in", "on", "for", "is", "that", "with"}
        return {t for t in re.findall(r"[a-z0-9%+-]+", text.lower()) if t not in stop and len(t) > 2}

    for claim in claims:
        toks = tokens(claim["text"])
        matched = None
        for cluster in clusters:
            overlap = len(toks & cluster["tokens"]) / max(1, len(toks | cluster["tokens"]))
            if overlap >= 0.55:
                matched = cluster
                break
        if matched is None:
            cluster = {
                "id": claim["id"],
                "text": claim["text"],
                "tokens": toks,
                "question_ids": set(filter(None, [claim.get("question_id")])),
                "members": [claim],
            }
            clusters.append(cluster)
        else:
            matched["members"].append(claim)
            if claim.get("question_id"):
                matched["question_ids"].add(claim["question_id"])
    out = []
    for cluster in clusters:
        supports = [m for m in cluster["members"] if m.get("polarity") in {"supports", "support", "affirm"}]
        refutes = [m for m in cluster["members"] if m.get("polarity") in {"refutes", "refute", "contradicts", "against"}]
        neutral = [m for m in cluster["members"] if m not in supports and m not in refutes]
        support_w = sum(WEIGHT.get(m.get("band", "unknown"), 1) for m in supports)
        refute_w = sum(WEIGHT.get(m.get("band", "unknown"), 1) for m in refutes)
        families = {m.get("source_id") for m in cluster["members"]}
        out.append({
            "id": cluster["id"],
            "text": cluster["text"],
            "question_ids": sorted(cluster["question_ids"]),
            "support_count": len(supports),
            "refute_count": len(refutes),
            "neutral_count": len(neutral),
            "support_weight": support_w,
            "refute_weight": refute_w,
            "net_weight": support_w - refute_w,
            "sources": sorted({m["source_id"] for m in cluster["members"] if m.get("source_id")}),
            "support_sources": sorted({m["source_id"] for m in supports if m.get("source_id")}),
            "refute_sources": sorted({m["source_id"] for m in refutes if m.get("source_id")}),
            "unique_source_ids": len(families),
        })
    return out


def independence_report(cluster: Dict[str, Any], sources_by_id: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    families = []
    bands = []
    for sid in cluster["sources"]:
        src = sources_by_id.get(sid) or {}
        families.append(src.get("family") or "unknown")
        bands.append(src.get("band") or "unknown")
    unique_families = sorted(set(families))
    highish = sum(1 for b in bands if b in {"high", "medium-high"})
    independent_high = 0
    seen = set()
    for sid in cluster["support_sources"]:
        src = sources_by_id.get(sid) or {}
        fam = src.get("family") or sid
        if src.get("band") in {"high", "medium-high"} and fam not in seen:
            independent_high += 1
            seen.add(fam)
    pivotal_ok = independent_high >= 2 or (
        independent_high >= 1
        and any((sources_by_id.get(s) or {}).get("source_type") in {"primary", "legislation", "judgment", "dataset"} for s in cluster["support_sources"])
    )
    return {
        "unique_publisher_families": unique_families,
        "family_count": len(unique_families),
        "shared_provenance_risk": len(families) > 1 and len(unique_families) == 1,
        "high_or_better_sources": highish,
        "independent_high_support": independent_high,
        "meets_pivotal_bar": pivotal_ok,
    }


def build_matrix(
    claims: List[Dict[str, Any]],
    sources: List[Dict[str, Any]],
    questions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    sources_by_id = {s["id"]: s for s in sources}
    clustered = cluster_claims(claims)
    rows = []
    for cluster in clustered:
        indep = independence_report(cluster, sources_by_id)
        status = "contested" if cluster["refute_count"] and cluster["support_count"] else (
            "supported" if cluster["net_weight"] > 0 else (
                "refuted" if cluster["net_weight"] < 0 else "insufficient"
            )
        )
        if not indep["meets_pivotal_bar"] and status == "supported":
            status = "weakly-supported"
        rows.append({**cluster, "independence": indep, "status": status})
    rows.sort(key=lambda r: (r["status"] != "contested", -abs(r["net_weight"])))
    by_q: Dict[str, int] = defaultdict(int)
    for row in rows:
        for qid in row["question_ids"] or ["unmapped"]:
            by_q[qid] += 1
    pivotal = [r for r in rows if r["status"] in {"contested", "weakly-supported", "insufficient"}]
    return {
        "skill": "deep-research",
        "artifact": "claim_matrix",
        "generated_at": utc_now(),
        "counts": {
            "claims_in": len(claims),
            "clusters": len(rows),
            "sources": len(sources),
            "contested": sum(1 for r in rows if r["status"] == "contested"),
            "weakly_supported": sum(1 for r in rows if r["status"] == "weakly-supported"),
            "supported": sum(1 for r in rows if r["status"] == "supported"),
        },
        "questions_coverage": dict(by_q),
        "questions_declared": questions or [],
        "pivotal_gaps": [
            {
                "id": r["id"],
                "text": r["text"],
                "status": r["status"],
                "independence": r["independence"],
            }
            for r in pivotal[:20]
        ],
        "matrix": rows,
    }


def format_text(payload: Dict[str, Any]) -> str:
    c = payload["counts"]
    lines = [
        "=" * 72,
        "CLAIM–EVIDENCE MATRIX",
        "=" * 72,
        f"Generated: {payload['generated_at']}",
        f"Clusters: {c['clusters']}  (supported={c['supported']} contested={c['contested']} weak={c['weakly_supported']})",
        "",
        f"{'STATUS':18} {'NET':>4} {'SUP':>3} {'REF':>3}  CLAIM",
        "-" * 72,
    ]
    for row in payload["matrix"]:
        text = row["text"] if len(row["text"]) < 70 else row["text"][:67] + "..."
        lines.append(
            f"{row['status']:18} {row['net_weight']:>4} {row['support_count']:>3} {row['refute_count']:>3}  {text}"
        )
        if row["independence"]["shared_provenance_risk"]:
            lines.append("                    ⚠ shared provenance — not independent corroboration")
    if payload["pivotal_gaps"]:
        lines += ["", "PIVOTAL GAPS (need verification loop)"]
        for g in payload["pivotal_gaps"][:10]:
            lines.append(f"  [{g['status']}] {g['text']}")
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
        description="Build a claim-to-evidence matrix with independence checks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python claim_matrix.py --input ../assets/sample_evidence_store.json
  python claim_matrix.py --input claims.json --sources sources.json --format json -o matrix.json
""",
    )
    parser.add_argument("--input", "-i", required=True, help="Evidence store, claims list, or mixed JSON/JSONL")
    parser.add_argument("--sources", help="Optional separate sources file")
    parser.add_argument("--questions", help="Comma-separated question ids expected in the matrix")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", "-o")
    args = parser.parse_args(argv)
    try:
        data = load_any(args.input)
        records = as_list(data, ("evidence", "records", "items", "sources", "claims"))
        sources, claims = extract_from_evidence(records)
        if args.sources:
            extra = as_list(load_any(args.sources), ("sources", "records", "items"))
            extra_s, extra_c = extract_from_evidence(extra)
            sources.extend(extra_s)
            claims.extend(extra_c)
        # If the file is claims-only (has text/claim but no url), keep them.
        if not claims:
            maybe_claims = as_list(data, ("claims",))
            for c in maybe_claims:
                text = c.get("text") or c.get("claim")
                if text:
                    claims.append({
                        "id": c.get("id") or claim_id(text),
                        "text": normalize_claim_text(text),
                        "polarity": (c.get("polarity") or "supports").lower(),
                        "question_id": c.get("question_id"),
                        "source_id": c.get("source_id") or "unspecified",
                        "band": c.get("band") or "unknown",
                    })
        questions = [q.strip() for q in (args.questions or "").split(",") if q.strip()]
        payload = build_matrix(claims, sources, questions)
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
