#!/usr/bin/env python3
"""Package research notes into brief, memo, bibliography, or layered report.

Usage:
    python output_packager.py notes.json --kind brief
    python output_packager.py notes.json --kind memo --format json
    python output_packager.py notes.json --kind bibliography --format markdown
    python output_packager.py notes.json --kind layered --as-of 2026-08-27
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from typing import Any, Dict, List, Optional


KINDS = ("brief", "memo", "bibliography", "layered")


def parse_as_of(value: Optional[str], notes: Dict[str, Any]) -> str:
    if value:
        return value
    if notes.get("as_of"):
        return str(notes["as_of"])[:10]
    return date.today().isoformat()


def load_notes(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Expected a research notes object.")
    return data


def sources(notes: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(notes.get("sources") or [])


def claims(notes: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(notes.get("claims") or [])


def findings(notes: Dict[str, Any]) -> List[Dict[str, Any]]:
    if notes.get("findings"):
        return list(notes["findings"])
    out = []
    for claim in claims(notes):
        out.append({
            "id": claim.get("id"),
            "text": claim.get("claim") or claim.get("text"),
            "confidence": claim.get("confidence") or claim.get("integrity") or "unspecified",
            "question_id": claim.get("question_id"),
            "source_ids": claim.get("source_ids") or claim.get("supports") or [],
        })
    return out


def query_of(notes: Dict[str, Any]) -> str:
    return str(notes.get("query") or notes.get("title") or "Untitled research")


def cite(src: Dict[str, Any]) -> str:
    parts = [
        src.get("author") or src.get("organization") or "",
        src.get("title") or src.get("id") or "Untitled",
        f"({src.get('date') or 'n.d.'})" if src.get("date") or True else "",
    ]
    title = src.get("title") or src.get("id") or "Untitled"
    author = src.get("author") or src.get("organization") or "Unknown"
    year = (str(src.get("date") or "n.d."))[:4]
    url = src.get("url") or ""
    integrity = src.get("integrity") or ""
    extra = f" [{integrity}]" if integrity else ""
    if url:
        return f"{author} ({year}). {title}.{extra} {url}"
    return f"{author} ({year}). {title}.{extra}"


def build_brief(notes: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    top = findings(notes)[:5]
    return {
        "kind": "brief",
        "as_of": as_of,
        "title": f"Research brief: {query_of(notes)}",
        "query": query_of(notes),
        "bottom_line": notes.get("bottom_line") or notes.get("executive_summary") or (
            top[0]["text"] if top else "No findings recorded in notes."
        ),
        "key_findings": top,
        "confidence": notes.get("overall_confidence") or "unspecified",
        "limitations": notes.get("limitations") or [
            "Findings reflect sources in the notes file only.",
            f"Evidence assessment as of {as_of}.",
        ],
        "recommended_actions": notes.get("recommended_actions") or [],
    }


def build_memo(notes: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    brief = build_brief(notes, as_of)
    return {
        "kind": "memo",
        "as_of": as_of,
        "title": f"Synthesis memo: {query_of(notes)}",
        "query": query_of(notes),
        "bottom_line": brief["bottom_line"],
        "analysis": notes.get("analysis") or [
            f.get("text") for f in findings(notes)
        ],
        "disagreements": notes.get("disagreements") or [],
        "stakeholders": notes.get("stakeholders") or [],
        "key_findings": brief["key_findings"],
        "limitations": brief["limitations"],
        "open_questions": [
            q.get("question") if isinstance(q, dict) else q
            for q in (notes.get("research_questions") or [])
        ],
        "recommended_actions": brief["recommended_actions"],
    }


def build_bibliography(notes: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    rows = []
    for src in sources(notes):
        rows.append({
            "id": src.get("id"),
            "citation": cite(src),
            "type": src.get("type") or src.get("host_class"),
            "integrity": src.get("integrity"),
            "date": src.get("date"),
            "url": src.get("url"),
            "contribution": src.get("contribution") or src.get("notes") or "",
            "limitations": src.get("limitations") or "",
        })
    rows.sort(key=lambda r: (str(r.get("integrity") or "Z"), str(r.get("id") or "")))
    return {
        "kind": "bibliography",
        "as_of": as_of,
        "title": f"Annotated bibliography: {query_of(notes)}",
        "entries": rows,
        "count": len(rows),
    }


def build_layered(notes: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    brief = build_brief(notes, as_of)
    biblio = build_bibliography(notes, as_of)
    return {
        "kind": "layered",
        "as_of": as_of,
        "title": f"Deep research report: {query_of(notes)}",
        "layer1_executive_summary": {
            "bottom_line": brief["bottom_line"],
            "confidence": brief["confidence"],
            "implications": brief["recommended_actions"][:5],
            "scope_note": f"Evidence assessment as of {as_of}. Public data may have shifted since.",
        },
        "layer2_key_findings": brief["key_findings"],
        "layer3_analysis": notes.get("analysis") or [f["text"] for f in findings(notes)],
        "layer4_bibliography": biblio["entries"],
        "layer5_limitations": brief["limitations"],
        "layer6_decision_framework": notes.get("decision_framework") or notes.get("scenarios") or [],
        "quality_gates": notes.get("quality_gates") or {
            "pivotal_claims_have_two_sources": None,
            "low_integrity_caveated": None,
            "uncertainties_disclosed": True,
        },
    }


BUILDERS = {
    "brief": build_brief,
    "memo": build_memo,
    "bibliography": build_bibliography,
    "layered": build_layered,
}


def to_markdown(payload: Dict[str, Any]) -> str:
    kind = payload["kind"]
    lines = [f"# {payload['title']}", "", f"*As of {payload['as_of']}*", ""]
    if kind == "brief":
        lines += [
            "## Bottom line",
            payload["bottom_line"],
            "",
            f"**Confidence:** {payload['confidence']}",
            "",
            "## Key findings",
        ]
        for finding in payload["key_findings"]:
            srcs = ", ".join(map(str, finding.get("source_ids") or [])) or "n/a"
            lines.append(
                f"- {finding.get('text')} *(confidence: {finding.get('confidence')}; sources: {srcs})*"
            )
        lines += ["", "## Limitations"]
        for item in payload["limitations"]:
            lines.append(f"- {item}")
        if payload["recommended_actions"]:
            lines += ["", "## Actions"]
            for item in payload["recommended_actions"]:
                lines.append(f"- {item}")
    elif kind == "memo":
        lines += ["## Bottom line", payload["bottom_line"], "", "## Analysis"]
        for para in payload["analysis"]:
            lines.append(f"- {para}")
        if payload["disagreements"]:
            lines += ["", "## Disagreements"]
            for item in payload["disagreements"]:
                lines.append(f"- {item}")
        lines += ["", "## Open questions"]
        for item in payload["open_questions"]:
            lines.append(f"- {item}")
        lines += ["", "## Limitations"]
        for item in payload["limitations"]:
            lines.append(f"- {item}")
    elif kind == "bibliography":
        lines.append(f"{payload['count']} sources")
        lines.append("")
        lines.append("| ID | Integrity | Citation | Contribution |")
        lines.append("|----|-----------|----------|--------------|")
        for row in payload["entries"]:
            contrib = (row.get("contribution") or "").replace("|", "/")
            lines.append(
                f"| {row.get('id')} | {row.get('integrity') or ''} | {row['citation']} | {contrib} |"
            )
    else:
        layer1 = payload["layer1_executive_summary"]
        lines += [
            "## Layer 1 — Executive summary",
            layer1["bottom_line"],
            "",
            f"**Confidence:** {layer1['confidence']}",
            f"*{layer1['scope_note']}*",
            "",
            "## Layer 2 — Key findings",
        ]
        for finding in payload["layer2_key_findings"]:
            lines.append(f"- {finding.get('text')}")
        lines += ["", "## Layer 3 — Analysis"]
        for para in payload["layer3_analysis"]:
            lines.append(f"- {para}")
        lines += ["", "## Layer 4 — Annotated bibliography"]
        for row in payload["layer4_bibliography"]:
            lines.append(f"- {row['citation']}")
        lines += ["", "## Layer 5 — Limitations"]
        for item in payload["layer5_limitations"]:
            lines.append(f"- {item}")
        if payload["layer6_decision_framework"]:
            lines += ["", "## Layer 6 — Decision framework"]
            for item in payload["layer6_decision_framework"]:
                lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def format_text(payload: Dict[str, Any]) -> str:
    # Human-readable is markdown-like without requiring a markdown renderer
    return to_markdown(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Package research notes into brief, memo, bibliography, or layered report."
    )
    parser.add_argument("notes_file", help="JSON research notes / findings package")
    parser.add_argument(
        "--kind",
        choices=KINDS,
        default="brief",
        help="Output artifact kind (default: brief)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        help="text and markdown are equivalent structured prose; json is machine-readable",
    )
    parser.add_argument("--as-of", dest="as_of", help="As-of date YYYY-MM-DD")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        notes = load_notes(args.notes_file)
        as_of = parse_as_of(args.as_of, notes)
        payload = BUILDERS[args.kind](notes, as_of)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        text = format_text(payload)
        if not text.endswith("\n"):
            text += "\n"
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
