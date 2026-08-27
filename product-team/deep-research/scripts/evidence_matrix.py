#!/usr/bin/env python3
"""Build an evidence matrix mapping sources to research questions and claims.

Usage:
    python evidence_matrix.py notes.json --format json
    python evidence_matrix.py notes.json --question q1
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional


WEIGHT = {
    "High": 3.0,
    "Medium-High": 2.5,
    "Medium": 2.0,
    "Medium-Low": 1.0,
    "Low": 0.4,
}


def load_notes(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Notes file must be a JSON object.")
    return data


def source_map(notes: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    sources = notes.get("sources") or []
    indexed = {}
    for src in sources:
        sid = str(src.get("id") or src.get("url") or src.get("title"))
        indexed[sid] = src
        if src.get("url"):
            indexed[str(src["url"])] = src
    return indexed


def cell_weight(src: Optional[Dict[str, Any]], polarity: str) -> float:
    if not src:
        return 0.0
    base = WEIGHT.get(str(src.get("integrity") or "Medium"), 2.0)
    if src.get("average"):
        try:
            base = max(base, float(src["average"]) / 5.0 * 3.0)
        except (TypeError, ValueError):
            pass
    if polarity in {"contradicts", "against", "disconfirm"}:
        return -base
    return base


def build_matrix(notes: Dict[str, Any]) -> Dict[str, Any]:
    questions = notes.get("research_questions") or notes.get("questions") or []
    claims = notes.get("claims") or []
    sources = notes.get("sources") or []
    indexed = source_map(notes)

    q_ids: List[str] = []
    q_text: Dict[str, str] = {}
    for q in questions:
        if isinstance(q, str):
            qid = f"q{len(q_ids) + 1}"
            q_text[qid] = q
            q_ids.append(qid)
        else:
            qid = str(q.get("id") or f"q{len(q_ids) + 1}")
            q_text[qid] = q.get("question") or q.get("text") or qid
            q_ids.append(qid)

    source_ids = [str(s.get("id") or s.get("url") or s.get("title")) for s in sources]

    cells: Dict[str, Dict[str, Dict[str, Any]]] = {qid: {} for qid in q_ids}
    uncovered_questions: List[str] = []
    unused_sources: List[str] = list(source_ids)

    for claim in claims:
        qid = str(claim.get("question_id") or "")
        if qid not in cells:
            if qid:
                cells[qid] = {}
                q_ids.append(qid)
                q_text[qid] = qid
            else:
                continue
        polarity = str(claim.get("polarity") or "supports")
        for sid in claim.get("source_ids") or claim.get("supports") or []:
            sid = str(sid)
            src = indexed.get(sid)
            entry = cells[qid].setdefault(sid, {
                "source_id": sid,
                "integrity": (src or {}).get("integrity"),
                "claims": [],
                "net_weight": 0.0,
            })
            entry["claims"].append({
                "id": claim.get("id"),
                "text": claim.get("claim") or claim.get("text"),
                "polarity": polarity,
            })
            entry["net_weight"] = round(entry["net_weight"] + cell_weight(src, polarity), 2)
            if sid in unused_sources:
                unused_sources.remove(sid)

    question_summaries = []
    for qid in q_ids:
        qcells = cells.get(qid) or {}
        coverage = len(qcells)
        net = round(sum(c["net_weight"] for c in qcells.values()), 2)
        if coverage == 0:
            uncovered_questions.append(qid)
        question_summaries.append({
            "id": qid,
            "question": q_text.get(qid, qid),
            "source_count": coverage,
            "net_weight": net,
            "status": "covered" if coverage >= 2 else ("thin" if coverage == 1 else "gap"),
            "sources": sorted(qcells.values(), key=lambda c: abs(c["net_weight"]), reverse=True),
        })

    return {
        "questions": question_summaries,
        "uncovered_questions": uncovered_questions,
        "unused_sources": unused_sources,
        "source_count": len(source_ids),
        "claim_count": len(claims),
        "coverage_ratio": round(
            (len(q_ids) - len(uncovered_questions)) / len(q_ids), 3
        ) if q_ids else 0.0,
    }


def format_text(matrix: Dict[str, Any], question_filter: Optional[str] = None) -> str:
    lines = [
        "EVIDENCE MATRIX",
        "=" * 72,
        f"Coverage: {matrix['coverage_ratio']:.0%} of questions mapped",
        f"Claims: {matrix['claim_count']}   Sources: {matrix['source_count']}",
        "",
    ]
    for q in matrix["questions"]:
        if question_filter and q["id"] != question_filter:
            continue
        lines.append(f"[{q['status'].upper():7}] {q['id']}  sources={q['source_count']}  net={q['net_weight']:+.2f}")
        lines.append(f"  {q['question']}")
        for cell in q["sources"]:
            nclaims = len(cell["claims"])
            lines.append(
                f"    {cell['source_id']:20}  {cell.get('integrity') or '?':11}  "
                f"w={cell['net_weight']:+.2f}  claims={nclaims}"
            )
        lines.append("")
    if matrix["uncovered_questions"]:
        lines.append("Gaps: " + ", ".join(matrix["uncovered_questions"]))
    if matrix["unused_sources"]:
        lines.append("Unused sources: " + ", ".join(matrix["unused_sources"]))
    return "\n".join(lines).rstrip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a research-question × source evidence matrix."
    )
    parser.add_argument("notes_file", help="JSON research notes (questions, sources, claims)")
    parser.add_argument("--question", help="Filter to a single question id")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        notes = load_notes(args.notes_file)
        matrix = build_matrix(notes)
        if args.question:
            matrix["questions"] = [q for q in matrix["questions"] if q["id"] == args.question]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(matrix, indent=2))
    else:
        print(format_text(matrix, args.question))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
