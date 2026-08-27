#!/usr/bin/env python3
"""Decompose a research query into questions, hypotheses, and evidence needs.

Deterministic heuristics only — no LLM or network calls.

Usage:
    python question_decomposer.py "Does remote work increase engineering productivity?"
    python question_decomposer.py --query "..." --format json
    python question_decomposer.py --input query.json --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Dict, List, Optional


COMPARISON_MARKERS = (
    " vs ", " versus ", " compared to ", " compared with ",
    " better than ", " worse than ", " or ", " versus.",
)
CAUSAL_MARKERS = (
    " cause", " causes", " caused", " because", " lead to", " leads to",
    " impact", " effect", " affect", " result in", " due to", " driven by",
    " increase", " decrease", " reduce", " improve", " worsen",
)
PREDICTIVE_MARKERS = (
    " will ", " forecast", " predict", " future", " outlook", " trend toward",
    " by 20", " next year", " in five years",
)
EVALUATIVE_MARKERS = (
    " should ", " best ", " worst ", " recommend", " worth", " effective",
    " good idea", " bad idea", " is it true",
)
DEFINITIONAL_MARKERS = (
    " what is", " define", " meaning of", " how does", " how do",
)
LEGAL_MARKERS = (
    " legal", " statute", " regulation", " case law", " court", " liability",
    " compliance", " policy", " legislation",
)
QUANT_MARKERS = (
    " how much", " how many", " rate", " percent", " percentage", " statistic",
    " data", " number of", " prevalence", " incidence",
)

STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "being", "that", "this",
    "it", "as", "by", "from", "at", "into", "about", "does", "do", "did",
    "can", "could", "would", "should", "will", "its", "their", "than",
}


def load_query(args: argparse.Namespace) -> str:
    if args.input:
        with open(args.input, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, str):
            return payload.strip()
        return str(payload.get("query") or payload.get("question") or "").strip()
    if args.query:
        return args.query.strip()
    if args.positional:
        return args.positional.strip()
    raise SystemExit("Provide a query string, --query, or --input JSON.")


def classify_query(query: str) -> str:
    lowered = f" {query.lower()} "
    scores = {
        "comparison": sum(1 for m in COMPARISON_MARKERS if m in lowered),
        "causal": sum(1 for m in CAUSAL_MARKERS if m in lowered),
        "predictive": sum(1 for m in PREDICTIVE_MARKERS if m in lowered),
        "evaluative": sum(1 for m in EVALUATIVE_MARKERS if m in lowered),
        "definitional": sum(1 for m in DEFINITIONAL_MARKERS if m in lowered),
        "legal_policy": sum(1 for m in LEGAL_MARKERS if m in lowered),
        "quantitative": sum(1 for m in QUANT_MARKERS if m in lowered),
    }
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        if query.strip().endswith("?"):
            return "descriptive"
        return "exploratory"
    return best


def extract_quoted(query: str) -> List[str]:
    return [m.strip() for m in re.findall(r"[\"“”']([^\"“”']+)[\"“”']", query) if m.strip()]


def extract_entities(query: str) -> List[str]:
    quoted = extract_quoted(query)
    # Capitalized multi-word phrases and acronyms
    phrases = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", query)
    acronyms = re.findall(r"\b([A-Z]{2,})\b", query)
    years = re.findall(r"\b(19|20)\d{2}\b", query)
    entities: List[str] = []
    for item in quoted + phrases + acronyms + years:
        if item not in entities:
            entities.append(item)
    return entities[:12]


def split_clauses(query: str) -> List[str]:
    parts = re.split(r"\s+(?:and also|as well as|;|\band\b)\s+", query, flags=re.I)
    cleaned = [re.sub(r"\s+", " ", p).strip(" ?.") for p in parts if p.strip()]
    return cleaned if len(cleaned) > 1 else [query.strip(" ?.")]


def keywords(query: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", query)
    out: List[str] = []
    for token in tokens:
        low = token.lower()
        if low not in STOPWORDS and low not in out:
            out.append(low)
    return out[:16]


def restatement(query: str, qtype: str) -> str:
    core = re.sub(r"\s+", " ", query).strip().rstrip("?")
    frames = {
        "comparison": f"What does the evidence show when comparing: {core}?",
        "causal": f"What causal relationship, if any, is supported by evidence for: {core}?",
        "predictive": f"What forward-looking evidence and uncertainty bounds apply to: {core}?",
        "evaluative": f"On what criteria and evidence should we evaluate: {core}?",
        "definitional": f"How is the following defined in primary sources, and where do definitions diverge: {core}?",
        "legal_policy": f"What do primary legal/policy sources state regarding: {core}?",
        "quantitative": f"What measured magnitudes, time windows, and populations apply to: {core}?",
        "descriptive": f"What is currently known, as of the research date, about: {core}?",
        "exploratory": f"What is the evidence landscape for: {core}?",
    }
    return frames.get(qtype, frames["exploratory"])


def implicit_assumptions(query: str, qtype: str) -> List[str]:
    assumptions = [
        "The query as stated is the decision-relevant framing (not a loaded proxy question).",
        "Available public sources are sufficient to bound the answer, or gaps will be disclosed.",
    ]
    lowered = query.lower()
    if qtype == "causal":
        assumptions.append("Correlation in cited studies is not treated as causation without design support.")
    if qtype == "evaluative":
        assumptions.append("Evaluation criteria (effectiveness, cost, risk, equity) may be implicit and must be named.")
    if qtype == "comparison":
        assumptions.append("Compared options are sufficiently similar on unstated dimensions (population, time, definition).")
    if any(w in lowered for w in ("always", "never", "everyone", "no one", "proven")):
        assumptions.append("Absolute language in the query overstates what evidence can typically support.")
    if any(w in lowered for w in ("recent", "current", "now", "today")):
        assumptions.append("'Current' is time-boxed to the research as-of date and may shift quickly.")
    if qtype == "legal_policy":
        assumptions.append("Jurisdiction is specified or will be treated as a scope gap if missing.")
    return assumptions


def build_questions(query: str, qtype: str, entities: List[str], clauses: List[str]) -> List[Dict[str, str]]:
    subject = entities[0] if entities else "the focal topic"
    questions: List[Dict[str, str]] = []

    def add(qid: str, text: str, role: str) -> None:
        questions.append({"id": qid, "question": text, "role": role})

    add("q1", f"How is {subject} defined across high-integrity sources, and where do definitions conflict?", "definition")
    add("q2", f"What is the current baseline evidence on: {clauses[0]}?", "descriptive")

    if qtype in {"causal", "quantitative", "evaluative", "exploratory", "descriptive"}:
        add("q3", f"What causal or correlational evidence exists, including study designs and effect sizes, for {subject}?", "causal")
    if qtype in {"comparison", "evaluative"}:
        add("q3", f"On which dimensions do the compared options differ, and what is the evidential weight on each?", "comparison")
    if qtype == "predictive":
        add("q3", "What leading indicators, base rates, and scenario bounds inform the forecast?", "predictive")
    if qtype == "legal_policy":
        add("q3", "What do primary statutes, regulations, and controlling decisions actually say versus commentary?", "legal")

    add("q4", "Which findings replicate or converge across independent sources, and which rest on a single lineage?", "corroboration")
    add("q5", "What are the strongest disconfirming findings or alternative explanations?", "disconfirming")
    add("q6", "Who are the stakeholders, and how do incentives shape the available evidence?", "stakeholders")
    add("q7", "What is the recency profile: what changed in the last 24 months versus foundational older work?", "temporal")
    add("q8", "Where are the coverage gaps (population, geography, method, data access) that bound confidence?", "gaps")

    # Extra clause-specific questions
    for idx, clause in enumerate(clauses[1:3], start=9):
        add(f"q{idx}", f"What independent evidence addresses this sub-claim: {clause}?", "subclaim")

    return questions[:8]


def build_hypotheses(query: str, qtype: str, questions: List[Dict[str, str]]) -> List[Dict[str, str]]:
    core = query.strip().rstrip("?")
    hypotheses = [
        {
            "id": "h1",
            "statement": f"The leading affirmative reading of the query is supported by ≥2 independent high/medium-integrity sources: {core}.",
            "test": "corroboration",
        },
        {
            "id": "h2",
            "statement": "Apparent consensus is an artifact of shared provenance (same dataset, same funder, or circular citation) rather than independent replication.",
            "test": "independence",
        },
        {
            "id": "h3",
            "statement": "Effect direction or magnitude is sensitive to population, time window, or outcome definition.",
            "test": "heterogeneity",
        },
    ]
    if qtype == "causal":
        hypotheses.append({
            "id": "h4",
            "statement": "Observed association is confounded or reverse-causal; no identified design isolates the claimed mechanism.",
            "test": "identification",
        })
    elif qtype == "predictive":
        hypotheses.append({
            "id": "h4",
            "statement": "Historical base rates outperform narrative forecasts once uncertainty is quantified.",
            "test": "base_rate",
        })
    else:
        hypotheses.append({
            "id": "h4",
            "statement": "A credible minority position exists that is under-weighted because it is less amplified, not because it is weaker.",
            "test": "selection_bias",
        })
    hypotheses.append({
        "id": "h5",
        "statement": f"Key open question remains unresolved: {questions[-1]['question']}",
        "test": "gap",
    })
    return hypotheses


def evidence_types(qtype: str) -> List[str]:
    base = [
        "primary documents (statutes, filings, datasets, papers)",
        "high-quality secondary syntheses (systematic reviews, official statistics)",
        "independent corroboration from a second institutional lineage",
    ]
    extra = {
        "causal": ["experimental or quasi-experimental studies", "pre-registration / open data where available"],
        "quantitative": ["raw or reconstructed statistics with methods notes", "time series with vintage dates"],
        "legal_policy": ["black-letter text", "enforcement / tribunal practice", "guidance vs binding authority"],
        "comparison": ["like-for-like metric definitions", "pricing or feature primary pages"],
        "predictive": ["base rates", "leading indicators", "explicit scenario assumptions"],
        "evaluative": ["named criteria and trade-off evidence", "cost, risk, and equity impacts"],
        "definitional": ["glossary / statutory definitions", "boundary cases"],
    }
    return base + extra.get(qtype, ["expert consensus statements with dissent noted"])


def decompose(query: str) -> Dict[str, Any]:
    qtype = classify_query(query)
    entities = extract_entities(query)
    clauses = split_clauses(query)
    questions = build_questions(query, qtype, entities, clauses)
    payload = {
        "query": query,
        "restated": restatement(query, qtype),
        "query_type": qtype,
        "entities": entities,
        "keywords": keywords(query),
        "clauses": clauses,
        "implicit_assumptions": implicit_assumptions(query, qtype),
        "research_questions": questions,
        "hypotheses": build_hypotheses(query, qtype, questions),
        "evidence_types_needed": evidence_types(qtype),
        "falsifiability_note": (
            "Prefer questions that a primary source could confirm or refute. "
            "If a question cannot be operationalized, treat it as a values dispute."
        ),
    }
    return payload


def format_text(payload: Dict[str, Any]) -> str:
    lines = [
        "RESEARCH QUESTION DECOMPOSITION",
        "=" * 72,
        f"Query type: {payload['query_type']}",
        f"Original:   {payload['query']}",
        f"Restated:   {payload['restated']}",
        "",
        "Entities: " + (", ".join(payload["entities"]) or "(none extracted)"),
        "Keywords: " + ", ".join(payload["keywords"]),
        "",
        "Implicit assumptions",
    ]
    for item in payload["implicit_assumptions"]:
        lines.append(f"  - {item}")
    lines.append("")
    lines.append("Research questions")
    for q in payload["research_questions"]:
        lines.append(f"  [{q['id']}/{q['role']}] {q['question']}")
    lines.append("")
    lines.append("Testable hypotheses")
    for h in payload["hypotheses"]:
        lines.append(f"  [{h['id']}/{h['test']}] {h['statement']}")
    lines.append("")
    lines.append("Evidence types needed")
    for item in payload["evidence_types_needed"]:
        lines.append(f"  - {item}")
    lines.append("")
    lines.append(payload["falsifiability_note"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decompose a research query into questions, hypotheses, and evidence needs."
    )
    parser.add_argument("positional", nargs="?", help="Research query text")
    parser.add_argument("--query", help="Research query text (alternative to positional)")
    parser.add_argument("--input", help="JSON file with a 'query' field")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        query = load_query(args)
        if not query:
            parser.error("Query is empty.")
        payload = decompose(query)
    except OSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(format_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
