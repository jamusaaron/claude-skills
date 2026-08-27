#!/usr/bin/env python3
"""Confidence and uncertainty quantifier.

Maps each finding to an uncertainty-ladder band using source count, publisher
independence, recency, corroboration, and contradiction flags. Flags
overconfidence (high language, thin evidence).

Usage:
    python confidence_calibrator.py --input matrix.json
    python confidence_calibrator.py --input store.json --contradictions report.json --format json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


LADDER = [
    (90, "very-high", "Very High >90% — multiple independent primaries, stable over time."),
    (70, "high", "High 70–90% — convergent high-integrity sources; residual caveats."),
    (50, "medium", "Medium 50–70% — plausible but thin, mixed, or method-limited."),
    (0, "low", "Low <50% — sparse, contested, or single-provenance."),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_any(path: str) -> Any:
    text = open(path, "r", encoding="utf-8").read().strip()
    if path.endswith(".jsonl"):
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def rows_from(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("matrix", "findings", "claims", "results", "evidence", "records", "items"):
            if isinstance(data.get(key), list):
                return [x for x in data[key] if isinstance(x, dict)]
        if data.get("text") or data.get("claim") or data.get("title"):
            return [data]
    return []


def band_name(score: float) -> Tuple[str, str]:
    for threshold, name, desc in LADDER:
        if score >= threshold:
            return name, desc
    return "low", LADDER[-1][2]


def logistic(x: float) -> float:
    return 100.0 / (1.0 + math.exp(-x))


def independence(row: Dict[str, Any]) -> Dict[str, Any]:
    indep = row.get("independence") or {}
    if indep:
        return {
            "family_count": int(indep.get("family_count") or 0),
            "independent_high": int(indep.get("independent_high_support") or 0),
            "shared_risk": bool(indep.get("shared_provenance_risk")),
            "meets_bar": bool(indep.get("meets_pivotal_bar")),
        }
    sources = row.get("sources") or row.get("support_sources") or []
    n = len(sources) if isinstance(sources, list) else int(row.get("unique_source_ids") or row.get("source_count") or 0)
    return {
        "family_count": n,
        "independent_high": int(row.get("high_integrity_count") or 0),
        "shared_risk": bool(row.get("shared_provenance_risk")),
        "meets_bar": n >= 2,
    }


def recency_bonus(row: Dict[str, Any]) -> float:
    if row.get("recent_count"):
        return min(1.2, 0.3 * int(row["recent_count"]))
    if row.get("stale"):
        return -0.8
    return 0.0


def contradiction_penalty(row_id: str, text: str, conflicts: List[Dict[str, Any]]) -> Tuple[float, int]:
    if not conflicts:
        return 0.0, 0
    n = 0
    penalty = 0.0
    blob = (text or "").lower()
    for c in conflicts:
        ids = {c.get("left_id"), c.get("right_id")}
        involved = row_id in ids or (blob and blob[:40] in (c.get("left_text") or "").lower())
        if not involved:
            continue
        n += 1
        if c.get("severity") == "high" or c.get("dispute_class") == "factual":
            penalty += 1.4
        elif c.get("dispute_class") == "interpretive":
            penalty += 0.5
        else:
            penalty += 0.2
    return penalty, n


def calibrate_row(row: Dict[str, Any], conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
    text = row.get("text") or row.get("claim") or row.get("title") or ""
    rid = str(row.get("id") or text[:24] or "finding")
    status = (row.get("status") or "").lower()
    support = int(row.get("support_count") or row.get("source_count") or len(row.get("support_sources") or []) or 0)
    refute = int(row.get("refute_count") or 0)
    weight = float(row.get("support_weight") or 0) - float(row.get("refute_weight") or 0)
    indep = independence(row)

    # Logit-style features around a 50% prior.
    x = 0.0
    x += 0.45 * min(support, 6)
    x -= 0.55 * min(refute, 6)
    x += 0.12 * max(-6.0, min(6.0, weight))
    x += 0.50 * min(indep["independent_high"], 4)
    x += 0.20 * min(indep["family_count"], 5)
    if indep["shared_risk"]:
        x -= 0.9
    if status in {"contested"}:
        x -= 1.1
    elif status in {"weakly-supported", "insufficient"}:
        x -= 0.8
    elif status == "supported" and indep["meets_bar"]:
        x += 0.7
    elif status == "refuted":
        x -= 1.3
    x += recency_bonus(row)
    cpen, cn = contradiction_penalty(rid, text, conflicts)
    x -= cpen

    score = round(max(5.0, min(97.0, logistic(x - 1.1))), 1)
    band, desc = band_name(score)

    drivers = []
    if support:
        drivers.append(f"{support} supporting source(s)")
    if refute:
        drivers.append(f"{refute} contradicting source(s)")
    if indep["shared_risk"]:
        drivers.append("shared publisher family")
    if indep["independent_high"]:
        drivers.append(f"{indep['independent_high']} independent high-integrity supports")
    if cn:
        drivers.append(f"{cn} contradiction flag(s)")
    if not drivers:
        drivers.append("sparse metadata — defaulting toward medium/low")

    overconfident = band in {"high", "very-high"} and (support < 2 or indep["shared_risk"] or cn)
    underpowered = band == "low" and support >= 4 and refute == 0

    return {
        "id": rid,
        "text": text,
        "status": status or None,
        "confidence": score,
        "band": band,
        "ladder": desc,
        "drivers": drivers,
        "overconfidence_flag": overconfident,
        "possible_undercall": underpowered,
        "independence": indep,
        "contradiction_flags": cn,
        "what_would_move_it": (
            "One independent high-integrity primary on the same operationalization."
            if score < 70
            else "A registered replication or contradictory official statistic."
        ),
    }


def format_text(payload: Dict[str, Any]) -> str:
    lines = [
        "=" * 72,
        "CONFIDENCE CALIBRATION",
        "=" * 72,
        f"Generated: {payload['generated_at']}",
        f"Findings: {payload['count']}   Mean: {payload['summary']['mean']}   "
        f"Overconfidence flags: {payload['summary']['overconfidence_flags']}",
        "",
        f"{'BAND':12} {'%':>5}  FINDING",
        "-" * 72,
    ]
    for item in payload["findings"]:
        text = item["text"] if len(item["text"]) < 58 else item["text"][:55] + "..."
        flag = " ⚠ OVERCONFIDENT" if item["overconfidence_flag"] else ""
        lines.append(f"{item['band']:12} {item['confidence']:5.1f}  {text}{flag}")
        lines.append(f"             drivers: {'; '.join(item['drivers'][:3])}")
    lines += ["", "LADDER"]
    for _, name, desc in LADDER:
        lines.append(f"  {name:10} {desc}")
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
        description="Quantify confidence bands for research findings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python confidence_calibrator.py --input matrix.json
  python confidence_calibrator.py --input store.json --contradictions contra.json --format json
""",
    )
    parser.add_argument("--input", "-i", required=True, help="Claim matrix, findings, or evidence JSON/JSONL")
    parser.add_argument("--contradictions", help="Optional contradiction_detector.py JSON")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", "-o")
    args = parser.parse_args(argv)
    try:
        rows = rows_from(load_any(args.input))
        if not rows:
            raise ValueError("No findings/claims found in input")
        conflicts: List[Dict[str, Any]] = []
        if args.contradictions:
            cdata = load_any(args.contradictions)
            if isinstance(cdata, dict):
                conflicts = cdata.get("conflicts") or []
            elif isinstance(cdata, list):
                conflicts = [x for x in cdata if isinstance(x, dict)]
        findings = [calibrate_row(r, conflicts) for r in rows]
        scores = [f["confidence"] for f in findings]
        payload = {
            "skill": "deep-research",
            "artifact": "confidence_report",
            "generated_at": utc_now(),
            "count": len(findings),
            "summary": {
                "mean": round(sum(scores) / len(scores), 1) if scores else 0,
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "very_high": sum(1 for f in findings if f["band"] == "very-high"),
                "high": sum(1 for f in findings if f["band"] == "high"),
                "medium": sum(1 for f in findings if f["band"] == "medium"),
                "low": sum(1 for f in findings if f["band"] == "low"),
                "overconfidence_flags": sum(1 for f in findings if f["overconfidence_flag"]),
            },
            "findings": findings,
        }
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
