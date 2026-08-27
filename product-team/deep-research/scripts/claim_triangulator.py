#!/usr/bin/env python3
"""Score claim triangulation from structured claims and scored sources.

Groups supporting sources by institutional lineage so circular citation is
not counted as independent corroboration.

Usage:
    python claim_triangulator.py claims.json --sources sources.scored.json
    python claim_triangulator.py claims.json --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


BAND_WEIGHT = {
    "High": 3.0,
    "Medium-High": 2.4,
    "Medium": 1.6,
    "Medium-Low": 0.8,
    "Low": 0.3,
}

VERDICT_RULES = [
    (2.5, 2, "corroborated"),
    (1.5, 2, "provisionally_corroborated"),
    (1.5, 1, "single_lineage"),
    (0.0, 0, "unverified"),
]


def host_org(url: str, org: Optional[str] = None) -> str:
    if org:
        return str(org).strip().lower()
    host = urlparse(url or "").netloc.lower().lstrip("www.")
    parts = host.split(".")
    if len(parts) >= 2:
        return parts[-2] if parts[-1] not in {"uk", "au", "nz"} else parts[-3] if len(parts) >= 3 else parts[0]
    return host or "unknown"


def index_sources(sources: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    for src in sources:
        for key in (src.get("id"), src.get("url"), src.get("title")):
            if key:
                indexed[str(key)] = src
    return indexed


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def unwrap_list(data: Any, *keys: str) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in keys:
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError(f"Expected a list or object with one of {keys}")


def lineage_id(source: Dict[str, Any]) -> str:
    if source.get("lineage") or source.get("dataset") or source.get("organization"):
        return str(source.get("lineage") or source.get("dataset") or source.get("organization")).lower()
    return host_org(str(source.get("url") or ""), source.get("organization"))


def score_claim(claim: Dict[str, Any], source_index: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    support_ids = claim.get("supports") or claim.get("source_ids") or claim.get("sources") or []
    contradict_ids = claim.get("contradicts") or claim.get("contradicting_source_ids") or []
    if isinstance(support_ids, str):
        support_ids = [s.strip() for s in support_ids.split(",") if s.strip()]

    lineages: Dict[str, List[str]] = {}
    weighted = 0.0
    used: List[Dict[str, Any]] = []
    missing: List[str] = []

    for sid in support_ids:
        src = source_index.get(str(sid))
        if not src:
            missing.append(str(sid))
            continue
        band = src.get("integrity") or "Medium"
        weight = BAND_WEIGHT.get(str(band), 1.0)
        lid = lineage_id(src)
        lineages.setdefault(lid, []).append(str(sid))
        # Independent lineages get full weight; duplicates in same lineage get 0.35x
        if len(lineages[lid]) == 1:
            weighted += weight
        else:
            weighted += weight * 0.35
        used.append({
            "id": src.get("id") or sid,
            "integrity": band,
            "lineage": lid,
        })

    independent = len(lineages)
    high_or_mid = sum(
        1 for rows in lineages.values()
        if any(
            (source_index.get(sid) or {}).get("integrity") in {"High", "Medium-High", "Medium"}
            for sid in rows
        )
    )
    verdict = "unverified"
    if independent >= 2 and weighted >= 2.5 and high_or_mid >= 2:
        verdict = "corroborated"
    elif independent >= 2 and weighted >= 1.5:
        verdict = "provisionally_corroborated"
    elif independent == 1 and weighted >= 1.5:
        verdict = "single_lineage"
    elif contradict_ids:
        verdict = "contested"
    else:
        verdict = "unverified"

    if contradict_ids and independent >= 1:
        if verdict == "corroborated":
            verdict = "contested_but_weighted"
        elif verdict != "unverified":
            verdict = "contested"

    confidence = min(0.95, 0.2 + 0.15 * independent + 0.08 * weighted)
    if verdict.startswith("contested"):
        confidence *= 0.7
    if verdict == "unverified":
        confidence = min(confidence, 0.35)

    return {
        "id": claim.get("id") or claim.get("claim"),
        "claim": claim.get("claim") or claim.get("text") or claim.get("statement"),
        "question_id": claim.get("question_id"),
        "supporting_sources": used,
        "missing_source_ids": missing,
        "contradicting_source_ids": list(contradict_ids),
        "independent_lineages": independent,
        "lineages": {k: v for k, v in lineages.items()},
        "triangulation_score": round(weighted, 2),
        "verdict": verdict,
        "confidence": round(confidence, 2),
        "note": (
            "Independent lineages required; same-host or same-dataset sources are down-weighted."
        ),
    }


def format_text(results: List[Dict[str, Any]]) -> str:
    lines = [
        "CLAIM TRIANGULATION REPORT",
        "=" * 72,
        f"Claims: {len(results)}",
        "",
    ]
    for item in results:
        lines.append(
            f"[{item['verdict']}] score={item['triangulation_score']:.2f}  "
            f"lineages={item['independent_lineages']}  conf={item['confidence']:.2f}"
        )
        lines.append(f"  {item['id']}: {item['claim']}")
        if item["supporting_sources"]:
            srcs = ", ".join(
                f"{s['id']}({s['integrity']}/{s['lineage']})" for s in item["supporting_sources"]
            )
            lines.append(f"  sources: {srcs}")
        if item["contradicting_source_ids"]:
            lines.append(f"  contradicts: {', '.join(map(str, item['contradicting_source_ids']))}")
        if item["missing_source_ids"]:
            lines.append(f"  missing ids: {', '.join(item['missing_source_ids'])}")
        lines.append("")
    return "\n".join(lines).rstrip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Triangulate claims against independent source lineages."
    )
    parser.add_argument("claims_file", help="JSON claims list")
    parser.add_argument(
        "--sources",
        help="JSON sources (raw or source_credibility.py output). Optional if claims file embeds sources.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        claims_raw = load_json(args.claims_file)
        claims = unwrap_list(claims_raw, "claims", "items")
        sources: List[Dict[str, Any]] = []
        if args.sources:
            sources = unwrap_list(load_json(args.sources), "sources", "items")
        elif isinstance(claims_raw, dict) and "sources" in claims_raw:
            sources = unwrap_list(claims_raw, "sources")
        if not sources:
            raise ValueError("Provide --sources or embed a 'sources' array in the claims file.")
        index = index_sources(sources)
        results = [score_claim(claim, index) for claim in claims]
        results.sort(key=lambda r: r["triangulation_score"], reverse=True)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    payload = {"count": len(results), "claims": results}
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(format_text(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
