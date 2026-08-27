#!/usr/bin/env python3
"""Deterministic research planner for the deep-research skill.

From a query plus optional notes, emit sub-questions, hypotheses, source
types, search queries, a pre-mortem, effort tier, risk class, DAG phases,
and replan triggers. Keyword heuristics only. No network, no LLM.

Usage:
    python research_planner.py --query "Does retrieval quality dominate agentic RAG accuracy?"
    python research_planner.py --query "..." --notes notes.txt --tier deep --domain scientific --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

TIERS = ("light", "standard", "deep", "adversarial")
DOMAINS = ("auto", "scientific", "legal", "policy", "market", "medical", "geopolitical", "technical", "general")

DOMAIN_SIGNALS = {
    "legal": ("law", "legal", "court", "statute", "litigation", "employment", "contract", "liability",
              "precedent", "tribunal", "plaintiff", "defendant", "compliance", "judgment", "act "),
    "medical": ("health", "clinical", "trial", "disease", "patient", "treatment", "diagnosis",
                "drug", "epidemiolog", "mortality", "who ", "cdc", "fda", "vaccine"),
    "market": ("market", "competitor", "pricing", "tam ", "market share", "industry", "revenue",
               "saas", "go-to-market", "customer", "pricing page"),
    "scientific": ("study", "experiment", "paper", "replication", "rct", "meta-analysis",
                   "hypothesis", "peer-reviewed", "doi", "p-value", "effect size"),
    "policy": ("government", "legislation", "bill", "agency", "policy", "regulator",
               "public sector", "white paper", "consultation"),
    "geopolitical": ("war", "treaty", "sanctions", "election", "diplomacy", "nato", "geopolit",
                     "conflict", "sovereign", "alliance"),
    "technical": ("architecture", "cve", "vendor", "due diligence", "latency", "protocol",
                  "api", "benchmark", "throughput", "exploit"),
}

RISK_R3 = ("misinfo", "disinfo", "conspiracy", "hoax", "polarized", "contested", "adversarial",
           "debunk", "cover-up", "scandal")
RISK_R2 = ("legal", "medical", "safety", "clinical", "litigation", "public claim", "high-stakes",
           "child", "suicide", "weapon", "diagnosis")
RISK_R1 = ("decision", "invest", "strategy", "hire", "budget", "roadmap", "vendor", "buy")

SOURCE_TYPES = {
    "legal": ["primary legislation", "case law / judgments", "regulator guidance", "explanatory memoranda",
              "secondary commentary", "parliamentary records"],
    "medical": ["systematic reviews / Cochrane", "RCTs and registries", "regulator labels (FDA/EMA)",
                "surveillance datasets", "clinical guidelines", "preprints (caveated)"],
    "market": ["filings (10-K, annual reports)", "pricing pages / archives", "independent analyst notes",
               "customer reviews", "job postings", "traffic/SEO signals"],
    "scientific": ["peer-reviewed papers", "preprints", "replication packages / OSF", "datasets",
                   "methods critiques", "conference proceedings"],
    "policy": ["statute / bill text", "agency reports", "budget papers", "consultation submissions",
               "think tanks across spectrum", "administrative data"],
    "geopolitical": ["official statements", "treaty / UN docs", "conflict datasets (ACLED/UCDP)",
                     "local-language journalism", "IO reports", "satellite / trade stats"],
    "technical": ["primary specs", "CVE/NVD", "vendor docs", "independent benchmarks",
                  "source code / RFCs", "postmortems"],
    "general": ["government / IGO", "peer-reviewed", "primary documents", "high-quality journalism",
                "datasets", "stakeholder testimony"],
}

PREMORTEM = [
    "Data gap: the decisive primary source is paywalled, unreleased, or never collected.",
    "Source bias: the first cluster of hits shares funding, ideology, or a syndication origin.",
    "Framing error: the query smuggles a conclusion (loaded verbs, false dichotomy).",
    "Recency effect: a 2025-2026 shift is missed, or an old finding is treated as current.",
    "Synthesis drift: later writing answers a cleaner question than the user asked.",
    "Overconfidence: triangulation is actually one study cited three times.",
    "Semantic drift in retrieval: query expansion walks off the original intent.",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def detect_domain(query: str, notes: str, forced: str) -> Tuple[str, List[str]]:
    if forced and forced != "auto":
        return forced, [f"domain forced by --domain {forced}"]
    blob = f"{query} {notes}".lower()
    scores = {d: sum(1 for sig in sigs if sig in blob) for d, sigs in DOMAIN_SIGNALS.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "general", ["no domain keyword hits; default general"]
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    reasons = [f"{d}:{n}" for d, n in ranked if n]
    return best, reasons


def detect_risk(query: str, notes: str, domain: str) -> str:
    blob = f"{query} {notes}".lower()
    if any(tok in blob for tok in RISK_R3) or " vs " in blob:
        return "R3"
    if domain in ("legal", "medical") or any(tok in blob for tok in RISK_R2):
        return "R2"
    if any(tok in blob for tok in RISK_R1) or domain in ("market", "technical"):
        return "R1"
    return "R0"


def detect_tier(explicit: Optional[str], risk: str, query: str) -> str:
    if explicit:
        return explicit
    words = len(query.split())
    if risk == "R3":
        return "adversarial"
    if risk == "R2" or words > 40:
        return "deep"
    if words < 8 and risk == "R0":
        return "light"
    return "standard"


def split_questions(query: str, domain: str) -> List[str]:
    q = normalize(query).rstrip("?")
    base = [
        f"What is the precise, falsifiable claim inside: {q}?",
        f"What primary evidence exists for the affirmative case?",
        f"What is the strongest disconfirming evidence?",
        f"How has the evidence or expert consensus changed over the last 5 years?",
        f"Who are the stakeholders, and who funds or controls the main sources?",
    ]
    extras = {
        "legal": [
            "What is black-letter law vs enforcement practice vs commentary?",
            "Which jurisdiction, forum, and date range actually apply?",
        ],
        "medical": [
            "What is the study design, population, and absolute effect size — not relative risk alone?",
            "What do regulators and independent systematic reviews currently say?",
        ],
        "market": [
            "What is observable (filings, prices, usage) vs inferred (TAM, intent)?",
            "Where could competitor or vendor marketing be mistaken for evidence?",
        ],
        "scientific": [
            "Has the key result been independently replicated, and at what power?",
            "What would a methods critic flag first (confounding, multiple comparisons, leakage)?",
        ],
        "policy": [
            "What does the operative instrument actually require, vs political talking points?",
            "What are implementation costs, incidence, and unintended effects?",
        ],
        "geopolitical": [
            "What do primary official texts say vs subsequent media frames?",
            "Which local-language or on-the-ground sources contradict the dominant English narrative?",
        ],
        "technical": [
            "What is measured (benchmark, CVE, latency) vs vendor claim?",
            "What failure modes appear in postmortems or independent audits?",
        ],
        "general": [
            "Which terms in the query need a glossary or operational definition?",
        ],
    }
    questions = base + extras.get(domain, extras["general"])
    return questions[:8]


def hypotheses(query: str) -> List[Dict[str, str]]:
    q = normalize(query)
    return [
        {
            "id": "H1",
            "statement": f"The dominant public answer to '{q}' is roughly correct and well-supported.",
            "status": "untested",
            "falsifier": "Two independent high-integrity sources that contradict the dominant answer.",
        },
        {
            "id": "H2",
            "statement": "Apparent consensus is an artifact of syndication, shared funding, or citation rings.",
            "status": "untested",
            "falsifier": "At least two independent provenance clusters with primary data agreeing.",
        },
        {
            "id": "H3",
            "statement": "The question as asked mixes a factual dispute with a value or definitional dispute.",
            "status": "untested",
            "falsifier": "Operational definitions on all sides collapse to one measurable quantity.",
        },
        {
            "id": "H4",
            "statement": "The best available evidence is stale relative to the decision window.",
            "status": "untested",
            "falsifier": "A primary source inside the scoped recency window confirming the same result.",
        },
        {
            "id": "H5",
            "statement": "A minority or outlier position has stronger methods than the popular one.",
            "status": "untested",
            "falsifier": "Methods review shows the outlier is weaker on sample, identification, or transparency.",
        },
    ]


def effort_budget(tier: str) -> Dict[str, Any]:
    return {
        "light": {
            "subquestions": "3-4",
            "search_families": "direct + one contradiction + one primary-source family",
            "sources_target": "5-10",
            "verification_loops": 0,
            "red_team": False,
            "max_tool_rounds": 3,
        },
        "standard": {
            "subquestions": "5-8",
            "search_families": "all nine families, at least one query each",
            "sources_target": "10-20",
            "verification_loops": 1,
            "red_team": False,
            "max_tool_rounds": 6,
        },
        "deep": {
            "subquestions": "6-8",
            "search_families": "full taxonomy + multilingual if material",
            "sources_target": "20+",
            "verification_loops": 2,
            "red_team": True,
            "max_tool_rounds": 10,
        },
        "adversarial": {
            "subquestions": "6-8 plus opposing-camp steelman",
            "search_families": "full taxonomy + dedicated disconfirming pass",
            "sources_target": "20+ across ≥3 provenance clusters",
            "verification_loops": 2,
            "red_team": True,
            "max_tool_rounds": 12,
        },
    }[tier]


def seed_queries(query: str, domain: str, jurisdiction: Optional[str]) -> List[Dict[str, str]]:
    quoted = f'"{normalize(query)}"'
    gov = "site:.gov"
    if jurisdiction and jurisdiction.upper() == "AU":
        gov = "site:.gov.au"
    elif jurisdiction and jurisdiction.upper() == "UK":
        gov = "site:.gov.uk"
    elif jurisdiction and jurisdiction.upper() == "EU":
        gov = "site:europa.eu"
    families = [
        ("direct", quoted),
        ("direct", f"{query} evidence"),
        ("synonym", f"{query} overview"),
        ("contradiction", f"{quoted} criticism OR limitations OR 'failed to'"),
        ("contradiction", f"{quoted} controversy OR 'contrary evidence'"),
        ("site_academic", f"{quoted} site:arxiv.org OR site:.edu"),
        ("site_gov", f"{quoted} {gov}"),
        ("filetype_pdf", f"{quoted} filetype:pdf"),
        ("recency", f"{quoted} after:{datetime.now(timezone.utc).year - 2}-01-01"),
        ("stakeholder", f"{quoted} regulator OR industry OR critic"),
        ("dataset", f"{query} dataset OR statistics OR 'open data'"),
    ]
    if domain == "legal":
        families.append(("site_gov", f"{quoted} legislation OR judgment OR 'explanatory memorandum'"))
    if domain == "medical":
        families.append(("site_academic", f"{quoted} site:pubmed.ncbi.nlm.nih.gov"))
    return [{"family": f, "query": q} for f, q in families]


def replan_triggers(tier: str) -> List[str]:
    items = [
        "A pivotal claim still has fewer than 2 independent high/medium-integrity sources after the first acquisition round.",
        "Conflict count among medium+ sources exceeds 3 and is not classified (factual vs interpretive vs value).",
        "Horizon scan yields <40% non-news sources.",
        "A new primary document contradicts the working hypothesis.",
        "Tool failure, paywall, or truncation on an anchor source.",
        "Query restatement in Phase 1 no longer matches user intent after evidence arrives (semantic drift).",
    ]
    if tier in ("deep", "adversarial"):
        items.append("Red-team pass finds a citation-laundering cluster or hallucinated source.")
    return items


def dag(tier: str) -> List[Dict[str, Any]]:
    phases = [
        {"id": "P0", "name": "intake", "depends_on": [], "parallel": False},
        {"id": "P1", "name": "deconstruct_and_plan", "depends_on": ["P0"], "parallel": False},
        {"id": "P2", "name": "horizon_scan", "depends_on": ["P1"], "parallel": True,
         "note": "Issue independent search families in one tool batch."},
        {"id": "P3", "name": "primary_extraction", "depends_on": ["P2"], "parallel": True},
        {"id": "P4", "name": "source_criticism", "depends_on": ["P3"], "parallel": True},
        {"id": "P5", "name": "claim_graph", "depends_on": ["P4"], "parallel": False},
        {"id": "P6", "name": "steelman_bias_audit", "depends_on": ["P5"], "parallel": False},
        {"id": "P7", "name": "uncertainty", "depends_on": ["P5"], "parallel": False},
        {"id": "P8", "name": "synthesis", "depends_on": ["P6", "P7"], "parallel": False},
        {"id": "P9", "name": "red_team_verify", "depends_on": ["P8"], "parallel": False},
        {"id": "P10", "name": "case_log", "depends_on": ["P9"], "parallel": False},
    ]
    if tier == "light":
        skip = {"P6", "P9"}
        phases = [p for p in phases if p["id"] not in skip]
        for p in phases:
            p["depends_on"] = [d for d in p["depends_on"] if d not in skip]
    return phases


def early_stop(tier: str) -> List[str]:
    return [
        "Every in-scope sub-question has an evidence status (supported / contested / insufficient).",
        "Pivotal claims meet the corroboration rule for this tier: "
        + {"light": "1 primary or 2 secondary.", "standard": "2 independent medium+ sources.",
           "deep": "2 independent medium+ plus verification loop.",
           "adversarial": "2 independent medium+ across ≥2 clusters plus red-team."}[tier],
        "Contradiction family has been run at least once.",
        "Confidence has not moved more than 5 points in the last verification pass (diminishing returns).",
        "Do not stop solely because a fluent narrative is available.",
    ]


def plan(query: str, notes: str, tier: Optional[str], domain_arg: str, jurisdiction: Optional[str]) -> Dict[str, Any]:
    domain, domain_reasons = detect_domain(query, notes, domain_arg)
    risk = detect_risk(query, notes, domain)
    chosen_tier = detect_tier(tier, risk, query)
    return {
        "query_original": query,
        "query_restated": normalize(query),
        "assumptions_to_flag": [
            "The query's key nouns have a single operational definition.",
            "The relevant time window is the last 5 years unless stated otherwise.",
            "English-language sources are sufficient unless a local-language corpus is material.",
        ],
        "domain": domain,
        "domain_signals": domain_reasons,
        "jurisdiction_pack": jurisdiction,
        "risk_class": risk,
        "risk_class_meaning": {
            "R0": "Informational. Standard corroboration.",
            "R1": "Operational / business decision. Verification loop on pivotal claims.",
            "R2": "High-stakes (legal, medical-adjacent, public, safety). Deep tier default; no diagnostic or legal advice.",
            "R3": "Adversarial or polarized. Dedicated disconfirming pass and red-team required.",
        }[risk],
        "effort_tier": chosen_tier,
        "budget": effort_budget(chosen_tier),
        "subquestions": split_questions(query, domain),
        "hypotheses": hypotheses(query),
        "source_types": SOURCE_TYPES.get(domain, SOURCE_TYPES["general"]),
        "search_queries": seed_queries(query, domain, jurisdiction),
        "pre_mortem": PREMORTEM,
        "mitigations": [
            "Run contradiction and stakeholder families before synthesis.",
            "Score every non-trivial source with source_scorer.py.",
            "Atomize claims into the ledger before writing prose.",
            "Cap confidence via confidence_calibrator.py; never self-assign Very High without primaries.",
        ],
        "replan_triggers": replan_triggers(chosen_tier),
        "early_stop": early_stop(chosen_tier),
        "dag": dag(chosen_tier),
        "scripts_to_run": [
            "scripts/search_query_generator.py --topic ... --domain ...",
            "scripts/source_scorer.py --title ... --type ...",
            "scripts/claim_ledger.py init --query ...",
            "scripts/confidence_calibrator.py --n-sources ...",
            "scripts/bias_audit.py --input report.md",
            "scripts/citation_integrity.py --ledger ledger.json",
            "scripts/report_assembler.py --ledger ledger.json",
        ],
        "references_to_load": [
            "references/search-query-playbook.md  (Phase 2)",
            "references/source-evaluation-framework.md  (Phase 4)",
            "references/claim-graph-and-triangulation.md  (Phase 5)",
            "references/bias-and-adversarial-analysis.md  (Phase 6)",
            "references/uncertainty-and-calibration.md  (Phase 7)",
            "references/output-contracts.md  (Phase 8)",
            "references/red-team-checklist.md  (Phase 9)",
            "references/domain-lenses.md  (if domain != general)",
            "references/agentic-research-patterns.md  (if using subagents)",
        ],
        "when_not_to_use": [
            "Simple factual lookup with a single canonical source.",
            "Requests for medical diagnosis, legal advice, or instructions to cause harm.",
            "Tasks that are purely generative (drafting copy with no evidential claim).",
        ],
    }


def render_human(result: Dict[str, Any]) -> str:
    lines = [
        f"Query:        {result['query_restated']}",
        f"Domain:       {result['domain']}  ({', '.join(result['domain_signals'])})",
        f"Risk class:   {result['risk_class']} — {result['risk_class_meaning']}",
        f"Effort tier:  {result['effort_tier']}",
        f"Jurisdiction: {result['jurisdiction_pack'] or '(none)'}",
        "",
        "Budget:",
    ]
    for k, v in result["budget"].items():
        lines.append(f"  {k}: {v}")
    lines.append("\nSub-questions:")
    for i, q in enumerate(result["subquestions"], 1):
        lines.append(f"  {i}. {q}")
    lines.append("\nHypotheses:")
    for h in result["hypotheses"]:
        lines.append(f"  {h['id']}: {h['statement']}")
        lines.append(f"      falsifier: {h['falsifier']}")
    lines.append("\nSource types:")
    for s in result["source_types"]:
        lines.append(f"  - {s}")
    lines.append("\nSeed queries:")
    for item in result["search_queries"]:
        lines.append(f"  [{item['family']}] {item['query']}")
    lines.append("\nPre-mortem:")
    for p in result["pre_mortem"]:
        lines.append(f"  - {p}")
    lines.append("\nReplan triggers:")
    for t in result["replan_triggers"]:
        lines.append(f"  - {t}")
    lines.append("\nDAG:")
    for node in result["dag"]:
        deps = ",".join(node["depends_on"]) or "-"
        par = " parallel" if node.get("parallel") else ""
        lines.append(f"  {node['id']} {node['name']} (after {deps}){par}")
    lines.append("\nEarly-stop:")
    for s in result["early_stop"]:
        lines.append(f"  - {s}")
    return "\n".join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit a structured deep-research plan from a query (deterministic heuristics)."
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--notes", help="Path to extra notes file")
    parser.add_argument("--notes-text", dest="notes_text", help="Inline notes")
    parser.add_argument("--tier", choices=TIERS)
    parser.add_argument("--domain", choices=DOMAINS, default="auto")
    parser.add_argument("--jurisdiction", help="Optional pack: AU, UK, US, EU, CA, NZ, IN, SG")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    notes = args.notes_text or ""
    if args.notes:
        try:
            with open(args.notes, "r", encoding="utf-8") as handle:
                notes = handle.read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    result = plan(args.query, notes, args.tier, args.domain, args.jurisdiction)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_human(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
