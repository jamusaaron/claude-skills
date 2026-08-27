#!/usr/bin/env python3
"""Detect consensus and contradictions in structured research notes.

Classifies disputes as factual, interpretive, or value-laden using polarity
and antonym/negation heuristics. No LLM calls.

Usage:
    python contradiction_detector.py notes.json
    python contradiction_detector.py notes.json --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


ANTONYM_PAIRS = [
    ("increase", "decrease"),
    ("increased", "decreased"),
    ("higher", "lower"),
    ("more", "less"),
    ("effective", "ineffective"),
    ("safe", "unsafe"),
    ("true", "false"),
    ("support", "oppose"),
    ("supports", "contradicts"),
    ("positive", "negative"),
    ("benefit", "harm"),
    ("benefits", "harms"),
    ("causal", "spurious"),
    ("significant", "null"),
    ("remote", "office"),
    ("better", "worse"),
    ("success", "failure"),
    ("legal", "illegal"),
]

VALUE_MARKERS = (
    "should", "must", "ought", "fair", "unfair", "ethical", "wrong",
    "right to", "moral", "just", "unjust", "deserve",
)
INTERPRETIVE_MARKERS = (
    "suggests", "implies", "means that", "because", "due to", "driven by",
    "indicates that", "may reflect", "consistent with", "explained by",
)
FACTUAL_MARKERS = (
    "percent", "%", "rate", "count", "n=", "sample", "dated", "filed",
    "published", "measured", "observed", "statute", "section",
)

NEGATION = re.compile(r"\b(?:not|no|never|n't|without|neither)\b", re.I)
TOKEN = re.compile(r"[a-z0-9%+\-]+")


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[“”\"']", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def stem(token: str) -> str:
    if token.endswith("ing") and len(token) > 6:
        return token[:-3]
    if token.endswith("ed") and len(token) > 5:
        return token[:-2]
    if token.endswith("es") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 3 and not token.endswith("ss"):
        return token[:-1]
    return token


def tokens(text: str) -> List[str]:
    return [stem(t) for t in TOKEN.findall(normalize(text))]


def signature(text: str) -> Tuple[frozenset, str]:
    toks = tokens(text)
    antonym_side = "neutral"
    for a, b in ANTONYM_PAIRS:
        if a in toks:
            antonym_side = a
            toks = [t for t in toks if t != a]
            break
        if b in toks:
            antonym_side = b
            toks = [t for t in toks if t != b]
            break
    # Drop filler
    drop = {"the", "a", "an", "of", "and", "to", "in", "for", "on", "is", "that", "with"}
    core = frozenset(t for t in toks if t not in drop and len(t) > 2)
    if NEGATION.search(text):
        antonym_side = f"neg:{antonym_side}"
    return core, antonym_side


def overlap(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def classify_dispute(text_a: str, text_b: str) -> str:
    blob = f"{text_a} {text_b}".lower()
    if any(m in blob for m in VALUE_MARKERS):
        return "value_laden"
    if any(m in blob for m in INTERPRETIVE_MARKERS) and not any(m in blob for m in FACTUAL_MARKERS):
        return "interpretive"
    return "factual"


def opposing(side_a: str, side_b: str) -> bool:
    if side_a == side_b:
        return False
    if side_a.startswith("neg:") and side_a[4:] == side_b:
        return True
    if side_b.startswith("neg:") and side_b[4:] == side_a:
        return True
    for a, b in ANTONYM_PAIRS:
        pair = {a, b}
        if {side_a, side_b} == pair:
            return True
    polar = {
        "supports": "contradicts",
        "support": "oppose",
        "for": "against",
    }
    return polar.get(side_a) == side_b or polar.get(side_b) == side_a


def polarities_oppose(pol_a: str, pol_b: str) -> bool:
    negative = {"contradicts", "against", "disconfirm", "oppose"}
    positive = {"supports", "for"}
    return (pol_a in positive and pol_b in negative) or (pol_b in positive and pol_a in negative)


def load_notes(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return {"claims": data}
    if not isinstance(data, dict):
        raise ValueError("Expected notes object or claims list.")
    return data


def detect(notes: Dict[str, Any]) -> Dict[str, Any]:
    claims = notes.get("claims") or notes.get("notes") or []
    prepared = []
    for claim in claims:
        if isinstance(claim, str):
            text = claim
            cid = claim[:40]
            polarity = "supports"
            qid = None
        else:
            text = str(claim.get("claim") or claim.get("text") or claim.get("statement") or "")
            cid = str(claim.get("id") or text[:40])
            polarity = str(claim.get("polarity") or "supports").lower()
            qid = claim.get("question_id")
        core, side = signature(text)
        # Polarity field can flip side
        if polarity in {"contradicts", "against", "disconfirm", "oppose"}:
            side = f"neg:{side}" if not side.startswith("neg:") else side[4:]
        prepared.append({
            "id": cid,
            "text": text,
            "question_id": qid,
            "polarity": polarity,
            "core": core,
            "side": side,
            "source_ids": claim.get("source_ids") or claim.get("supports") or [] if isinstance(claim, dict) else [],
        })

    contradictions = []
    consensus_groups: List[List[str]] = []
    used_pairs = set()

    for i, a in enumerate(prepared):
        for b in prepared[i + 1 :]:
            sim = overlap(a["core"], b["core"])
            same_question = bool(a["question_id"] and a["question_id"] == b["question_id"])
            lexical_hit = sim >= 0.28 and opposing(a["side"], b["side"])
            polarity_hit = polarities_oppose(a["polarity"], b["polarity"]) and (
                same_question or sim >= 0.18
            )
            if not (lexical_hit or polarity_hit):
                continue
            pair = tuple(sorted([a["id"], b["id"]]))
            if pair in used_pairs:
                continue
            used_pairs.add(pair)
            contradictions.append({
                "claims": [a["id"], b["id"]],
                "texts": [a["text"], b["text"]],
                "overlap": round(sim, 2),
                "dispute_type": classify_dispute(a["text"], b["text"]),
                "question_ids": [x for x in (a["question_id"], b["question_id"]) if x],
                "resolution_hint": _hint(classify_dispute(a["text"], b["text"])),
            })

    # Consensus: high overlap, same side
    parent = {c["id"]: c["id"] for c in prepared}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i, a in enumerate(prepared):
        for b in prepared[i + 1 :]:
            sim = overlap(a["core"], b["core"])
            if (
                sim >= 0.34
                and not opposing(a["side"], b["side"])
                and not polarities_oppose(a["polarity"], b["polarity"])
            ):
                union(a["id"], b["id"])

    buckets: Dict[str, List[str]] = defaultdict(list)
    for c in prepared:
        buckets[find(c["id"])].append(c["id"])
    consensus_groups = [sorted(v) for v in buckets.values() if len(v) >= 2]
    consensus_groups.sort(key=len, reverse=True)

    type_counts: Dict[str, int] = defaultdict(int)
    for item in contradictions:
        type_counts[item["dispute_type"]] += 1

    return {
        "claim_count": len(prepared),
        "contradiction_count": len(contradictions),
        "contradictions": sorted(contradictions, key=lambda x: x["overlap"], reverse=True),
        "consensus_groups": consensus_groups,
        "dispute_type_counts": dict(type_counts),
        "summary": (
            f"{len(contradictions)} contradiction(s), {len(consensus_groups)} consensus cluster(s)."
        ),
    }


def _hint(kind: str) -> str:
    return {
        "factual": "Resolve with primary data, vintage dates, and identical metric definitions.",
        "interpretive": "Present both frameworks with evidential weight; do not collapse into a fake fact.",
        "value_laden": "Map underlying values and implications; do not treat as an empirical tie.",
    }[kind]


def format_text(report: Dict[str, Any]) -> str:
    lines = [
        "CONTRADICTION / CONSENSUS REPORT",
        "=" * 72,
        report["summary"],
        "",
    ]
    if report["contradictions"]:
        lines.append("Contradictions")
        for item in report["contradictions"]:
            lines.append(
                f"  [{item['dispute_type']}] overlap={item['overlap']:.2f}  "
                f"{item['claims'][0]} vs {item['claims'][1]}"
            )
            lines.append(f"    A: {item['texts'][0]}")
            lines.append(f"    B: {item['texts'][1]}")
            lines.append(f"    Next: {item['resolution_hint']}")
        lines.append("")
    if report["consensus_groups"]:
        lines.append("Consensus clusters")
        for group in report["consensus_groups"]:
            lines.append("  - " + ", ".join(group))
    if not report["contradictions"] and not report["consensus_groups"]:
        lines.append("No overlapping claims detected. Check that notes share entities/metrics.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect contradictions and consensus clusters in structured notes."
    )
    parser.add_argument("notes_file", help="JSON notes with a claims array")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        notes = load_notes(args.notes_file)
        report = detect(notes)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, default=list))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
