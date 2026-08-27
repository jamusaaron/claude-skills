#!/usr/bin/env python3
"""Assemble a decision-grade research report from a ledger and findings files.

Fills the output-contract sections. Does not invent claims: missing ledger
fields become explicit gaps. Offline.

Usage:
    python report_assembler.py --ledger ledger.json
    python report_assembler.py --ledger ledger.json --findings findings.md --brief brief.md --format markdown
    python report_assembler.py --ledger ledger.json --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("ledger must be a JSON object")
    return data


def read_optional(path: Optional[str]) -> str:
    if not path:
        return ""
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def claims(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(data.get("claims") or [])


def evidence_for(data: Dict[str, Any], claim: Dict[str, Any]) -> List[Dict[str, Any]]:
    ids = set(claim.get("evidence_ids") or [])
    return [e for e in data.get("evidence") or [] if e.get("id") in ids]


def exec_summary(data: Dict[str, Any], as_of: str) -> str:
    cs = claims(data)
    if not cs:
        return (
            f"No claims have been entered in the ledger as of {as_of}. "
            "This briefing is incomplete; do not treat it as research output."
        )
    supported = [c for c in cs if c.get("status") == "supported"]
    contested = [c for c in cs if c.get("status") == "contested"]
    insufficient = [c for c in cs if c.get("status") in ("unverified", "insufficient")]
    top = supported[:3] or cs[:3]
    bullets = "; ".join(c["statement"] for c in top)
    return (
        f"As of {as_of}, the ledger for “{data.get('query', '')}” contains "
        f"{len(cs)} claims ({len(supported)} supported, {len(contested)} contested, "
        f"{len(insufficient)} unverified/insufficient). Headline: {bullets}. "
        "Read the limitations section before acting. Confidence is claim-level, not report-level."
    )


def findings_block(data: Dict[str, Any]) -> List[str]:
    lines = []
    for c in claims(data):
        evs = evidence_for(data, c)
        cites = ", ".join(e.get("id", "?") for e in evs) or "NO EVIDENCE"
        lines.append(
            f"- **{c['id']}** ({c.get('type')}, {c.get('status')}, conf={c.get('confidence', 'unscored')}): "
            f"{c['statement']} [{cites}]"
        )
    if not lines:
        lines.append("- No findings: ledger has zero claims.")
    return lines


def limitations(data: Dict[str, Any]) -> List[str]:
    items = [
        "This assembler does not fetch sources; citation integrity still needs citation_integrity.py.",
        "Statuses are mechanical (support vs contradict counts), not a substitute for source criticism.",
    ]
    cs = claims(data)
    if any(c.get("status") in ("unverified", "insufficient") for c in cs):
        items.append("One or more claims remain unverified or insufficiently sourced.")
    if any(c.get("status") == "contested" for c in cs):
        items.append("Contested claims are unresolved; do not flatten them into a single narrative.")
    if not data.get("sources"):
        items.append("Source appendix is empty.")
    return items


def actionables(data: Dict[str, Any]) -> List[str]:
    acts = []
    for c in claims(data):
        if c.get("status") == "supported":
            acts.append(f"Treat {c['id']} as usable for decision support, with the cited evidence in view.")
        elif c.get("status") == "contested":
            acts.append(f"Do not decide on {c['id']} until the factual/interpretive/value split is classified.")
        else:
            acts.append(f"Do not act on {c['id']} until corroboration meets the tier rule.")
    if not acts:
        acts.append("Populate the ledger before generating action items.")
    acts.append("Record as-of date; re-run if a primary source newer than the ledger appears.")
    return acts


def source_table(data: Dict[str, Any]) -> List[str]:
    rows = [
        "| ID | Type | Band | Date | Title | URL |",
        "|----|------|------|------|-------|-----|",
    ]
    sources = data.get("sources") or []
    if not sources:
        rows.append("| — | — | — | — | (none) | — |")
        return rows
    for s in sources:
        title = (s.get("title") or "").replace("|", "\\|")
        rows.append(
            f"| {s.get('id')} | {s.get('type', '')} | {s.get('integrity_band', '')} | "
            f"{s.get('date', '')} | {title} | {s.get('url', '')} |"
        )
    return rows


def assemble(data: Dict[str, Any], findings_md: str, brief_md: str, as_of: str) -> Dict[str, Any]:
    report = {
        "title": f"Deep research report: {data.get('query', '(untitled)')}",
        "as_of": as_of,
        "query": data.get("query", ""),
        "executive_briefing": exec_summary(data, as_of),
        "intake_brief": brief_md,
        "key_findings": findings_block(data),
        "findings_memo": findings_md,
        "limitations": limitations(data),
        "actionables": actionables(data),
        "claim_count": len(claims(data)),
        "evidence_count": len(data.get("evidence") or []),
        "source_count": len(data.get("sources") or []),
        "sources": data.get("sources") or [],
        "claims": claims(data),
    }
    return report


def render_markdown(report: Dict[str, Any], data: Dict[str, Any]) -> str:
    parts = [
        f"# {report['title']}",
        "",
        f"**As of:** {report['as_of']}",
        f"**Query:** {report['query']}",
        "",
        "## 1. Executive briefing",
        "",
        report["executive_briefing"],
        "",
        "## 2. Key findings",
        "",
        *report["key_findings"],
        "",
        "## 3. Detailed findings",
        "",
        report["findings_memo"] or "_No findings memo supplied. Do not pad this section with unsourced prose._",
        "",
        "## 4. Limitations and uncertainties",
        "",
    ]
    parts.extend(f"- {item}" for item in report["limitations"])
    parts.extend(["", "## 5. Actionables", ""])
    parts.extend(f"- {item}" for item in report["actionables"])
    parts.extend(["", "## 6. Claim ledger", ""])
    parts.extend([
        "| ID | Type | Status | Confidence | Statement |",
        "|----|------|--------|------------|-----------|",
    ])
    for c in report["claims"]:
        stmt = c.get("statement", "").replace("|", "\\|")
        parts.append(
            f"| {c.get('id')} | {c.get('type')} | {c.get('status')} | {c.get('confidence')} | {stmt} |"
        )
    if not report["claims"]:
        parts.append("| — | — | — | — | (empty) |")
    parts.extend(["", "## 7. Source appendix", ""])
    parts.extend(source_table(data))
    if report["intake_brief"]:
        parts.extend(["", "## Appendix A. Intake brief", "", report["intake_brief"]])
    parts.extend([
        "",
        "---",
        "Generated by `scripts/report_assembler.py`. Run `citation_integrity.py` and `bias_audit.py` before delivery.",
        "",
    ])
    return "\n".join(parts)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble a deep-research report from a claim ledger.")
    parser.add_argument("--ledger", required=True, help="Path to claim ledger JSON")
    parser.add_argument("--findings", help="Optional findings markdown")
    parser.add_argument("--brief", help="Optional intake brief markdown")
    parser.add_argument("--as-of", dest="as_of", help="YYYY-MM-DD (default: today UTC)")
    parser.add_argument("--out", help="Write markdown to this path")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--json", action="store_true", help="Alias for --format json")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        data = load_json(args.ledger)
        findings = read_optional(args.findings)
        brief = read_optional(args.brief)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    as_of = args.as_of or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = assemble(data, findings, brief, as_of)
    as_json = args.json or args.format == "json"
    if as_json:
        text = json.dumps(report, indent=2, ensure_ascii=False)
    else:
        text = render_markdown(report, data)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
            if not text.endswith("\n"):
                handle.write("\n")
        print(args.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
