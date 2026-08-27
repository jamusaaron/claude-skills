#!/usr/bin/env python3
"""Contradiction detector across research notes and claims.

Flags numeric conflicts, negation clashes, and antonym/polarity conflicts on
similar claims. Classifies disputes as factual, interpretive, or value-laden
and recommends a verification move.

Usage:
    python contradiction_detector.py --input notes.jsonl
    python contradiction_detector.py --input store.json --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple


NEGATION = re.compile(
    r"\b(?:no|not|never|none|neither|without|n't|cannot|can't|did not|does not|no evidence|failed to|false|incorrect|untrue)\b",
    re.I,
)
ANTONYM_PAIRS = [
    ("increase", "decrease"),
    ("increased", "decreased"),
    ("higher", "lower"),
    ("rise", "fall"),
    ("gain", "loss"),
    ("effective", "ineffective"),
    ("safe", "unsafe"),
    ("support", "oppose"),
    ("positive", "negative"),
    ("improve", "worsen"),
    ("improved", "worsened"),
    ("success", "failure"),
    ("legal", "illegal"),
    ("constitutional", "unconstitutional"),
    ("causal", "spurious"),
    ("significant", "insignificant"),
    ("confirmed", "refuted"),
    ("replicated", "failed to replicate"),
]
VALUE_MARKERS = (
    "should", "must", "ought", "unfair", "unjust", "immoral", "right to",
    "wrong to", "better society", "we need to",
)
INTERPRET_MARKERS = (
    "suggests", "implies", "consistent with", "may indicate", "could mean",
    "interpretation", "framework", "narrative", "because",
)
NUMBER_RE = re.compile(
    r"(?P<num>[-+]?\d+(?:[.,]\d+)?)(?P<unit>\s*(?:%|percent|pp|x|times|ms|s|kg|km|usd|aud|eur|gbp|million|billion|trillion))?",
    re.I,
)
STOP = {
    "the", "a", "an", "of", "to", "and", "in", "on", "for", "is", "that", "with",
    "from", "by", "as", "at", "or", "be", "this", "it", "are", "was", "were",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_notes(path: str) -> List[Dict[str, Any]]:
    raw = open(path, "r", encoding="utf-8").read().strip()
    items: List[Any]
    if path.endswith(".jsonl"):
        items = [json.loads(line) for line in raw.splitlines() if line.strip()]
    else:
        data = json.loads(raw)
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = None
            for key in ("notes", "claims", "evidence", "records", "items", "matrix"):
                if isinstance(data.get(key), list):
                    items = data[key]
                    break
            if items is None:
                items = [data]
        else:
            raise ValueError("Unsupported JSON")
    notes = []
    for i, item in enumerate(items):
        if isinstance(item, str):
            notes.append({"id": f"N{i+1}", "text": item})
            continue
        if not isinstance(item, dict):
            continue
        texts: List[Tuple[str, str]] = []
        if item.get("text") or item.get("claim") or item.get("note"):
            texts.append((item.get("id") or f"N{i+1}", item.get("text") or item.get("claim") or item.get("note")))
        for j, c in enumerate(item.get("claims") or []):
            if isinstance(c, str):
                texts.append((f"{item.get('id', f'E{i+1}')}-c{j+1}", c))
            elif isinstance(c, dict) and (c.get("text") or c.get("claim")):
                texts.append((c.get("id") or f"{item.get('id', f'E{i+1}')}-c{j+1}", c.get("text") or c.get("claim")))
        if not texts and item.get("title"):
            texts.append((item.get("id") or f"N{i+1}", item["title"]))
        for nid, text in texts:
            notes.append({
                "id": nid,
                "text": str(text),
                "source_id": item.get("id") or item.get("source_id"),
                "url": item.get("url"),
                "question_id": item.get("question_id") or (
                    next(
                        (
                            c.get("question_id")
                            for c in (item.get("claims") or [])
                            if isinstance(c, dict) and c.get("question_id")
                        ),
                        None,
                    )
                ),
                "polarity": item.get("polarity"),
            })
    return notes


def tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9%+-]+", text.lower()) if t not in STOP and len(t) > 2}


def overlap(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def numbers(text: str) -> List[Tuple[float, str, str]]:
    found = []
    for m in NUMBER_RE.finditer(text.replace(",", "")):
        try:
            val = float(m.group("num"))
        except ValueError:
            continue
        unit = (m.group("unit") or "").strip().lower()
        found.append((val, unit, m.group(0)))
    return found


def antonym_hit(a: str, b: str) -> Optional[str]:
    la, lb = a.lower(), b.lower()
    for x, y in ANTONYM_PAIRS:
        if (x in la and y in lb) or (y in la and x in lb):
            return f"{x}/{y}"
    return None


def classify_dispute(a: str, b: str, kind: str) -> str:
    blob = f"{a} {b}".lower()
    if any(m in blob for m in VALUE_MARKERS):
        return "value-laden"
    if kind == "numeric":
        return "factual"
    if any(m in blob for m in INTERPRET_MARKERS) and kind != "numeric":
        return "interpretive"
    if kind == "negation" or kind == "antonym":
        return "factual"
    return "interpretive"


def compare_pair(a: Dict[str, Any], b: Dict[str, Any], min_overlap: float) -> Optional[Dict[str, Any]]:
    ta, tb = tokens(a["text"]), tokens(b["text"])
    ov = overlap(ta, tb)
    if ov < min_overlap:
        return None
    kinds = []
    detail = []

    nums_a, nums_b = numbers(a["text"]), numbers(b["text"])
    for va, ua, ra in nums_a:
        for vb, ub, rb in nums_b:
            unit_ok = (not ua and not ub) or ua == ub or (
                ua in {"%", "percent", "pp"} and ub in {"%", "percent", "pp"}
            )
            if not unit_ok:
                continue
            if va == 0 and vb == 0:
                continue
            rel = abs(va - vb) / max(abs(va), abs(vb), 1e-9)
            sign_flip = (va > 0 > vb) or (vb > 0 > va)
            if rel >= 0.15 or sign_flip:
                kinds.append("numeric")
                detail.append(f"numbers {ra} vs {rb} (rel_diff={rel:.2f})")

    na, nb = bool(NEGATION.search(a["text"])), bool(NEGATION.search(b["text"]))
    if na ^ nb and ov >= min_overlap:
        kinds.append("negation")
        detail.append("one claim negated, the other not")

    ant = antonym_hit(a["text"], b["text"])
    if ant:
        kinds.append("antonym")
        detail.append(f"antonym pair {ant}")

    pol_a, pol_b = (a.get("polarity") or "").lower(), (b.get("polarity") or "").lower()
    if pol_a and pol_b and pol_a != pol_b and {pol_a, pol_b} <= {"supports", "refutes", "support", "refute", "contradicts"}:
        kinds.append("polarity")
        detail.append(f"polarity {pol_a} vs {pol_b}")

    if not kinds:
        return None
    kind = kinds[0]
    dispute = classify_dispute(a["text"], b["text"], kind)
    severity = "high" if "numeric" in kinds or "negation" in kinds else "medium"
    if dispute == "value-laden":
        severity = "low"
    next_step = {
        "factual": "Re-acquire primary data or original document; treat as a verification-loop target.",
        "interpretive": "Present both frameworks with evidential weight; do not collapse into a false single answer.",
        "value-laden": "Map underlying values/assumptions; keep them out of the empirical claim set.",
    }[dispute]
    return {
        "left_id": a["id"],
        "right_id": b["id"],
        "left_text": a["text"],
        "right_text": b["text"],
        "left_source": a.get("source_id") or a.get("url"),
        "right_source": b.get("source_id") or b.get("url"),
        "overlap": round(ov, 3),
        "kinds": sorted(set(kinds)),
        "detail": detail,
        "dispute_class": dispute,
        "severity": severity,
        "next_step": next_step,
    }


def detect(notes: List[Dict[str, Any]], min_overlap: float) -> Dict[str, Any]:
    conflicts = []
    for left, right in combinations(notes, 2):
        if left.get("source_id") and left.get("source_id") == right.get("source_id"):
            continue
        hit = compare_pair(left, right, min_overlap)
        if hit:
            conflicts.append(hit)
    conflicts.sort(key=lambda c: ({"high": 0, "medium": 1, "low": 2}[c["severity"]], -c["overlap"]))
    by_class = {}
    for c in conflicts:
        by_class[c["dispute_class"]] = by_class.get(c["dispute_class"], 0) + 1
    return {
        "skill": "deep-research",
        "artifact": "contradiction_report",
        "generated_at": utc_now(),
        "notes_scanned": len(notes),
        "pairs_flagged": len(conflicts),
        "by_class": by_class,
        "high_severity": sum(1 for c in conflicts if c["severity"] == "high"),
        "conflicts": conflicts[:200],
        "verification_targets": [
            {"ids": [c["left_id"], c["right_id"]], "why": c["detail"], "class": c["dispute_class"]}
            for c in conflicts if c["severity"] == "high"
        ][:15],
    }


def format_text(payload: Dict[str, Any]) -> str:
    lines = [
        "=" * 72,
        "CONTRADICTION REPORT",
        "=" * 72,
        f"Generated: {payload['generated_at']}",
        f"Notes: {payload['notes_scanned']}   Flagged pairs: {payload['pairs_flagged']}   High: {payload['high_severity']}",
        f"Classes: {payload['by_class'] or '{}'}",
        "",
    ]
    if not payload["conflicts"]:
        lines.append("No contradictions detected at the current overlap threshold.")
    for c in payload["conflicts"][:25]:
        lines.append(f"[{c['severity'].upper()}|{c['dispute_class']}|{','.join(c['kinds'])}] overlap={c['overlap']}")
        lines.append(f"  A ({c['left_id']}): {c['left_text']}")
        lines.append(f"  B ({c['right_id']}): {c['right_text']}")
        lines.append(f"  → {c['next_step']}")
        lines.append("")
    if payload["verification_targets"]:
        lines.append("VERIFICATION TARGETS")
        for t in payload["verification_targets"]:
            lines.append(f"  {t['ids']}: {t['why']}")
    lines.append("=" * 72)
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
        description="Detect numeric, negation, and antonym contradictions across notes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python contradiction_detector.py --input ../assets/sample_notes.jsonl
  python contradiction_detector.py --input store.json --min-overlap 0.25 --format json
""",
    )
    parser.add_argument("--input", "-i", required=True, help="Notes, claims, or evidence JSON/JSONL")
    parser.add_argument("--min-overlap", type=float, default=0.18, help="Minimum token Jaccard to compare a pair")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", "-o")
    args = parser.parse_args(argv)
    try:
        notes = load_notes(args.input)
        if len(notes) < 2:
            raise ValueError("Need at least two notes/claims to compare")
        payload = detect(notes, args.min_overlap)
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
