#!/usr/bin/env python3
"""Research Plan Generator — Structured deep research planning from a query.

Generates sub-questions, hypotheses, scope boundaries, source strategy,
verification targets, milestones, and replan triggers.

Usage:
    python3 research_plan_generator.py --query "EU AI Act impact on SaaS" --depth deep
    python3 research_plan_generator.py --input plan_input.json --format json
    python3 research_plan_generator.py --query "Topic" --domain legal --format text --output plan.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any


DEPTH_PROFILES = {
    "light": {
        "sub_questions": (3, 4),
        "hypotheses": (1, 2),
        "source_target": "5-10",
        "verification_passes": 1,
        "search_rounds": "1-2",
    },
    "medium": {
        "sub_questions": (4, 6),
        "hypotheses": (2, 4),
        "source_target": "15-25",
        "verification_passes": 2,
        "search_rounds": "2-3",
    },
    "deep": {
        "sub_questions": (6, 8),
        "hypotheses": (3, 5),
        "source_target": "30+",
        "verification_passes": 3,
        "search_rounds": "3-5",
    },
}

DOMAIN_SOURCE_PRIORITIES = {
    "general": [
        "peer-reviewed academic literature",
        "government and official statistics",
        "primary documents and datasets",
        "high-quality journalism with named sources",
        "expert institutional reports",
    ],
    "scientific": [
        "systematic reviews and meta-analyses",
        "peer-reviewed primary research (PubMed, arXiv with caveats)",
        "regulatory agency guidance (FDA, EMA, WHO)",
        "clinical trial registries",
        "replication studies and preprint caveats",
    ],
    "legal": [
        "statutes and regulations (primary law)",
        "court decisions and tribunal rulings",
        "official legislative history and explanatory memoranda",
        "regulatory agency guidance and enforcement actions",
        "law review and practitioner commentary (secondary)",
    ],
    "business": [
        "SEC/company filings and annual reports",
        "industry analyst reports (note conflicts)",
        "market data from reputable providers",
        "customer review aggregators and case studies",
        "competitor primary sources (pricing pages, job postings)",
    ],
    "policy": [
        "legislation and regulatory text",
        "government agency reports and statistics",
        "think tank analyses (note ideological positioning)",
        "stakeholder submissions and public consultations",
        "international body reports (UN, OECD, World Bank)",
    ],
}

DOMAIN_EXCLUSIONS = {
    "general": ["unsourced opinion blogs", "unverified social media as sole evidence"],
    "scientific": ["predatory journals", "single unreplicated preprints without caveats"],
    "legal": ["non-jurisdiction legal commentary presented as binding law"],
    "business": ["anonymous forum posts", "undisclosed sponsored content"],
    "policy": ["partisan op-eds without data", "cherry-picked statistics"],
}

SEARCH_QUERY_TEMPLATES = [
    '"{topic}" overview statistics',
    '"{topic}" systematic review OR meta-analysis',
    '"{topic}" primary source data filetype:pdf',
    '"{topic}" criticism limitations controversy',
    'site:.gov OR site:.edu "{topic}"',
    '"{topic}" expert consensus OR official guidance',
    '"{topic}" timeline history evolution',
    '"{topic}" stakeholder perspectives',
]

PREMORTEM_FAILURES = [
    {
        "mode": "Source selection bias",
        "mitigation": "Enforce source tier diversity; include disconfirming search queries",
    },
    {
        "mode": "Recency bias / outdated data",
        "mitigation": "Set temporal scope explicitly; check publication dates on all sources",
    },
    {
        "mode": "Shared-provenance echo chamber",
        "mitigation": "Trace claims to primary sources; require 2+ independent sources for pivotal claims",
    },
    {
        "mode": "Scope creep / query drift",
        "mitigation": "Revisit original query each phase; document replan triggers",
    },
    {
        "mode": "Overconfidence in synthesis",
        "mitigation": "Apply uncertainty ladder; run verification loop on top 3-5 findings",
    },
]

REPLAN_TRIGGERS = [
    "Major new evidence contradicts initial hypotheses",
    "Pivotal claim has fewer than 2 medium+ integrity sources after 2 search rounds",
    "Source landscape is sparser than expected (<50% sub-questions have evidence)",
    "User scope expansion or refinement requested",
    "Tool failures prevent access to critical primary sources",
]


def _tokenize_topic(query: str) -> list[str]:
    stop = {
        "the", "a", "an", "of", "on", "in", "for", "to", "and", "or", "is", "are",
        "what", "how", "why", "does", "do", "impact", "effect", "analysis", "research",
    }
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]+", query)
    return [w for w in words if w.lower() not in stop][:8]


def generate_sub_questions(query: str, domain: str, count: int) -> list[dict[str, str]]:
    topic = query.strip().rstrip("?")
    templates = [
        ("definition", f"What is the current consensus definition and scope of {topic}?"),
        ("magnitude", f"What quantitative evidence exists on the scale, rate, or magnitude of {topic}?"),
        ("causation", f"What causal mechanisms or drivers are supported by evidence for {topic}?"),
        ("stakeholders", f"Who are the key stakeholders affected by {topic}, and what are their documented positions?"),
        ("timeline", f"How has understanding or policy regarding {topic} evolved over time?"),
        ("controversy", f"What are the main contested claims about {topic}, and what evidence supports each side?"),
        ("regulatory", f"What legal, regulatory, or institutional frameworks govern {topic}?"),
        ("gaps", f"What significant evidence gaps or uncertainties remain regarding {topic}?"),
    ]
    if domain == "legal":
        templates[6] = ("jurisdiction", f"What jurisdictional variations and precedents apply to {topic}?")
    elif domain == "scientific":
        templates[1] = ("evidence_quality", f"What is the quality and replication status of key studies on {topic}?")
    elif domain == "business":
        templates[1] = ("market", f"What market data and competitive dynamics characterize {topic}?")

    selected = templates[:count]
    return [{"id": f"sq{i+1}", "type": t, "question": q} for i, (t, q) in enumerate(selected)]


def generate_hypotheses(query: str, count: int) -> list[dict[str, str]]:
    topic = query.strip().rstrip("?")
    pool = [
        {
            "id": "h1",
            "statement": f"The dominant evidence-supported view on {topic} is accurate and well-calibrated.",
            "falsifiable_by": "High-integrity sources demonstrating systematic error in the consensus view",
        },
        {
            "id": "h2",
            "statement": f"Recent developments have materially changed the evidence landscape for {topic}.",
            "falsifiable_by": "Temporal analysis showing stability in expert consensus and primary data",
        },
        {
            "id": "h3",
            "statement": f"Stakeholder narratives about {topic} diverge significantly from quantitative evidence.",
            "falsifiable_by": "Convergence between stakeholder claims and independent data sources",
        },
        {
            "id": "h4",
            "statement": f"Regulatory or institutional responses to {topic} are proportionate to documented evidence.",
            "falsifiable_by": "Evidence of regulatory action preceding or exceeding empirical support",
        },
        {
            "id": "h5",
            "statement": f"Significant evidence gaps prevent confident conclusions about {topic}.",
            "falsifiable_by": "Multiple high-integrity convergent sources addressing all core sub-questions",
        },
    ]
    return pool[:count]


def generate_search_queries(query: str) -> list[dict[str, str]]:
    topic = query.strip().rstrip("?")
    queries = []
    for i, tmpl in enumerate(SEARCH_QUERY_TEMPLATES[:8]):
        queries.append({
            "id": f"q{i+1}",
            "query": tmpl.format(topic=topic),
            "purpose": ["overview", "academic", "primary_docs", "contrarian",
                        "official", "consensus", "historical", "stakeholder"][i],
        })
    return queries


def generate_milestones(depth: str) -> list[dict[str, str]]:
    base = [
        {"phase": "1", "name": "Planning complete", "artifact": "research brief"},
        {"phase": "2", "name": "Horizon scan complete", "artifact": "source shortlist (70-80% coverage)"},
        {"phase": "3", "name": "Deep acquisition complete", "artifact": "evidence ledger populated"},
        {"phase": "4", "name": "Source scoring complete", "artifact": "credibility scores for all sources"},
        {"phase": "5", "name": "Synthesis + verification complete", "artifact": "evidence matrix + verification log"},
        {"phase": "6", "name": "Output delivered", "artifact": "layered report + appendix"},
    ]
    if depth == "light":
        return base[:4] + [base[-1]]
    return base


def build_plan(
    query: str,
    depth: str = "medium",
    domain: str = "general",
    temporal_scope: str | None = None,
    geographic_scope: str | None = None,
) -> dict[str, Any]:
    profile = DEPTH_PROFILES.get(depth, DEPTH_PROFILES["medium"])
    sq_count = profile["sub_questions"][1]
    h_count = profile["hypotheses"][1]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    temporal = temporal_scope or f"Evidence as of {now}; prioritize sources from last 5 years unless historical context required"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "query_restatement": f"Investigate: {query.strip()} — producing evidence-backed, auditable findings with explicit confidence bands.",
        "depth": depth,
        "domain": domain,
        "scope": {
            "temporal": temporal,
            "geographic": geographic_scope or "Global unless query specifies jurisdiction",
            "disciplinary_lenses": [domain, "critical source evaluation", "multi-perspective synthesis"],
            "source_priorities": DOMAIN_SOURCE_PRIORITIES.get(domain, DOMAIN_SOURCE_PRIORITIES["general"]),
            "exclusions": DOMAIN_EXCLUSIONS.get(domain, DOMAIN_EXCLUSIONS["general"]),
        },
        "depth_profile": profile,
        "sub_questions": generate_sub_questions(query, domain, sq_count),
        "hypotheses": generate_hypotheses(query, h_count),
        "search_queries": generate_search_queries(query),
        "premortem": PREMORTEM_FAILURES[:3],
        "replan_triggers": REPLAN_TRIGGERS,
        "verification_targets": [
            "Top 3-5 pivotal claims requiring 2+ independent medium+ sources",
            "Any claim where sources share common primary origin",
            "Contested claims with conflicting evidence",
        ],
        "output_artifacts": [
            "Executive summary (Layer 1)",
            "Key findings with confidence tags (Layer 2)",
            "Detailed analysis (Layer 3)",
            "Evidence appendix / source matrix (Layer 4)",
            "Limitations and gap analysis (Layer 5)",
        ],
        "milestones": generate_milestones(depth),
        "parallelization": {
            "independent_sub_questions": [f"sq{i}" for i in range(1, min(4, sq_count + 1))],
            "parallel_source_types": ["government/academic", "primary documents", "contrarian perspectives"],
        },
    }


def format_text(plan: dict[str, Any]) -> str:
    lines = [
        "=" * 72,
        "DEEP RESEARCH PLAN",
        f"Generated: {plan['generated_at']}",
        "=" * 72,
        "",
        f"Query: {plan['query']}",
        f"Depth: {plan['depth'].upper()} | Domain: {plan['domain']}",
        f"Target sources: {plan['depth_profile']['source_target']}",
        f"Verification passes: {plan['depth_profile']['verification_passes']}",
        "",
        "## Query Restatement",
        plan["query_restatement"],
        "",
        "## Scope",
        f"  Temporal: {plan['scope']['temporal']}",
        f"  Geographic: {plan['scope']['geographic']}",
        "  Source priorities:",
    ]
    for src in plan["scope"]["source_priorities"]:
        lines.append(f"    • {src}")
    lines.extend(["  Exclusions:"])
    for ex in plan["scope"]["exclusions"]:
        lines.append(f"    • {ex}")

    lines.extend(["", "## Sub-Questions"])
    for sq in plan["sub_questions"]:
        lines.append(f"  [{sq['id']}] ({sq['type']}) {sq['question']}")

    lines.extend(["", "## Hypotheses"])
    for h in plan["hypotheses"]:
        lines.append(f"  [{h['id']}] {h['statement']}")
        lines.append(f"         Falsifiable by: {h['falsifiable_by']}")

    lines.extend(["", "## Search Queries"])
    for q in plan["search_queries"]:
        lines.append(f"  [{q['id']}] ({q['purpose']}) {q['query']}")

    lines.extend(["", "## Pre-Mortem Failure Modes"])
    for pm in plan["premortem"]:
        lines.append(f"  • {pm['mode']}")
        lines.append(f"    Mitigation: {pm['mitigation']}")

    lines.extend(["", "## Replan Triggers"])
    for rt in plan["replan_triggers"]:
        lines.append(f"  • {rt}")

    lines.extend(["", "## Milestones"])
    for m in plan["milestones"]:
        lines.append(f"  Phase {m['phase']}: {m['name']} → {m['artifact']}")

    lines.extend(["", "## Output Artifacts"])
    for art in plan["output_artifacts"]:
        lines.append(f"  • {art}")

    lines.append("\n" + "=" * 72)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate structured deep research plans")
    parser.add_argument("--query", "-q", help="Research query or topic")
    parser.add_argument("--input", "-i", help="JSON input file with query, depth, domain, scope fields")
    parser.add_argument("--depth", choices=["light", "medium", "deep"], default="medium")
    parser.add_argument("--domain", choices=list(DOMAIN_SOURCE_PRIORITIES.keys()), default="general")
    parser.add_argument("--temporal-scope", help="Temporal boundary for evidence")
    parser.add_argument("--geographic-scope", help="Geographic/jurisdictional boundary")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")

    args = parser.parse_args()

    if args.input:
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
        plan = build_plan(
            query=data.get("query", ""),
            depth=data.get("depth", args.depth),
            domain=data.get("domain", args.domain),
            temporal_scope=data.get("temporal_scope"),
            geographic_scope=data.get("geographic_scope"),
        )
    elif args.query:
        plan = build_plan(
            query=args.query,
            depth=args.depth,
            domain=args.domain,
            temporal_scope=args.temporal_scope,
            geographic_scope=args.geographic_scope,
        )
    else:
        parser.error("Provide --query or --input")

    output = json.dumps(plan, indent=2) if args.format == "json" else format_text(plan)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Plan written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
