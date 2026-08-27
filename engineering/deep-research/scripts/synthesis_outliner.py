#!/usr/bin/env python3
"""Synthesis outline builder.

Produces a layered research outline (executive summary, findings, analysis,
appendix, limitations) tailored to a stakeholder and effort tier. Can ingest a
plan, claim matrix, and coverage report.

Usage:
    python synthesis_outliner.py --topic "Hybrid work and delivery" --audience executive
    python synthesis_outliner.py --plan plan.json --matrix matrix.json --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


AUDIENCES = {
    "executive": {
        "label": "Decision-maker / executive",
        "layers": ["exec", "findings", "decision", "limitations"],
        "tone": "Short, decision-first, residual risk explicit.",
        "max_findings": 5,
    },
    "policy": {
        "label": "Policy / legal",
        "layers": ["exec", "findings", "legal_map", "analysis", "limitations", "appendix"],
        "tone": "Distinguish black-letter rule, practice, and advocacy.",
        "max_findings": 8,
    },
    "academic": {
        "label": "Scholarly / technical",
        "layers": ["exec", "findings", "methods", "analysis", "challenge", "limitations", "appendix"],
        "tone": "Methods, uncertainty, and research agenda first-class.",
        "max_findings": 10,
    },
    "product": {
        "label": "Product / GTM",
        "layers": ["exec", "findings", "implications", "decision", "limitations"],
        "tone": "What to ship, stop, or watch; evidence for positioning claims.",
        "max_findings": 6,
    },
    "investigative": {
        "label": "Investigative / full audit",
        "layers": ["exec", "findings", "analysis", "challenge", "stakeholder", "limitations", "appendix", "log"],
        "tone": "Full provenance; steelman; no buried disagreements.",
        "max_findings": 12,
    },
}

LAYER_COPY = {
    "exec": {
        "title": "Layer 1 — Executive summary (150–300 words)",
        "slots": [
            "Core answer in one paragraph, dated as-of.",
            "Confidence band + top 2 drivers of uncertainty.",
            "Top 3–5 implications or recommendations.",
            "One-sentence scope/limitation note.",
        ],
    },
    "findings": {
        "title": "Layer 2 — Key findings (claim + citation + confidence)",
        "slots": [
            "One bullet per finding: claim, inline citation, source note, confidence tag, 1–2 sentence rationale.",
            "Group by research question.",
            "Mark contested findings explicitly; do not smooth them.",
        ],
    },
    "analysis": {
        "title": "Layer 3 — Detailed analysis",
        "slots": [
            "Thematic or chronological sections.",
            "Tables for comparisons, timelines, quantitative summaries.",
            "Mechanism discussion: what would have to be true.",
        ],
    },
    "methods": {
        "title": "Methods and source criticism",
        "slots": [
            "Search strategy and packs used.",
            "12-point scoring summary and excluded low-integrity sources.",
            "Verification loop actions and deltas.",
        ],
    },
    "challenge": {
        "title": "Challenge pass — steelman, red team, pre-mortem",
        "slots": [
            "Strongest opposing case, evidentially supported.",
            "Where the synthesis could be wrong (pre-mortem).",
            "Shared-provenance risks and remaining contradictions.",
        ],
    },
    "legal_map": {
        "title": "Legal / policy map",
        "slots": [
            "Black-letter rule vs enforcement practice vs guidance.",
            "Onus, standing, time limits, jurisdiction.",
            "What facts, if proven, change the outcome.",
        ],
    },
    "implications": {
        "title": "Implications for product / GTM",
        "slots": [
            "Claims safe to make in public.",
            "Claims to stop making.",
            "Watch items and leading indicators.",
        ],
    },
    "decision": {
        "title": "Decision frame",
        "slots": [
            "Options considered.",
            "Recommended option and the evidence that would reverse it.",
            "No-regret moves vs bets that need more evidence.",
        ],
    },
    "stakeholder": {
        "title": "Stakeholder power–interest map",
        "slots": [
            "Who benefits, who bears costs, who controls information.",
            "Incentive-driven distortions in the evidence base.",
        ],
    },
    "limitations": {
        "title": "Layer 5 — Limitations, uncertainties, research agenda",
        "slots": [
            "Inventory of gaps and volatile areas.",
            "Alternative interpretations still standing.",
            "Specific follow-up queries and data sources.",
        ],
    },
    "appendix": {
        "title": "Layer 4 — Evidence appendix / annotated bibliography",
        "slots": [
            "Source | type | credibility | key contribution | limitations | relevance.",
            "Every non-obvious claim must be traceable here.",
        ],
    },
    "log": {
        "title": "Research process audit log (optional)",
        "slots": [
            "Phases, iterations, replan events, tool failures, confidence evolution.",
            "1–3 meta-improvements to the method.",
        ],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Optional[str]) -> Any:
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.loads(fh.read())


def questions_from(plan: Any) -> List[Dict[str, Any]]:
    if not isinstance(plan, dict):
        return []
    out = []
    for q in plan.get("questions") or []:
        if isinstance(q, dict):
            out.append({"id": q.get("id"), "text": q.get("text"), "priority": q.get("priority")})
        else:
            out.append({"id": str(q), "text": str(q), "priority": "supporting"})
    return out


def findings_from_matrix(matrix: Any, limit: int) -> List[Dict[str, Any]]:
    if not isinstance(matrix, dict):
        return []
    rows = matrix.get("matrix") or matrix.get("rows") or []
    findings = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        findings.append({
            "id": row.get("id"),
            "text": row.get("text"),
            "status": row.get("status"),
            "net_weight": row.get("net_weight"),
            "question_ids": row.get("question_ids") or [],
            "outline_hint": (
                "Lead with this — well supported."
                if row.get("status") == "supported"
                else "Present as contested; do not pick a winner in the exec summary."
                if row.get("status") == "contested"
                else "Park in limitations until verification loop."
            ),
        })
        if len(findings) >= limit:
            break
    return findings


def coverage_flags(coverage: Any) -> List[str]:
    if not isinstance(coverage, dict):
        return []
    flags = []
    for g in coverage.get("gaps") or []:
        flags.append(f"{g.get('question_id')}: {g.get('why')}")
    for r in coverage.get("recommendations") or []:
        flags.append(str(r))
    return flags[:12]


def build_outline(
    topic: str,
    audience: str,
    effort: str,
    plan: Any,
    matrix: Any,
    coverage: Any,
) -> Dict[str, Any]:
    profile = AUDIENCES[audience]
    questions = questions_from(plan)
    findings = findings_from_matrix(matrix, profile["max_findings"])
    layers = []
    for key in profile["layers"]:
        spec = LAYER_COPY[key]
        section: Dict[str, Any] = {
            "id": key,
            "title": spec["title"],
            "slots": list(spec["slots"]),
        }
        if key == "findings":
            if questions:
                section["group_by_questions"] = questions
            if findings:
                section["seed_findings"] = findings
            else:
                section["slots"].append("No claim matrix provided — populate after triangulate phase.")
        if key == "limitations":
            flags = coverage_flags(coverage)
            if flags:
                section["known_gaps"] = flags
        if key == "challenge" and effort == "light":
            section["slots"] = ["Minimum: one steelman paragraph for the main opposing view."]
        layers.append(section)

    return {
        "skill": "deep-research",
        "artifact": "synthesis_outline",
        "generated_at": utc_now(),
        "topic": topic or (plan or {}).get("topic") if isinstance(plan, dict) else topic,
        "audience": audience,
        "audience_label": profile["label"],
        "tone": profile["tone"],
        "effort": effort,
        "quality_gates": [
            "Every non-obvious high-stakes claim has ≥2 independent high/medium-integrity sources or 1 primary.",
            "Low-integrity sources used only illustratively, with explicit framing.",
            "Opposing evidence is steelmanned, not minimized.",
            "Findings dated as-of; rapidly evolving topics carry a monitor note.",
            "Uncertainty bands appear on every key finding.",
            "Decision-relevant residual risk is explicit if audience is executive/product.",
        ],
        "suggested_order": [l["id"] for l in layers],
        "layers": layers,
        "persona_passes_before_delivery": [
            "analyst: completeness of claim mapping",
            "domain_expert: methods and missing canonical sources",
            "skeptic: contradictions, shared provenance, overclaiming",
            "decision_maker: so-what, reverse-the-call evidence",
        ],
        "anti_patterns": [
            "Leading with a narrative and hunting citations afterwards.",
            "False balance on a lopsided evidence base.",
            "Burying contested findings in an appendix.",
            "Omitting the as-of date on volatile topics.",
        ],
    }


def format_text(payload: Dict[str, Any]) -> str:
    lines = [
        "=" * 72,
        "SYNTHESIS OUTLINE",
        "=" * 72,
        f"Topic:    {payload.get('topic')}",
        f"Audience: {payload['audience_label']} ({payload['audience']})",
        f"Effort:   {payload['effort']}",
        f"Tone:     {payload['tone']}",
        "",
    ]
    for layer in payload["layers"]:
        lines.append(layer["title"])
        for slot in layer["slots"]:
            lines.append(f"  • {slot}")
        for f in layer.get("seed_findings") or []:
            lines.append(f"    - [{f.get('status')}] {f.get('text')}")
        for g in layer.get("known_gaps") or []:
            lines.append(f"    GAP: {g}")
        lines.append("")
    lines.append("QUALITY GATES")
    for g in payload["quality_gates"]:
        lines.append(f"  - {g}")
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
        description="Build a stakeholder-specific layered research outline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python synthesis_outliner.py --topic "Four-day week productivity" --audience executive
  python synthesis_outliner.py --plan plan.json --matrix matrix.json --coverage cov.json --format json
""",
    )
    parser.add_argument("--topic", "-t", help="Research topic (optional if --plan provided)")
    parser.add_argument("--plan", help="research_planner.py JSON")
    parser.add_argument("--matrix", help="claim_matrix.py JSON")
    parser.add_argument("--coverage", help="coverage_analyzer.py JSON")
    parser.add_argument(
        "--audience",
        choices=sorted(AUDIENCES),
        default="investigative",
        help="Stakeholder lens (default: investigative)",
    )
    parser.add_argument("--effort", choices=["light", "medium", "deep"], default="medium")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", "-o")
    args = parser.parse_args(argv)
    try:
        plan = load_json(args.plan)
        matrix = load_json(args.matrix)
        coverage = load_json(args.coverage)
        topic = args.topic or (plan or {}).get("topic")
        if not topic:
            raise ValueError("Provide --topic or a --plan JSON that includes topic")
        payload = build_outline(topic, args.audience, args.effort, plan, matrix, coverage)
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
