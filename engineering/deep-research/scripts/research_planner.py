#!/usr/bin/env python3
"""Research plan generator and question decomposer.

Turns a research topic into a structured, falsifiable plan: reframed query,
core questions, testable hypotheses, scope bounds, pre-mortem, tool strategy,
persona assignments, and replan triggers.

Stdlib only. No network. No LLM calls.

Usage:
    python research_planner.py --topic "Impact of hybrid work on software delivery"
    python research_planner.py --input brief.json --format json
    python research_planner.py --topic "..." --mode legal --effort deep --geo AU
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


TOPIC_SIGNALS = {
    "legal": [
        "law", "statute", "regulation", "court", "liability", "compliance",
        "act", "case law", "tribunal", "policy", "enforcement", "gdpr", "fda",
        "iso", "mdr", "employment", "dismissal", "fair work",
    ],
    "scientific": [
        "trial", "rct", "meta-analysis", "efficacy", "mechanism", "biology",
        "physics", "climate", "epidemiolog", "peer-reviewed", "preprint",
        "dose", "genome", "clinical",
    ],
    "market": [
        "market", "competitor", "pricing", "tam", "share", "customer", "icp",
        "revenue", "saas", "go-to-market", "positioning", "win rate",
    ],
    "technical": [
        "architecture", "api", "latency", "security", "database", "protocol",
        "framework", "benchmark", "open source", "cve", "implementation",
    ],
    "policy": [
        "government", "public", "welfare", "tax", "immigration", "education",
        "health system", "budget", "parliament", "white paper",
    ],
    "historical": [
        "history", "archive", "century", "war", "origin", "timeline",
        "historiography", "primary source",
    ],
}

EVIDENCE_BY_MODE = {
    "legal": [
        "primary legislation", "case law / judgments", "explanatory memoranda",
        "regulator guidance", "enforcement statistics", "commentary from both sides",
    ],
    "scientific": [
        "systematic reviews", "pre-registered RCTs", "open datasets",
        "replication studies", "conflict-of-interest disclosures", "preprints (caveated)",
    ],
    "market": [
        "filings", "pricing pages", "win/loss notes", "review sites",
        "hiring signals", "changelog / product moves", "independent analyst notes",
    ],
    "technical": [
        "source code / specs", "benchmarks with methodology", "CVEs / advisories",
        "architecture docs", "production postmortems", "standards (RFC, ISO)",
    ],
    "policy": [
        "official statistics", "legislation", "budget papers", "think-tank papers across spectrum",
        "affected-community testimony", "implementation evaluations",
    ],
    "historical": [
        "primary documents", "archival records", "contemporaneous press",
        "historiographical debate", "material evidence",
    ],
    "general": [
        "primary documents", "high-quality secondary synthesis", "quantitative data",
        "qualitative testimony", "expert consensus statements", "disconfirming sources",
    ],
}

QUESTION_TEMPLATES = {
    "general": [
        "What is the current, evidence-based answer to: {topic}?",
        "What are the strongest competing explanations or positions, and what evidence supports each?",
        "Which claims are well-established vs contested vs unknown as of the research date?",
        "What mechanisms (causal, institutional, technical) would have to be true for the leading claim to hold?",
        "Who are the stakeholders, what incentives do they have, and how does that shape the evidence base?",
        "What would falsify the leading hypothesis, and has that test been run?",
        "What are the practical implications and decision-relevant uncertainties for the intended audience?",
    ],
    "legal": [
        "What is the black-letter rule (statute, regulation, binding precedent) relevant to {topic}?",
        "How do courts or tribunals actually apply the rule (enforcement practice vs text)?",
        "What onus, standing, time limits, and procedural fairness issues apply?",
        "Which facts, if proven, would change the legal outcome?",
        "Where do jurisdictions diverge, and which is in scope?",
        "What remedies, appeal paths, and practical constraints exist?",
        "What competing interpretations exist among regulators, advocates, and courts?",
    ],
    "scientific": [
        "What is the current consensus, if any, on {topic}, and how recently did it form?",
        "What is the quality of the evidence hierarchy (meta-analysis, RCT, observational, mechanistic)?",
        "What effect sizes, confidence intervals, and heterogeneity are reported?",
        "What confounders, biases, and failed replications exist?",
        "How do funding sources and researcher degrees of freedom affect the literature?",
        "What would a decisive next experiment look like?",
        "What harms, opportunity costs, or implementation gaps sit between evidence and practice?",
    ],
    "market": [
        "How large is the relevant market for {topic}, by which definition, from which sources?",
        "Who are direct, indirect, and future competitors, and on which axes do they differ?",
        "What pricing, packaging, and switching-cost moves have occurred in the last 18 months?",
        "Why do buyers choose one option over another (win/loss evidence, not vendor claims)?",
        "Which claims in marketing or analyst notes are corroborated by primary evidence?",
        "What leading indicators (hiring, filings, partnerships) signal a shift?",
        "What decision should a product/GTM leader take, and what would change that decision?",
    ],
    "technical": [
        "What is the actual system/behavior under {topic}, as specified and as implemented?",
        "What are the performance, reliability, and security characteristics with methodology?",
        "What failure modes and operational constraints are documented in postmortems or issues?",
        "How do alternative designs compare on the criteria that matter for this decision?",
        "Which claims come from vendors vs independent benchmarks vs source inspection?",
        "What is the migration, lock-in, and maintenance cost of each option?",
        "What unknowns remain that would change the architecture choice?",
    ],
}

PREMORTEM_BANK = [
    {
        "failure_mode": "Source-selection bias (convenient, English-language, first-page results)",
        "mitigation": "Force 4–8 query variants, site: diversity packs, and an explicit outlier/contrarian search.",
    },
    {
        "failure_mode": "Shared provenance treated as independent corroboration",
        "mitigation": "Cluster sources by publisher family, wire service, and citation graph; require 2 independent high-integrity sources for pivotal claims.",
    },
    {
        "failure_mode": "Recency illusion or stale consensus",
        "mitigation": "Date-stamp every finding; recency-weight scores; flag rapidly evolving topics for a monitor note.",
    },
    {
        "failure_mode": "Semantic drift across iterative retrieval",
        "mitigation": "Revisit the reframed query at each phase; persist original intent in the evidence store.",
    },
    {
        "failure_mode": "Overconfidence in synthesis (narrative smoother than evidence)",
        "mitigation": "Run skeptic persona + contradiction detector; attach confidence bands with drivers.",
    },
    {
        "failure_mode": "Paywall / access gaps silently dropped",
        "mitigation": "Log access failures; seek open versions, DOI, or official mirrors; never fabricate access.",
    },
    {
        "failure_mode": "False equivalence on contested topics",
        "mitigation": "Steelman each side, then report evidential weight — not a 50/50 split by default.",
    },
    {
        "failure_mode": "Scope creep into adjacent interesting questions",
        "mitigation": "Write exclusion criteria; park out-of-scope items in a parking lot, do not chase them.",
    },
]

PERSONAS = [
    {
        "id": "analyst",
        "role": "Map the landscape, extract claims, keep the evidence store clean.",
        "pass": "gather",
    },
    {
        "id": "domain_expert",
        "role": "Judge methodological quality, jargon, and what a specialist would consider missing.",
        "pass": "triangulate",
    },
    {
        "id": "skeptic",
        "role": "Hunt disconfirming evidence, shared provenance, and overclaiming.",
        "pass": "challenge",
    },
    {
        "id": "decision_maker",
        "role": "Demand decision-relevance, residual risk, and what would change the call.",
        "pass": "deliver",
    },
]

GEO_HINTS = {
    "AU": {
        "note": "Prioritize ABS, Fair Work, Productivity Commission, ASIC, AustLII, state vs federal split.",
        "source_examples": [
            "abs.gov.au", "fairwork.gov.au", "fwc.gov.au", "legislation.gov.au",
            "austlii.edu.au", "pc.gov.au", "treasury.gov.au",
        ],
    },
    "US": {
        "note": "Prioritize .gov, SEC EDGAR, GAO, CBO, federal vs state, PACER/court opinions when legal.",
        "source_examples": [
            "sec.gov", "gao.gov", "cbo.gov", "congress.gov", "census.gov", "nih.gov",
        ],
    },
    "EU": {
        "note": "Prioritize EUR-Lex, Eurostat, national stats offices, and EU vs member-state competence.",
        "source_examples": [
            "europa.eu", "eur-lex.europa.eu", "ec.europa.eu", "eurostat.ec.europa.eu",
        ],
    },
    "UK": {
        "note": "Prioritize legislation.gov.uk, ONS, GOV.UK, Hansard, and devolved administrations.",
        "source_examples": [
            "gov.uk", "legislation.gov.uk", "ons.gov.uk", "parliament.uk",
        ],
    },
    "GLOBAL": {
        "note": "Prefer international primary sources (UN, OECD, WHO, ISO, IMF) then regional primaries.",
        "source_examples": [
            "oecd.org", "who.int", "imf.org", "un.org", "worldbank.org", "iso.org",
        ],
    },
}

EFFORT_TIERS = {
    "light": {
        "questions": 3,
        "hypotheses": 2,
        "tool_rounds": "1–2",
        "verification_loop": False,
        "description": "Decision support: executive brief + key findings + caveats.",
    },
    "medium": {
        "questions": 5,
        "hypotheses": 3,
        "tool_rounds": "3–5",
        "verification_loop": True,
        "description": "Standard deep research: layered report + evidence appendix + skeptic pass.",
    },
    "deep": {
        "questions": 8,
        "hypotheses": 5,
        "tool_rounds": "6+",
        "verification_loop": True,
        "description": "Exhaustive: multi-persona, continuing store, decision brief, research agenda.",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_mode(topic: str, forced: Optional[str] = None) -> str:
    if forced and forced != "auto":
        return forced
    text = topic.lower()
    scores = {mode: sum(1 for tok in toks if tok in text) for mode, toks in TOPIC_SIGNALS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "research"


def split_clauses(topic: str) -> List[str]:
    parts = re.split(r"\b(?:and|vs\.?|versus|compared to|or)\b", topic, flags=re.I)
    return [p.strip(" ?.") for p in parts if len(p.strip()) > 3]


def reframe_query(topic: str, mode: str) -> Dict[str, Any]:
    cleaned = re.sub(r"\s+", " ", topic).strip().rstrip("?")
    assumptions = []
    if re.search(r"\b(best|worst|always|never|prove|debunk)\b", cleaned, re.I):
        assumptions.append(
            "Loaded evaluative language detected; reframe toward comparative evidence rather than a verdict."
        )
    if "?" not in topic and mode != "general":
        assumptions.append(f"Query is a topic, not a question; treating as a {mode} investigation.")
    implicit = []
    if re.search(r"\bshould\b", cleaned, re.I):
        implicit.append("Normative 'should' — separate empirical claims from value judgments.")
    reframed = cleaned
    if not cleaned.lower().startswith(("what", "how", "why", "which", "who", "when", "where", "does")):
        reframed = f"What does current high-integrity evidence show about {cleaned}?"
    return {
        "original": topic,
        "reframed": reframed,
        "assumptions": assumptions,
        "implicit_judgments": implicit,
        "falsifiable": bool(re.search(r"\b(does|is|are|did|will|can|how much|what)\b", reframed, re.I)),
    }


def build_questions(topic: str, mode: str, n: int) -> List[Dict[str, Any]]:
    templates = QUESTION_TEMPLATES.get(mode, QUESTION_TEMPLATES["general"])
    extras = QUESTION_TEMPLATES["general"]
    ordered = templates + [t for t in extras if t not in templates]
    clauses = split_clauses(topic)
    questions = []
    for i, tmpl in enumerate(ordered[:n], start=1):
        text = tmpl.format(topic=topic.strip().rstrip("?"))
        qid = f"Q{i}"
        evidence = EVIDENCE_BY_MODE.get(mode, EVIDENCE_BY_MODE["general"])
        priority = "pivotal" if i <= 3 else "supporting"
        questions.append({
            "id": qid,
            "text": text,
            "priority": priority,
            "evidence_types": evidence[:4] if i <= 3 else evidence[2:6] or evidence[:3],
            "related_entities": clauses[:3],
        })
    return questions


def build_hypotheses(topic: str, questions: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    stems = [
        ("H_lead", "The leading public claim about {topic} is approximately correct and survives independent sources."),
        ("H_alt", "An alternative mechanism or interpretation explains the same observations better than the leading claim."),
        ("H_null", "Apparent effects around {topic} are measurement artifacts, selection effects, or narrative without causal support."),
        ("H_scope", "Effects exist but only in a narrower population, period, or jurisdiction than popular claims imply."),
        ("H_incentive", "Stakeholder incentives (funding, politics, commercial) materially distort the available evidence base."),
    ]
    hyps = []
    for i, (hid, tmpl) in enumerate(stems[:n], start=1):
        related = [q["id"] for q in questions[: min(3, len(questions))]]
        hyps.append({
            "id": f"H{i}",
            "code": hid,
            "text": tmpl.format(topic=topic.strip().rstrip("?")),
            "status": "untested",
            "falsification_test": (
                "Identify the observation that would most reduce posterior belief, then search for it first."
            ),
            "related_questions": related,
        })
    return hyps


def build_scope(
    mode: str,
    effort: str,
    geo: str,
    since: Optional[str],
    until: Optional[str],
    exclude: List[str],
) -> Dict[str, Any]:
    geo_meta = GEO_HINTS.get(geo.upper(), GEO_HINTS["GLOBAL"])
    source_types = [
        "primary documents",
        "government / official statistics",
        "peer-reviewed or equivalently reviewed",
        "high-quality journalism",
        "think tanks across the political/methodological spectrum",
        "datasets and filings",
    ]
    default_exclusions = [
        "Unverified social posts as standalone evidence",
        "Anonymous blogs without data or primary citation",
        "Vendor collateral without independent corroboration",
        "Paywalled claims that cannot be verified from an open primary",
    ]
    return {
        "temporal": {
            "since": since or "unspecified — prefer last 5 years plus foundational sources",
            "until": until or "as of research date",
            "as_of_required": True,
        },
        "geographic": {
            "code": geo.upper(),
            "note": geo_meta["note"],
            "priority_domains": geo_meta["source_examples"],
        },
        "mode": mode,
        "effort": effort,
        "source_types_in_scope": source_types,
        "exclusion_criteria": default_exclusions + exclude,
        "disciplinary_lenses": [mode] if mode != "general" else ["empirical", "institutional", "stakeholder"],
    }


def build_plan(mode: str, effort: str, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    tier = EFFORT_TIERS[effort]
    phases = [
        {"id": "ingest", "goal": "Capture user goal, constraints, prior store, and success criteria."},
        {"id": "plan", "goal": "Decompose questions, hypotheses, scope, pre-mortem, and tool DAG."},
        {"id": "gather", "goal": "Horizon scan then targeted primary-source extraction into the evidence store."},
        {"id": "triangulate", "goal": "Score sources, map claims, detect contradictions, measure coverage."},
        {"id": "synthesize", "goal": "Build outline, calibrated findings, and stakeholder-shaped narrative."},
        {"id": "challenge", "goal": "Skeptic/steelman/red-team pass on pivotal claims; verification loop."},
        {"id": "deliver", "goal": "Layered outputs + audit trail + limitations + research agenda."},
    ]
    return {
        "phases": phases,
        "effort_tier": effort,
        "effort_notes": tier["description"],
        "tool_rounds_estimate": tier["tool_rounds"],
        "verification_loop_required": tier["verification_loop"],
        "parallelization": [
            "Independent sub-questions may be searched in parallel.",
            "Source-type packs (gov / academic / news / filings) should be queried in one round.",
            "Persona passes after gather can run conceptually in sequence: analyst → expert → skeptic → decision-maker.",
        ],
        "early_stopping": [
            "Stop gathering a sub-question after 70–80% conceptual coverage or two consecutive low-yield rounds.",
            "Stop verification when pivotal claims have ≥2 independent high/medium-integrity sources or sparsity is explicit.",
        ],
        "replan_triggers": [
            "Major evidence contradicts a planning assumption.",
            "Access failures block a primary-source class.",
            "Contradiction detector flags a pivotal factual dispute.",
            "Coverage analyzer shows a high-priority question at <40% coverage.",
            "User goal shifts (decision vs scholarly vs advocacy).",
        ],
        "todo_milestones": [
            f"Research plan: {q['id']}" for q in questions
        ] + [
            "Horizon scan complete",
            "Evidence store populated",
            "Source scoring + claim matrix",
            "Contradiction + coverage pass",
            "Skeptic / steelman pass",
            "Deliver layered outputs",
        ],
        "scripts_by_phase": {
            "plan": ["research_planner.py", "query_expander.py"],
            "gather": ["evidence_store.py", "citation_normalizer.py"],
            "triangulate": [
                "source_scorer.py",
                "claim_matrix.py",
                "contradiction_detector.py",
                "coverage_analyzer.py",
            ],
            "synthesize": ["synthesis_outliner.py", "confidence_calibrator.py"],
            "challenge": ["contradiction_detector.py", "confidence_calibrator.py"],
            "deliver": ["citation_normalizer.py", "evidence_store.py"],
        },
    }


def load_input(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object")
    return data


def build_plan_payload(args: argparse.Namespace) -> Dict[str, Any]:
    incoming: Dict[str, Any] = {}
    if args.input:
        incoming = load_input(args.input)
    topic = args.topic or incoming.get("topic") or incoming.get("query")
    if not topic:
        raise ValueError("A --topic or input JSON with 'topic'/'query' is required")
    mode = detect_mode(topic, args.mode)
    effort = args.effort or incoming.get("effort") or "medium"
    if effort not in EFFORT_TIERS:
        raise ValueError(f"Unknown effort tier: {effort}")
    geo = args.geo or incoming.get("geo") or "GLOBAL"
    n_q = args.questions or EFFORT_TIERS[effort]["questions"]
    n_h = args.hypotheses or EFFORT_TIERS[effort]["hypotheses"]
    exclude = args.exclude or incoming.get("exclude") or []
    if isinstance(exclude, str):
        exclude = [e.strip() for e in exclude.split(",") if e.strip()]

    reframed = reframe_query(topic, mode)
    questions = build_questions(topic, mode, n_q)
    hypotheses = build_hypotheses(topic, questions, n_h)
    scope = build_scope(mode, effort, geo, args.since, args.until, exclude)
    plan = build_plan(mode, effort, questions)
    premortem = PREMORTEM_BANK[:5] if effort == "light" else PREMORTEM_BANK

    return {
        "skill": "deep-research",
        "artifact": "research_plan",
        "generated_at": utc_now(),
        "id": f"plan-{slugify(topic)}",
        "topic": topic,
        "mode": mode,
        "effort": effort,
        "reframe": reframed,
        "scope": scope,
        "questions": questions,
        "hypotheses": hypotheses,
        "premortem": premortem,
        "personas": PERSONAS,
        "plan": plan,
        "deliverables": [
            "research brief",
            "research plan",
            "evidence log / store",
            "claim-evidence matrix",
            "findings memo",
            "decision brief",
            "annotated bibliography",
            "limitations + research agenda",
        ],
        "quality_bar": {
            "pivotal_claim_sources": "≥2 independent high/medium-integrity or 1 primary",
            "date_stamp": True,
            "steelman_required": effort != "light",
            "confidence_bands": True,
        },
        "resume": {
            "evidence_store": incoming.get("evidence_store") or "research-store.jsonl",
            "prior_plan_id": incoming.get("id"),
        },
    }


def format_text(payload: Dict[str, Any]) -> str:
    lines = [
        "=" * 72,
        "DEEP RESEARCH PLAN",
        "=" * 72,
        f"Generated: {payload['generated_at']}",
        f"ID:        {payload['id']}",
        f"Mode:      {payload['mode']}    Effort: {payload['effort']}",
        "",
        "TOPIC",
        f"  {payload['topic']}",
        "",
        "REFRAMED QUERY",
        f"  {payload['reframe']['reframed']}",
    ]
    if payload["reframe"]["assumptions"]:
        lines.append("ASSUMPTIONS / FLAGS")
        for a in payload["reframe"]["assumptions"]:
            lines.append(f"  - {a}")
    lines += ["", "SCOPE"]
    geo = payload["scope"]["geographic"]
    lines.append(f"  Geo: {geo['code']} — {geo['note']}")
    lines.append(f"  Time: {payload['scope']['temporal']['since']} → {payload['scope']['temporal']['until']}")
    lines.append("  Exclusions:")
    for ex in payload["scope"]["exclusion_criteria"][:6]:
        lines.append(f"    - {ex}")
    lines += ["", "RESEARCH QUESTIONS"]
    for q in payload["questions"]:
        lines.append(f"  [{q['id']}|{q['priority']}] {q['text']}")
    lines += ["", "HYPOTHESES"]
    for h in payload["hypotheses"]:
        lines.append(f"  [{h['id']}|{h['code']}] {h['text']}")
        lines.append(f"      Falsify: {h['falsification_test']}")
    lines += ["", "PRE-MORTEM"]
    for p in payload["premortem"]:
        lines.append(f"  • {p['failure_mode']}")
        lines.append(f"    → {p['mitigation']}")
    lines += ["", "PHASES"]
    for ph in payload["plan"]["phases"]:
        lines.append(f"  {ph['id']:12} {ph['goal']}")
    lines += ["", "REPLAN TRIGGERS"]
    for t in payload["plan"]["replan_triggers"]:
        lines.append(f"  - {t}")
    lines += ["", "PERSONAS"]
    for p in payload["personas"]:
        lines.append(f"  {p['id']:16} ({p['pass']}) {p['role']}")
    lines += ["", "DELIVERABLES"]
    for d in payload["deliverables"]:
        lines.append(f"  - {d}")
    lines += ["", "=" * 72]
    return "\n".join(lines)


def emit(payload: Dict[str, Any], fmt: str, output: Optional[str]) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False) if fmt == "json" else format_text(payload)
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(text)
            if not text.endswith("\n"):
                fh.write("\n")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decompose a research topic into a structured, falsifiable research plan.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python research_planner.py --topic "Do four-day weeks improve software delivery?"
  python research_planner.py --topic "s351 FW Act adverse action" --mode legal --geo AU --effort deep
  python research_planner.py --input brief.json --format json -o plan.json
""",
    )
    parser.add_argument("--topic", "-t", help="Research topic or question")
    parser.add_argument("--input", "-i", help="JSON brief with topic/query and optional constraints")
    parser.add_argument(
        "--mode",
        choices=["auto", "general", "legal", "scientific", "market", "technical", "policy", "historical"],
        default="auto",
        help="Research mode (default: auto-detect)",
    )
    parser.add_argument(
        "--effort",
        choices=["light", "medium", "deep"],
        default="medium",
        help="Effort tier (default: medium)",
    )
    parser.add_argument("--geo", default="GLOBAL", help="Geographic lens: GLOBAL, AU, US, EU, UK, or custom")
    parser.add_argument("--since", help="Temporal lower bound (YYYY or YYYY-MM-DD)")
    parser.add_argument("--until", help="Temporal upper bound")
    parser.add_argument("--questions", type=int, help="Override number of research questions")
    parser.add_argument("--hypotheses", type=int, help="Override number of hypotheses")
    parser.add_argument("--exclude", help="Comma-separated extra exclusion criteria")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--output", "-o", help="Write to file instead of stdout")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        payload = build_plan_payload(args)
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
