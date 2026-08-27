#!/usr/bin/env python3
"""Synthesis Outline Builder — Generate layered research output structure.

Builds executive summary scaffold, key findings outline, detailed analysis
sections, evidence appendix structure, and limitations from a research plan.

Usage:
    python3 synthesis_outline_builder.py plan.json --format text
    python3 synthesis_outline_builder.py --query "Topic" --depth deep --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any


CONFIDENCE_BANDS = {
    "Very High": ">90% — Multiple convergent high-integrity sources, replicated or primary data",
    "High": "70-90% — Strong evidence with minor gaps or single high-quality primary source",
    "Medium": "50-70% — Adequate evidence with notable uncertainties or interpretive disputes",
    "Low": "<50% — Limited, conflicting, or low-integrity evidence; treat as provisional",
}


def build_outline(plan: dict[str, Any], findings: list[dict] | None = None) -> dict[str, Any]:
    query = plan.get("query", plan.get("topic", "Research Topic"))
    depth = plan.get("depth", "medium")
    sub_questions = plan.get("sub_questions", [])
    hypotheses = plan.get("hypotheses", [])

    layer1 = {
        "title": "Executive Summary",
        "word_target": "150-300",
        "sections": [
            {"name": "Core Answer", "prompt": f"In 2-3 sentences, state the evidence-backed answer to: {query}"},
            {"name": "Overall Confidence", "prompt": "State overall confidence band with primary drivers"},
            {"name": "Top Implications", "prompt": "List 3-5 actionable implications for the user"},
            {"name": "Scope Note", "prompt": "One sentence on temporal scope and key limitation"},
        ],
    }

    layer2_bullets = []
    for sq in sub_questions:
        layer2_bullets.append({
            "sub_question_id": sq.get("id", ""),
            "question": sq.get("question", ""),
            "bullet_template": "[Claim] — [Citation] — Confidence: [Band] — [1-2 sentence rationale]",
            "confidence_band_options": list(CONFIDENCE_BANDS.keys()),
        })

    layer2 = {
        "title": "Key Findings",
        "format": "Bullet hierarchy grouped by research question",
        "findings": layer2_bullets,
    }

    layer3_sections = []
    section_types = ["Background & Context", "Evidence Synthesis", "Contested Claims & Steelman",
                     "Quantitative Summary", "Stakeholder Perspectives", "Temporal Trends"]
    for i, sq in enumerate(sub_questions[:6]):
        section_type = section_types[i % len(section_types)]
        layer3_sections.append({
            "heading": f"{section_type}: {sq.get('type', 'analysis').replace('_', ' ').title()}",
            "sub_question_id": sq.get("id", ""),
            "content_prompts": [
                "Summarize convergent evidence",
                "Note key disagreements with evidential weight",
                "Include table or timeline if applicable",
            ],
        })

    layer3 = {"title": "Detailed Analysis", "sections": layer3_sections}

    layer4 = {
        "title": "Evidence Appendix",
        "columns": ["Source ID", "Title", "Type", "Date", "Credibility", "Key Contribution", "Limitations", "Relevance"],
        "sort_by": "credibility descending, then relevance",
    }

    layer5 = {
        "title": "Limitations, Uncertainties & Future Research",
        "sections": [
            {"name": "Evidence Gaps", "prompt": "List sub-questions with insufficient evidence"},
            {"name": "Volatile Areas", "prompt": "Topics where evidence may change rapidly"},
            {"name": "Alternative Interpretations", "prompt": "Viable alternative readings of the evidence"},
            {"name": "Recommended Follow-Up", "prompt": "Specific searches, data sources, or expert consultations"},
            {"name": "Hypothesis Outcomes", "prompt": _hypothesis_summary(hypotheses, findings)},
        ],
    }

    optional_layer6 = None
    if depth == "deep":
        optional_layer6 = {
            "title": "Decision Framework (Optional Layer 6)",
            "sections": [
                {"name": "Scenario A — Base Case", "prompt": "Most likely outcome based on current evidence"},
                {"name": "Scenario B — Upside", "prompt": "Optimistic scenario with supporting conditions"},
                {"name": "Scenario C — Downside", "prompt": "Pessimistic scenario with supporting conditions"},
                {"name": "Decision Criteria", "prompt": "What evidence would shift recommendation between scenarios"},
            ],
        }

    verification_checklist = [
        "Every pivotal claim has ≥2 independent medium+ sources or 1 primary source",
        "Medium-Low and Low sources carry explicit caveats",
        "Contested claims include steelman of both sides",
        "Confidence bands applied consistently",
        "Findings qualified with 'as of [date]'",
        "Bias audit completed",
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "depth": depth,
        "confidence_bands": CONFIDENCE_BANDS,
        "layers": {
            "layer_1_executive_summary": layer1,
            "layer_2_key_findings": layer2,
            "layer_3_detailed_analysis": layer3,
            "layer_4_evidence_appendix": layer4,
            "layer_5_limitations": layer5,
        },
        "optional_layer_6": optional_layer6,
        "verification_checklist": verification_checklist,
        "writing_guidance": {
            "tone": "Neutral, precise, authoritative without false certainty",
            "citation_rule": "Every non-obvious claim must cite source with credibility note if Medium-Low or below",
            "structure_rule": "Bottom line first in each section; What + Why + How for recommendations",
        },
    }


def _hypothesis_summary(hypotheses: list, findings: list | None) -> str:
    if not hypotheses:
        return "Document which hypotheses were supported, falsified, or remain uncertain"
    parts = []
    for h in hypotheses:
        parts.append(f"[{h.get('id', '?')}] {h.get('statement', '')[:80]}... → [Supported/Falsified/Uncertain]")
    return " | ".join(parts)


def format_text(outline: dict[str, Any]) -> str:
    lines = [
        "=" * 72,
        "SYNTHESIS OUTLINE",
        f"Query: {outline['query']}",
        f"Depth: {outline['depth']} | Generated: {outline['generated_at']}",
        "=" * 72,
    ]

    for key, layer in outline["layers"].items():
        lines.extend(["", f"## {layer['title']}", ""])
        if "word_target" in layer:
            lines.append(f"Target length: {layer['word_target']} words")
        if "sections" in layer:
            for sec in layer["sections"]:
                if isinstance(sec, dict):
                    name = sec.get("name") or sec.get("heading", "")
                    prompt = sec.get("prompt") or sec.get("content_prompts", "")
                    lines.append(f"  ### {name}")
                    if isinstance(prompt, list):
                        for p in prompt:
                            lines.append(f"    - {p}")
                    else:
                        lines.append(f"    {prompt}")
        if "findings" in layer:
            for f in layer["findings"]:
                lines.append(f"  [{f['sub_question_id']}] {f['question'][:70]}...")
                lines.append(f"    Template: {f['bullet_template']}")
        if "columns" in layer:
            lines.append(f"  Columns: {' | '.join(layer['columns'])}")

    if outline.get("optional_layer_6"):
        lines.extend(["", f"## {outline['optional_layer_6']['title']} (Deep only)"])
        for sec in outline["optional_layer_6"]["sections"]:
            lines.append(f"  ### {sec['name']}: {sec['prompt']}")

    lines.extend(["", "## Verification Checklist"])
    for item in outline["verification_checklist"]:
        lines.append(f"  [ ] {item}")

    lines.extend(["", "## Confidence Bands"])
    for band, desc in outline["confidence_bands"].items():
        lines.append(f"  {band}: {desc}")

    lines.append("\n" + "=" * 72)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build layered synthesis output outline")
    parser.add_argument("input", nargs="?", help="Research plan JSON file")
    parser.add_argument("--query", "-q", help="Generate minimal plan from query")
    parser.add_argument("--depth", choices=["light", "medium", "deep"], default="medium")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--output", "-o")

    args = parser.parse_args()

    if args.input:
        with open(args.input, encoding="utf-8") as f:
            plan = json.load(f)
    elif args.query:
        plan = {"query": args.query, "depth": args.depth, "sub_questions": [
            {"id": f"sq{i}", "question": f"Sub-question {i} about {args.query}", "type": "analysis"}
            for i in range(1, 6)
        ], "hypotheses": []}
    else:
        parser.error("Provide input file or --query")

    outline = build_outline(plan)
    output = json.dumps(outline, indent=2) if args.format == "json" else format_text(outline)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Outline written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
