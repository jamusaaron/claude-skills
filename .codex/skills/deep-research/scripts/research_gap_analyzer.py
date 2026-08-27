#!/usr/bin/env python3
"""Research Gap Analyzer — Identify coverage gaps and weak links in research.

Analyzes sub-question coverage, source diversity, credibility distribution,
temporal gaps, and generates prioritized follow-up recommendations.

Usage:
    python3 research_gap_analyzer.py coverage.json --format text
    python3 research_gap_analyzer.py --demo --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any


COVERAGE_THRESHOLDS = {
    "light": {"min_sources_per_question": 1, "min_high_integrity": 0},
    "medium": {"min_sources_per_question": 2, "min_high_integrity": 1},
    "deep": {"min_sources_per_question": 3, "min_high_integrity": 2},
}


def analyze_gaps(data: dict[str, Any]) -> dict[str, Any]:
    depth = data.get("depth", "medium")
    thresholds = COVERAGE_THRESHOLDS.get(depth, COVERAGE_THRESHOLDS["medium"])
    sub_questions = data.get("sub_questions", [])
    sources = data.get("sources", [])
    coverage_map = data.get("coverage", {})

    gaps = []
    weak_links = []
    follow_ups = []

    rating_counts = Counter(s.get("rating", "Medium") for s in sources)
    source_types = Counter(s.get("type", "unknown") for s in sources)
    years = [int(s["date"][:4]) for s in sources if s.get("date") and s["date"][:4].isdigit()]

    for sq in sub_questions:
        sq_id = sq.get("id", "")
        sq_text = sq.get("question", sq.get("text", ""))
        mapped = coverage_map.get(sq_id, coverage_map.get(sq_text, {}))
        source_ids = mapped.get("sources", []) if isinstance(mapped, dict) else mapped
        if isinstance(source_ids, str):
            source_ids = [source_ids]

        sq_sources = [s for s in sources if s.get("id") in source_ids]
        high_count = sum(1 for s in sq_sources if s.get("rating") in ("High", "Medium-High"))

        if len(sq_sources) < thresholds["min_sources_per_question"]:
            gaps.append({
                "sub_question_id": sq_id,
                "question": sq_text,
                "gap_type": "insufficient_sources",
                "current_count": len(sq_sources),
                "required": thresholds["min_sources_per_question"],
                "priority": "high",
            })
            follow_ups.append({
                "action": "targeted_search",
                "sub_question_id": sq_id,
                "query_suggestion": f'Site-restricted and academic search for: {sq_text[:80]}',
                "priority": "high",
            })

        if high_count < thresholds["min_high_integrity"]:
            weak_links.append({
                "sub_question_id": sq_id,
                "question": sq_text,
                "high_integrity_count": high_count,
                "required": thresholds["min_high_integrity"],
                "priority": "medium" if len(sq_sources) >= thresholds["min_sources_per_question"] else "high",
            })

    diversity_gaps = _analyze_diversity(source_types, rating_counts)
    temporal_gaps = _analyze_temporal(years, data.get("temporal_scope", ""))

    uncovered = [sq for sq in sub_questions if sq.get("id") not in
                 {g["sub_question_id"] for g in gaps} and
                 sq.get("id") not in coverage_map and sq.get("question") not in coverage_map]

    if uncovered:
        for sq in uncovered:
            gaps.append({
                "sub_question_id": sq.get("id", ""),
                "question": sq.get("question", ""),
                "gap_type": "no_coverage",
                "current_count": 0,
                "required": thresholds["min_sources_per_question"],
                "priority": "critical",
            })

    total_gaps = len(gaps) + len(weak_links)
    coverage_pct = round(
        (len(sub_questions) - len(gaps)) / max(len(sub_questions), 1) * 100, 1
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "depth": depth,
        "summary": {
            "total_sub_questions": len(sub_questions),
            "total_sources": len(sources),
            "coverage_percentage": coverage_pct,
            "gaps_found": len(gaps),
            "weak_links": len(weak_links),
            "quality_gate_passes": total_gaps == 0,
        },
        "source_portfolio": {
            "rating_distribution": dict(rating_counts),
            "type_distribution": dict(source_types),
            "year_range": f"{min(years)}-{max(years)}" if years else "unknown",
        },
        "gaps": sorted(gaps, key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x["priority"], 3)),
        "weak_links": weak_links,
        "diversity_gaps": diversity_gaps,
        "temporal_gaps": temporal_gaps,
        "follow_up_recommendations": _prioritize_follow_ups(follow_ups, gaps, diversity_gaps, temporal_gaps),
    }


def _analyze_diversity(types: Counter, ratings: Counter) -> list[dict]:
    gaps = []
    if len(types) < 3:
        gaps.append({
            "gap_type": "low_source_type_diversity",
            "detail": f"Only {len(types)} source types represented; aim for ≥3 (government, academic, primary)",
            "priority": "medium",
        })
    low_count = ratings.get("Low", 0) + ratings.get("Medium-Low", 0)
    total = sum(ratings.values()) or 1
    if low_count / total > 0.4:
        gaps.append({
            "gap_type": "high_low_integrity_ratio",
            "detail": f"{round(low_count/total*100)}% of sources are Medium-Low or Low integrity",
            "priority": "high",
        })
    if ratings.get("High", 0) + ratings.get("Medium-High", 0) < 2:
        gaps.append({
            "gap_type": "insufficient_high_integrity_sources",
            "detail": "Fewer than 2 High/Medium-High sources in portfolio",
            "priority": "high",
        })
    return gaps


def _analyze_temporal(years: list[int], scope: str) -> list[dict]:
    gaps = []
    if not years:
        gaps.append({"gap_type": "missing_publication_dates", "detail": "Many sources lack dates", "priority": "medium"})
        return gaps
    current_year = datetime.now(timezone.utc).year
    if max(years) < current_year - 3:
        gaps.append({
            "gap_type": "stale_sources",
            "detail": f"Most recent source is from {max(years)}; may not reflect current landscape",
            "priority": "high",
        })
    if min(years) > current_year - 2 and "historical" in scope.lower():
        gaps.append({
            "gap_type": "missing_historical_context",
            "detail": "No sources older than 2 years despite historical scope requirement",
            "priority": "medium",
        })
    return gaps


def _prioritize_follow_ups(follow_ups, gaps, diversity_gaps, temporal_gaps) -> list[dict]:
    recs = list(follow_ups)
    for dg in diversity_gaps:
        if dg["gap_type"] == "insufficient_high_integrity_sources":
            recs.append({
                "action": "source_upgrade",
                "query_suggestion": "Search peer-reviewed journals and government sources for core claims",
                "priority": "high",
            })
        elif dg["gap_type"] == "low_source_type_diversity":
            recs.append({
                "action": "diversify_sources",
                "query_suggestion": "Add site:.gov, site:.edu, and primary document searches",
                "priority": "medium",
            })
    for tg in temporal_gaps:
        if tg["gap_type"] == "stale_sources":
            recs.append({
                "action": "recency_search",
                "query_suggestion": f"Search with after:{datetime.now(timezone.utc).year - 1}-01-01 filter",
                "priority": "high",
            })
    if not recs and not gaps:
        recs.append({"action": "proceed_to_synthesis", "query_suggestion": "Coverage adequate", "priority": "low"})
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(recs, key=lambda x: priority_order.get(x.get("priority", "low"), 3))


def format_text(result: dict[str, Any]) -> str:
    s = result["summary"]
    lines = [
        "=" * 72,
        "RESEARCH GAP ANALYSIS",
        f"Generated: {result['generated_at']} | Depth: {result['depth']}",
        "=" * 72,
        "",
        f"Coverage: {s['coverage_percentage']}% | Sources: {s['total_sources']}",
        f"Gaps: {s['gaps_found']} | Weak links: {s['weak_links']}",
        f"Quality gate: {'PASS' if s['quality_gate_passes'] else 'FAIL'}",
        "",
        "## Source Portfolio",
        f"  Ratings: {result['source_portfolio']['rating_distribution']}",
        f"  Types: {result['source_portfolio']['type_distribution']}",
        f"  Year range: {result['source_portfolio']['year_range']}",
    ]

    if result["gaps"]:
        lines.extend(["", "## Coverage Gaps"])
        for g in result["gaps"]:
            lines.append(f"  [{g['priority'].upper()}] {g['sub_question_id']}: {g['question'][:60]}...")
            lines.append(f"    Type: {g['gap_type']} | Current: {g['current_count']} | Required: {g['required']}")

    if result["weak_links"]:
        lines.extend(["", "## Weak Links (Low High-Integrity Coverage)"])
        for w in result["weak_links"]:
            lines.append(f"  [{w['priority'].upper()}] {w['sub_question_id']}: "
                         f"{w['high_integrity_count']}/{w['required']} high-integrity sources")

    if result["diversity_gaps"]:
        lines.extend(["", "## Portfolio Diversity Gaps"])
        for d in result["diversity_gaps"]:
            lines.append(f"  [{d['priority'].upper()}] {d['gap_type']}: {d['detail']}")

    lines.extend(["", "## Follow-Up Recommendations"])
    for r in result["follow_up_recommendations"]:
        lines.append(f"  [{r['priority'].upper()}] {r['action']}: {r['query_suggestion']}")

    lines.append("\n" + "=" * 72)
    return "\n".join(lines)


DEMO = {
    "depth": "medium",
    "temporal_scope": "Evidence as of 2025",
    "sub_questions": [
        {"id": "sq1", "question": "What is the current consensus on topic X?"},
        {"id": "sq2", "question": "What quantitative data supports the main claims?"},
        {"id": "sq3", "question": "What are the contested perspectives?"},
        {"id": "sq4", "question": "What regulatory frameworks apply?"},
    ],
    "sources": [
        {"id": "s1", "type": "peer_reviewed_journal", "rating": "High", "date": "2024-06"},
        {"id": "s2", "type": "blog_opinion", "rating": "Low", "date": "2025-01"},
        {"id": "s3", "type": "quality_journalism", "rating": "Medium", "date": "2023-11"},
    ],
    "coverage": {
        "sq1": {"sources": ["s1", "s3"]},
        "sq2": {"sources": ["s2"]},
        "sq3": {"sources": []},
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze research coverage gaps and recommend follow-ups")
    parser.add_argument("input", nargs="?", help="JSON coverage data file")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--output", "-o")

    args = parser.parse_args()

    if args.demo:
        data = DEMO
    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
    else:
        parser.error("Provide input file or --demo")

    result = analyze_gaps(data)
    output = json.dumps(result, indent=2) if args.format == "json" else format_text(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Analysis written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
