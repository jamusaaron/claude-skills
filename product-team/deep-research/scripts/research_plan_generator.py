#!/usr/bin/env python3
"""Generate a phased deep-research plan from a query and constraints.

Deterministic planning heuristics. Pairs with question_decomposer.py.

Usage:
    python research_plan_generator.py --query "..." --depth deep --as-of 2026-08-27
    python research_plan_generator.py --input plan_request.json --format json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from question_decomposer import decompose, keywords


DEPTH_CONFIG = {
    "light": {
        "tool_rounds": 2,
        "min_sources": 6,
        "verification_claims": 2,
        "search_variants": 4,
        "early_stop": "Stop after landscape coverage of core definitions + 2 independent sources on the lead claim.",
    },
    "medium": {
        "tool_rounds": 4,
        "min_sources": 12,
        "verification_claims": 4,
        "search_variants": 6,
        "early_stop": "Stop when each research question has ≥2 independent sources or an explicit gap note.",
    },
    "deep": {
        "tool_rounds": 6,
        "min_sources": 20,
        "verification_claims": 5,
        "search_variants": 8,
        "early_stop": "Stop after verification loop on pivotal claims and diminishing-return gap round.",
    },
}

SYNONYM_SWAPS = [
    ("impact", "effect"),
    ("remote work", "work from home"),
    ("WFH", "remote-first"),
    ("productivity", "output OR performance"),
    ("regulation", "rule OR statute"),
    ("AI", "artificial intelligence"),
    ("vs", "compared to"),
]


def parse_date(value: Optional[str]) -> date:
    if not value:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_request(args: argparse.Namespace) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if args.input:
        with open(args.input, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            raise ValueError("Input JSON must be an object.")
        data.update(loaded)
    if args.query:
        data["query"] = args.query
    if args.positional and "query" not in data:
        data["query"] = args.positional
    if args.depth:
        data["depth"] = args.depth
    if args.as_of:
        data["as_of"] = args.as_of
    if args.geography:
        data["geography"] = args.geography
    if args.exclude:
        data["exclude"] = args.exclude
    if args.include_source_types:
        data["source_types"] = args.include_source_types
    query = str(data.get("query") or "").strip()
    if not query:
        raise ValueError("Provide a query via argument or JSON 'query' field.")
    data["query"] = query
    data["depth"] = str(data.get("depth") or "medium").lower()
    if data["depth"] not in DEPTH_CONFIG:
        raise ValueError("depth must be light, medium, or deep")
    return data


def search_variants(query: str, source_types: List[str], as_of: date, geography: str) -> List[str]:
    kws = keywords(query)
    core = " ".join(kws[:8]) or query
    year = as_of.year
    variants = [
        query.strip().rstrip("?"),
        f"{core} evidence review {year - 1}..{year}",
        f"{core} systematic review OR meta-analysis",
        f"{core} limitations OR criticism OR replication",
    ]
    for old, new in SYNONYM_SWAPS:
        if old.lower() in query.lower():
            variants.append(re.sub(re.escape(old), new, query, flags=re.I).strip(" ?"))
    geo = geography.strip()
    if geo and geo.lower() not in {"global", "worldwide", "all"}:
        variants.append(f"{core} {geo}")
    type_to_operator = {
        "government": "site:.gov OR site:.gov.au OR site:.europa.eu",
        "academic": "site:.edu OR filetype:pdf",
        "statistics": "dataset OR statistics filetype:xlsx OR filetype:csv",
        "legal": "legislation OR judgment OR \"explanatory memorandum\"",
        "news": "after:{year}-01-01".format(year=year - 1),
        "corporate": "investor OR 10-K OR annual report filetype:pdf",
    }
    for stype in source_types:
        op = type_to_operator.get(stype.lower())
        if op:
            variants.append(f"{core} {op}")
    # Deduplicate while preserving order
    seen = set()
    out: List[str] = []
    for item in variants:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def premortem(qtype: str, depth: str) -> List[Dict[str, str]]:
    modes = [
        {
            "failure": "Source-selection bias toward convenient first-page results",
            "mitigation": "Force 4–8 query variants plus an explicit outlier/disconfirming search.",
        },
        {
            "failure": "Shared-provenance illusion of corroboration",
            "mitigation": "Cluster sources by institution/dataset; require independent lineages for pivotal claims.",
        },
        {
            "failure": "Recency or vintage error (citing superseded data as current)",
            "mitigation": "Stamp every statistic with as-of date; run coverage_gap_analyzer.py.",
        },
        {
            "failure": "Semantic drift away from the original decision question",
            "mitigation": "Re-read restated query before synthesis; keep a running decision-relevance check.",
        },
        {
            "failure": "Overconfidence in synthesis under sparse evidence",
            "mitigation": "Apply uncertainty ladder; never upgrade Low evidence to High via fluent prose.",
        },
    ]
    if qtype == "causal":
        modes.append({
            "failure": "Causal language from observational studies",
            "mitigation": "Tag design (RCT, DiD, IV, observational) on every effect-size claim.",
        })
    if qtype == "legal_policy":
        modes.append({
            "failure": "Treating commentary or guidance as black-letter law",
            "mitigation": "Separate statute/regulation/holding from secondary interpretation.",
        })
    if depth == "light":
        modes.append({
            "failure": "Light-tier stopping before a single disconfirming search",
            "mitigation": "Minimum one contrary-evidence query even in light mode.",
        })
    return modes


def tool_sequence(depth: str, qtype: str) -> List[Dict[str, str]]:
    seq = [
        {"phase": "1-plan", "action": "Decompose query; persist plan, questions, and stop rules."},
        {"phase": "2-scan", "action": "Run search variants in parallel; capture titles/snippets before deep reads."},
        {"phase": "3-acquire", "action": "Extract verbatim methods, numbers, limitations, and funding from anchor sources."},
        {"phase": "4-evaluate", "action": "Score sources with source_credibility.py; drop or caveat Low integrity."},
        {"phase": "5-triangulate", "action": "Build evidence matrix + contradiction report; verify pivotal claims."},
        {"phase": "6-package", "action": "Produce layered output via output_packager.py; run quality gates."},
    ]
    if depth == "light":
        seq = [s for s in seq if s["phase"] not in {"5-triangulate"}] + [
            {"phase": "5-light-check", "action": "Spot-check the top 2 claims against a second independent source."}
        ]
    if qtype == "quantitative":
        seq.append({"phase": "5b-numbers", "action": "Recompute or sanity-check extracted statistics from primary tables."})
    return seq


def generate_plan(request: Dict[str, Any]) -> Dict[str, Any]:
    query = request["query"]
    depth = request["depth"]
    as_of = parse_date(request.get("as_of"))
    geography = str(request.get("geography") or "global")
    source_types = request.get("source_types") or [
        "government", "academic", "statistics", "news",
    ]
    if isinstance(source_types, str):
        source_types = [s.strip() for s in source_types.split(",") if s.strip()]
    exclude = request.get("exclude") or [
        "unverified social posts as standalone evidence",
        "anonymous blogs without primary data",
        "predatory journals without caveats",
    ]
    if isinstance(exclude, str):
        exclude = [exclude]

    decomposed = decompose(query)
    cfg = DEPTH_CONFIG[depth]
    variants = search_variants(query, source_types, as_of, geography)[: cfg["search_variants"]]

    plan = {
        "query": query,
        "as_of": as_of.isoformat(),
        "depth": depth,
        "geography": geography,
        "query_type": decomposed["query_type"],
        "restated": decomposed["restated"],
        "scope": {
            "temporal": f"Prioritize {as_of.year - 5}–{as_of.year}; foundational older work allowed if labeled.",
            "geographic": geography,
            "source_types_in": source_types,
            "exclusion_criteria": exclude,
            "min_sources": cfg["min_sources"],
            "verification_claims": cfg["verification_claims"],
        },
        "research_questions": decomposed["research_questions"],
        "hypotheses": decomposed["hypotheses"],
        "search_variants": variants,
        "tool_sequence": tool_sequence(depth, decomposed["query_type"]),
        "parallelization": [
            "Independent sub-questions may be searched in the same round.",
            "Do not parallelize verification of a claim with its first acquisition.",
        ],
        "replan_triggers": [
            "A pivotal claim has <2 independent high/medium-integrity sources.",
            "Conflicting high-integrity findings exceed two unresolved disputes.",
            "New evidence falsifies a scope assumption (population, jurisdiction, date).",
            "Paywalls or tool failures block all primary paths for an anchor source.",
        ],
        "early_stop": cfg["early_stop"],
        "premortem": premortem(decomposed["query_type"], depth),
        "scripts": {
            "decompose": "scripts/question_decomposer.py",
            "credibility": "scripts/source_credibility.py",
            "matrix": "scripts/evidence_matrix.py",
            "contradictions": "scripts/contradiction_detector.py",
            "gaps": "scripts/coverage_gap_analyzer.py",
            "package": "scripts/output_packager.py",
        },
        "effort_tier": depth,
        "estimated_tool_rounds": cfg["tool_rounds"],
    }
    return plan


def format_text(plan: Dict[str, Any]) -> str:
    lines = [
        "DEEP RESEARCH PLAN",
        "=" * 72,
        f"As of:    {plan['as_of']}",
        f"Depth:    {plan['depth']}  (tool rounds ≈ {plan['estimated_tool_rounds']})",
        f"Type:     {plan['query_type']}",
        f"Geo:      {plan['geography']}",
        f"Query:    {plan['query']}",
        f"Restated: {plan['restated']}",
        "",
        "Scope",
        f"  Temporal: {plan['scope']['temporal']}",
        f"  Sources in: {', '.join(plan['scope']['source_types_in'])}",
        f"  Min sources / verification claims: {plan['scope']['min_sources']} / {plan['scope']['verification_claims']}",
        "  Exclude:",
    ]
    for item in plan["scope"]["exclusion_criteria"]:
        lines.append(f"    - {item}")
    lines.append("")
    lines.append("Research questions")
    for q in plan["research_questions"]:
        lines.append(f"  [{q['id']}] {q['question']}")
    lines.append("")
    lines.append("Search variants")
    for idx, variant in enumerate(plan["search_variants"], start=1):
        lines.append(f"  {idx}. {variant}")
    lines.append("")
    lines.append("Tool sequence")
    for step in plan["tool_sequence"]:
        lines.append(f"  {step['phase']}: {step['action']}")
    lines.append("")
    lines.append("Replan triggers")
    for item in plan["replan_triggers"]:
        lines.append(f"  - {item}")
    lines.append(f"Early stop: {plan['early_stop']}")
    lines.append("")
    lines.append("Pre-mortem")
    for mode in plan["premortem"]:
        lines.append(f"  Failure: {mode['failure']}")
        lines.append(f"    Mitigate: {mode['mitigation']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a phased research plan from a query and constraints."
    )
    parser.add_argument("positional", nargs="?", help="Research query text")
    parser.add_argument("--query", help="Research query")
    parser.add_argument("--input", help="JSON request with query and optional constraints")
    parser.add_argument("--depth", choices=["light", "medium", "deep"], help="Effort tier")
    parser.add_argument("--as-of", dest="as_of", help="As-of date YYYY-MM-DD")
    parser.add_argument("--geography", help="Geographic scope (default: global)")
    parser.add_argument(
        "--include-source-types",
        dest="include_source_types",
        help="Comma-separated source types",
    )
    parser.add_argument("--exclude", help="Comma-separated exclusion criteria")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        request = load_request(args)
        if isinstance(request.get("exclude"), str) and "," in request["exclude"]:
            request["exclude"] = [p.strip() for p in request["exclude"].split(",") if p.strip()]
        plan = generate_plan(request)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(plan, indent=2))
    else:
        print(format_text(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
