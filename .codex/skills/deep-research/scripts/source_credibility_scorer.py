#!/usr/bin/env python3
"""Source Credibility Scorer — 12-point source evaluation framework.

Scores sources on provenance, recency, methodology, corroboration, conflicts,
framing, evidential weight, counter-evidence handling, reproducibility,
peer review, perspective diversity, and overall integrity.

Usage:
    python3 source_credibility_scorer.py sources.json --format text
    python3 source_credibility_scorer.py sources.json --format json --output scores.json
    python3 source_credibility_scorer.py --demo --format text
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any


CRITERIA = [
    ("provenance_authority", "Provenance & Authority", 0.10),
    ("recency_relevance", "Recency & Relevance", 0.08),
    ("methodological_transparency", "Methodological Transparency", 0.10),
    ("corroboration", "Corroboration", 0.10),
    ("funding_conflicts", "Funding & Conflicts", 0.08),
    ("framing_language", "Framing & Language", 0.07),
    ("evidential_weight", "Evidential Weight", 0.10),
    ("counter_evidence_handling", "Counter-Evidence Handling", 0.08),
    ("reproducibility", "Accessibility & Reproducibility", 0.08),
    ("peer_review", "Peer Review & Editorial Standards", 0.09),
    ("perspective_diversity", "Perspective Diversity", 0.06),
    ("overall_integrity", "Overall Integrity", 0.06),
]

SOURCE_TYPE_DEFAULTS: dict[str, dict[str, int]] = {
    "peer_reviewed_journal": {
        "provenance_authority": 5, "recency_relevance": 4, "methodological_transparency": 4,
        "corroboration": 3, "funding_conflicts": 4, "framing_language": 4,
        "evidential_weight": 4, "counter_evidence_handling": 3, "reproducibility": 4,
        "peer_review": 5, "perspective_diversity": 3, "overall_integrity": 4,
    },
    "government_official": {
        "provenance_authority": 5, "recency_relevance": 4, "methodological_transparency": 4,
        "corroboration": 4, "funding_conflicts": 5, "framing_language": 3,
        "evidential_weight": 4, "counter_evidence_handling": 3, "reproducibility": 5,
        "peer_review": 4, "perspective_diversity": 3, "overall_integrity": 4,
    },
    "primary_document": {
        "provenance_authority": 4, "recency_relevance": 3, "methodological_transparency": 3,
        "corroboration": 3, "funding_conflicts": 5, "framing_language": 4,
        "evidential_weight": 3, "counter_evidence_handling": 3, "reproducibility": 5,
        "peer_review": 3, "perspective_diversity": 3, "overall_integrity": 4,
    },
    "think_tank_report": {
        "provenance_authority": 3, "recency_relevance": 4, "methodological_transparency": 3,
        "corroboration": 3, "funding_conflicts": 2, "framing_language": 3,
        "evidential_weight": 3, "counter_evidence_handling": 2, "reproducibility": 3,
        "peer_review": 2, "perspective_diversity": 3, "overall_integrity": 3,
    },
    "quality_journalism": {
        "provenance_authority": 3, "recency_relevance": 4, "methodological_transparency": 3,
        "corroboration": 3, "funding_conflicts": 3, "framing_language": 3,
        "evidential_weight": 3, "counter_evidence_handling": 3, "reproducibility": 3,
        "peer_review": 3, "perspective_diversity": 3, "overall_integrity": 3,
    },
    "preprint": {
        "provenance_authority": 3, "recency_relevance": 5, "methodological_transparency": 3,
        "corroboration": 1, "funding_conflicts": 3, "framing_language": 3,
        "evidential_weight": 2, "counter_evidence_handling": 2, "reproducibility": 3,
        "peer_review": 1, "perspective_diversity": 3, "overall_integrity": 2,
    },
    "blog_opinion": {
        "provenance_authority": 2, "recency_relevance": 3, "methodological_transparency": 1,
        "corroboration": 1, "funding_conflicts": 2, "framing_language": 2,
        "evidential_weight": 1, "counter_evidence_handling": 1, "reproducibility": 1,
        "peer_review": 1, "perspective_diversity": 2, "overall_integrity": 1,
    },
    "social_media": {
        "provenance_authority": 1, "recency_relevance": 4, "methodological_transparency": 1,
        "corroboration": 1, "funding_conflicts": 1, "framing_language": 2,
        "evidential_weight": 1, "counter_evidence_handling": 1, "reproducibility": 1,
        "peer_review": 1, "perspective_diversity": 2, "overall_integrity": 1,
    },
}


def classify_rating(score: float) -> str:
    if score >= 4.2:
        return "High"
    if score >= 3.5:
        return "Medium-High"
    if score >= 2.8:
        return "Medium"
    if score >= 2.0:
        return "Medium-Low"
    return "Low"


def score_source(source: dict[str, Any]) -> dict[str, Any]:
    source_type = source.get("type", "quality_journalism")
    defaults = SOURCE_TYPE_DEFAULTS.get(source_type, SOURCE_TYPE_DEFAULTS["quality_journalism"])

    criterion_scores: dict[str, Any] = {}
    weighted_sum = 0.0
    weight_total = 0.0

    overrides = source.get("scores", {})
    notes = source.get("notes", {})

    for key, label, weight in CRITERIA:
        raw = overrides.get(key, defaults.get(key, 3))
        raw = max(1, min(5, int(raw)))
        weighted_sum += raw * weight
        weight_total += weight
        criterion_scores[key] = {
            "label": label,
            "score": raw,
            "weight": weight,
            "note": notes.get(key, ""),
        }

    composite = round(weighted_sum / weight_total, 2) if weight_total else 0
    rating = classify_rating(composite)

    flags = []
    if criterion_scores["funding_conflicts"]["score"] <= 2:
        flags.append("potential_conflict_of_interest")
    if criterion_scores["peer_review"]["score"] <= 2:
        flags.append("limited_editorial_oversight")
    if criterion_scores["corroboration"]["score"] <= 2:
        flags.append("limited_independent_corroboration")
    if criterion_scores["methodological_transparency"]["score"] <= 2:
        flags.append("opaque_methodology")
    if source_type in ("social_media", "blog_opinion"):
        flags.append("not_standalone_evidence")

    usage_guidance = {
        "High": "Suitable as primary evidence for pivotal claims",
        "Medium-High": "Suitable for supporting claims; verify pivotal findings independently",
        "Medium": "Use with contextual caveats; corroborate key claims",
        "Medium-Low": "Illustrative only; must corroborate all factual claims elsewhere",
        "Low": "Narrative/testimony value only; never sole evidence for factual claims",
    }

    return {
        "id": source.get("id", "unknown"),
        "title": source.get("title", "Untitled"),
        "url": source.get("url", ""),
        "type": source_type,
        "date": source.get("date", ""),
        "composite_score": composite,
        "rating": rating,
        "usage_guidance": usage_guidance[rating],
        "flags": flags,
        "criteria": criterion_scores,
        "justification": source.get("justification") or _auto_justification(rating, flags),
    }


def _auto_justification(rating: str, flags: list[str]) -> str:
    base = f"Rated {rating} based on 12-point framework composite score."
    if flags:
        return f"{base} Flags: {', '.join(flags)}."
    return base


def score_all(sources: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [score_source(s) for s in sources]
    ratings = [s["rating"] for s in scored]
    distribution = {r: ratings.count(r) for r in ["High", "Medium-High", "Medium", "Medium-Low", "Low"]}

    high_integrity = [s for s in scored if s["rating"] in ("High", "Medium-High")]
    low_integrity = [s for s in scored if s["rating"] in ("Medium-Low", "Low")]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_sources": len(scored),
        "rating_distribution": distribution,
        "high_integrity_count": len(high_integrity),
        "low_integrity_count": len(low_integrity),
        "pivotal_claim_ready": len(high_integrity) >= 2,
        "recommendation": _portfolio_recommendation(scored),
        "sources": scored,
    }


def _portfolio_recommendation(scored: list[dict[str, Any]]) -> str:
    high = sum(1 for s in scored if s["rating"] in ("High", "Medium-High"))
    low = sum(1 for s in scored if s["rating"] in ("Medium-Low", "Low"))
    total = len(scored) or 1
    if high / total >= 0.5:
        return "Strong source portfolio — proceed to synthesis with verification on pivotal claims"
    if high / total >= 0.3:
        return "Adequate portfolio — expand high-integrity sources before finalizing pivotal claims"
    return f"Weak portfolio ({low} low-integrity sources) — conduct additional targeted acquisition"


def format_text(result: dict[str, Any]) -> str:
    lines = [
        "=" * 72,
        "SOURCE CREDIBILITY SCORING REPORT",
        f"Generated: {result['generated_at']}",
        f"Total sources: {result['total_sources']}",
        "=" * 72,
        "",
        f"High-integrity sources: {result['high_integrity_count']}",
        f"Low-integrity sources: {result['low_integrity_count']}",
        f"Pivotal-claim ready (≥2 high-integrity): {'YES' if result['pivotal_claim_ready'] else 'NO'}",
        f"Recommendation: {result['recommendation']}",
        "",
        "## Rating Distribution",
    ]
    for rating, count in result["rating_distribution"].items():
        lines.append(f"  {rating}: {count}")

    lines.append("\n## Source Scores\n")
    for s in result["sources"]:
        lines.append(f"[{s['id']}] {s['title']}")
        lines.append(f"  Type: {s['type']} | Date: {s['date']} | Rating: {s['rating']} ({s['composite_score']}/5.0)")
        lines.append(f"  Guidance: {s['usage_guidance']}")
        if s["flags"]:
            lines.append(f"  Flags: {', '.join(s['flags'])}")
        lines.append(f"  Justification: {s['justification']}")
        if s["url"]:
            lines.append(f"  URL: {s['url']}")
        lines.append("")

    lines.append("=" * 72)
    return "\n".join(lines)


DEMO_SOURCES = [
    {
        "id": "s1",
        "title": "WHO Global Health Statistics Report 2025",
        "type": "government_official",
        "date": "2025-03",
        "url": "https://example.gov/health-stats-2025",
    },
    {
        "id": "s2",
        "title": "Meta-analysis of intervention outcomes",
        "type": "peer_reviewed_journal",
        "date": "2024-11",
        "url": "https://example.edu/journal/article/12345",
    },
    {
        "id": "s3",
        "title": "Industry blog post on market trends",
        "type": "blog_opinion",
        "date": "2025-01",
        "url": "https://example.com/blog/trends",
        "scores": {"funding_conflicts": 1, "evidential_weight": 2},
        "justification": "Vendor-funded blog with limited methodology; illustrative only.",
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Score source credibility using 12-point framework")
    parser.add_argument("input", nargs="?", help="JSON file with sources array")
    parser.add_argument("--demo", action="store_true", help="Run with demo data")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--output", "-o", help="Output file path")

    args = parser.parse_args()

    if args.demo:
        sources = DEMO_SOURCES
    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
        sources = data.get("sources", data if isinstance(data, list) else [])
    else:
        parser.error("Provide input file or --demo")

    result = score_all(sources)
    output = json.dumps(result, indent=2) if args.format == "json" else format_text(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
