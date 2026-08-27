#!/usr/bin/env python3
"""Conservative confidence-band calculator for research claims.

Maps source count, agreement, quality, recency, independence, and
controversy into a capped confidence band plus a "what would change
this" checklist. Offline. Matches references/uncertainty-and-calibration.md.

Usage:
    python confidence_calibrator.py --claim "X reduces Y" --n-sources 4 --agreement 0.75 --source-quality 0.7 --recency 0.8
    python confidence_calibrator.py --n-sources 1 --agreement 1 --source-quality 0.9 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional, Tuple

BANDS = [
    (90, "Very High", ">90%"),
    (70, "High", "70-90%"),
    (50, "Medium", "50-70%"),
    (30, "Low", "30-50%"),
    (0, "Very Low", "<30%"),
]


def clamp01(value: float, name: str) -> float:
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be between 0 and 1 inclusive")
    return value


def band_for(score: float) -> Tuple[str, str]:
    for threshold, name, rng in BANDS:
        if score >= threshold:
            return name, rng
    return "Very Low", "<30%"


def calibrate(
    n_sources: int,
    agreement: float,
    source_quality: float,
    recency: float,
    independent_clusters: int,
    has_primary: bool,
    methods_transparent: bool,
    contested: bool,
    claim_type: str,
) -> Dict[str, Any]:
    if n_sources < 0:
        raise ValueError("n-sources must be >= 0")
    if independent_clusters < 0:
        raise ValueError("independent-clusters must be >= 0")

    drivers: List[Dict[str, Any]] = []
    score = 18.0
    drivers.append({"factor": "base_prior", "delta": 18, "note": "Start conservative; absence of evidence is not evidence."})

    src_points = min(n_sources, 6) * 7.0
    score += src_points
    drivers.append({"factor": "n_sources", "delta": src_points, "note": f"{n_sources} sources (capped at 6)."})

    agr_points = agreement * 16.0
    score += agr_points
    drivers.append({"factor": "agreement", "delta": round(agr_points, 1), "note": f"Agreement ratio {agreement:.2f}."})

    qual_points = source_quality * 18.0
    score += qual_points
    drivers.append({"factor": "source_quality", "delta": round(qual_points, 1), "note": "Mean integrity of cited sources."})

    rec_points = recency * 8.0
    score += rec_points
    drivers.append({"factor": "recency", "delta": round(rec_points, 1), "note": "Temporal fit to the scoped window."})

    cluster_points = min(independent_clusters, 3) * 4.0
    score += cluster_points
    drivers.append({"factor": "independence", "delta": cluster_points, "note": f"{independent_clusters} independent provenance clusters."})

    if has_primary:
        score += 6
        drivers.append({"factor": "primary_source", "delta": 6, "note": "At least one primary source in the support set."})
    if methods_transparent:
        score += 4
        drivers.append({"factor": "methods", "delta": 4, "note": "Methods or data generating process are inspectable."})

    penalties = []
    if n_sources < 2:
        penalties.append(("single_source", 18, "Fewer than 2 sources. Easy to be wrong."))
    if independent_clusters <= 1 and n_sources >= 2:
        penalties.append(("citation_ring", 12, "Multiple sources but one provenance cluster (syndication/citation laundering risk)."))
    if agreement < 0.5 and n_sources >= 2:
        penalties.append(("disagreement", 14, "Material disagreement among sources."))
    if contested:
        penalties.append(("contested_topic", 8, "Topic is polarized or adversarially framed."))
    if claim_type in ("forecast", "value"):
        penalties.append(("claim_type", 10, f"{claim_type} claims cannot reach High without explicit scenario bounds."))
    if claim_type == "interpretation":
        penalties.append(("interpretation", 6, "Interpretive claims inherit extra uncertainty."))
    if not has_primary and claim_type == "fact":
        penalties.append(("no_primary", 5, "Factual claim without a primary source."))
    if source_quality < 0.4:
        penalties.append(("low_quality", 10, "Mean source quality below Medium-Low."))

    for name, delta, note in penalties:
        score -= delta
        drivers.append({"factor": name, "delta": -delta, "note": note})

    # Hard caps: never Very High without primary + 2 clusters + high agreement
    hard_cap = 92.0
    cap_reasons = []
    if not has_primary:
        hard_cap = min(hard_cap, 78.0)
        cap_reasons.append("No primary source: cap at High (78).")
    if independent_clusters < 2:
        hard_cap = min(hard_cap, 72.0)
        cap_reasons.append("Fewer than 2 independent clusters: cap at High (72).")
    if agreement < 0.8:
        hard_cap = min(hard_cap, 80.0)
        cap_reasons.append("Agreement < 0.8: cap at 80.")
    if claim_type in ("forecast", "value"):
        hard_cap = min(hard_cap, 65.0)
        cap_reasons.append("Forecast/value claims cap at Medium (65) unless separately modelled.")
    if n_sources == 0:
        hard_cap = min(hard_cap, 25.0)
        cap_reasons.append("Zero sources: cap at Very Low.")

    raw = score
    final = max(5.0, min(hard_cap, score))
    band, rng = band_for(final)

    change_list = what_would_change(
        n_sources, agreement, source_quality, recency, independent_clusters,
        has_primary, methods_transparent, contested, claim_type, band,
    )
    return {
        "raw_score": round(raw, 1),
        "confidence_score": round(final, 1),
        "band": band,
        "band_range": rng,
        "hard_cap": hard_cap,
        "cap_reasons": cap_reasons,
        "drivers": drivers,
        "what_would_change_this": change_list,
        "claim_type": claim_type,
        "conservative": True,
        "rule": "Overconfidence is a cardinal error. Prefer under-confidence when independent clusters are thin.",
    }


def what_would_change(
    n_sources: int,
    agreement: float,
    source_quality: float,
    recency: float,
    independent_clusters: int,
    has_primary: bool,
    methods_transparent: bool,
    contested: bool,
    claim_type: str,
    band: str,
) -> List[str]:
    items = [
        "One independent high-integrity source that directly contradicts the claim.",
        "Evidence that cited sources share an undisclosed common origin.",
    ]
    if n_sources < 3:
        items.append("Two additional independent sources in the same direction would raise the band by one step.")
    if not has_primary:
        items.append("A primary document (statute, dataset, paper, filing, judgment) matching the claim.")
    if not methods_transparent:
        items.append("A methods/limitations section that makes the result reproducible.")
    if recency < 0.5:
        items.append("A source dated inside the scoped window confirming the claim still holds.")
    if independent_clusters < 2:
        items.append("A second provenance cluster (different institution, dataset, or jurisdiction).")
    if agreement < 0.7:
        items.append("Resolution of the current conflict via primary data, not another commentary.")
    if contested:
        items.append("A steelman of the opposing camp that fails on evidence, not on rhetoric.")
    if claim_type == "forecast":
        items.append("A scored forecasting base rate or backtest; without it, keep as scenario not fact.")
    if band in ("High", "Very High"):
        items.append("Any retraction, erratum, or methodological critique of an anchor source.")
    return items


def render_human(result: Dict[str, Any], claim: str) -> str:
    lines = [
        f"Claim:      {claim or '(unspecified)'}",
        f"Type:       {result['claim_type']}",
        f"Confidence: {result['confidence_score']}/100  {result['band']} ({result['band_range']})",
        f"Raw score:  {result['raw_score']}  Hard cap: {result['hard_cap']}",
        "",
        "Drivers:",
    ]
    for d in result["drivers"]:
        sign = "+" if d["delta"] >= 0 else ""
        lines.append(f"  {sign}{d['delta']:>6}  {d['factor']}: {d['note']}")
    if result["cap_reasons"]:
        lines.append("Caps applied:")
        for c in result["cap_reasons"]:
            lines.append(f"  - {c}")
    lines.append("")
    lines.append("What would change this:")
    for item in result["what_would_change_this"]:
        lines.append(f"  - {item}")
    lines.append("")
    lines.append(result["rule"])
    return "\n".join(lines)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute a conservative confidence band for a researched claim."
    )
    parser.add_argument("--claim", default="", help="Claim text (for output only)")
    parser.add_argument("--n-sources", type=int, required=True)
    parser.add_argument("--agreement", type=float, required=True, help="0-1 fraction of sources agreeing")
    parser.add_argument("--source-quality", type=float, required=True, help="0-1 mean integrity (High≈0.9, Low≈0.3)")
    parser.add_argument("--recency", type=float, default=0.7, help="0-1 temporal fit")
    parser.add_argument("--independent-clusters", type=int, default=1)
    parser.add_argument("--has-primary", action="store_true")
    parser.add_argument("--methods-transparent", action="store_true")
    parser.add_argument("--contested", action="store_true")
    parser.add_argument(
        "--claim-type",
        choices=["fact", "interpretation", "mechanism", "forecast", "value"],
        default="fact",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        agreement = clamp01(args.agreement, "agreement")
        quality = clamp01(args.source_quality, "source-quality")
        recency = clamp01(args.recency, "recency")
        result = calibrate(
            n_sources=args.n_sources,
            agreement=agreement,
            source_quality=quality,
            recency=recency,
            independent_clusters=args.independent_clusters,
            has_primary=args.has_primary,
            methods_transparent=args.methods_transparent,
            contested=args.contested,
            claim_type=args.claim_type,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    result["claim"] = args.claim
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_human(result, args.claim))
    return 0


if __name__ == "__main__":
    sys.exit(main())
