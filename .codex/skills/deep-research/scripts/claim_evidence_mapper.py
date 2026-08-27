#!/usr/bin/env python3
"""Claim-Evidence Mapper — Map claims to supporting and contradicting sources.

Builds evidence matrices, identifies unsupported claims, detects shared-provenance
clusters, and flags claims needing verification.

Usage:
    python3 claim_evidence_mapper.py claims.json --format text
    python3 claim_evidence_mapper.py --demo --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse


def extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return "unknown"


def map_claims(data: dict[str, Any]) -> dict[str, Any]:
    claims = data.get("claims", [])
    sources = {s["id"]: s for s in data.get("sources", [])}

    mapped = []
    unsupported = []
    needs_verification = []
    shared_provenance_warnings = []

    for claim in claims:
        claim_id = claim.get("id", "unknown")
        supporting_ids = claim.get("supporting_sources", [])
        contradicting_ids = claim.get("contradicting_sources", [])
        pivotal = claim.get("pivotal", False)
        confidence_target = claim.get("confidence_target", "Medium")

        supporting = []
        for sid in supporting_ids:
            src = sources.get(sid)
            if src:
                supporting.append({
                    "source_id": sid,
                    "title": src.get("title", ""),
                    "rating": src.get("rating", "Medium"),
                    "url": src.get("url", ""),
                    "domain": extract_domain(src.get("url", "")),
                })

        contradicting = []
        for sid in contradicting_ids:
            src = sources.get(sid)
            if src:
                contradicting.append({
                    "source_id": sid,
                    "title": src.get("title", ""),
                    "rating": src.get("rating", "Medium"),
                    "url": src.get("url", ""),
                })

        high_integrity_support = [
            s for s in supporting if s["rating"] in ("High", "Medium-High")
        ]
        domains = [s["domain"] for s in supporting if s["domain"] != "unknown"]
        unique_domains = len(set(domains))
        shared_provenance = unique_domains < len(domains) and len(domains) > 1

        status = "supported"
        if not supporting:
            status = "unsupported"
            unsupported.append(claim_id)
        elif len(high_integrity_support) < 1:
            status = "weakly_supported"
        elif pivotal and len(high_integrity_support) < 2:
            status = "needs_verification"
            needs_verification.append({
                "claim_id": claim_id,
                "reason": "Pivotal claim with fewer than 2 high-integrity supporting sources",
                "high_integrity_count": len(high_integrity_support),
            })
        elif shared_provenance and pivotal:
            status = "shared_provenance_risk"
            shared_provenance_warnings.append({
                "claim_id": claim_id,
                "domains": list(set(domains)),
                "reason": "Supporting sources may share common origin",
            })

        if contradicting and supporting:
            status = "contested" if status == "supported" else status

        mapped.append({
            "claim_id": claim_id,
            "statement": claim.get("statement", ""),
            "pivotal": pivotal,
            "confidence_target": confidence_target,
            "status": status,
            "supporting_count": len(supporting),
            "high_integrity_support_count": len(high_integrity_support),
            "contradicting_count": len(contradicting),
            "supporting_sources": supporting,
            "contradicting_sources": contradicting,
            "shared_provenance_risk": shared_provenance,
        })

    contested = [m for m in mapped if m["status"] == "contested"]
    weak = [m for m in mapped if m["status"] in ("unsupported", "weakly_supported", "needs_verification")]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_claims": len(mapped),
            "supported": sum(1 for m in mapped if m["status"] == "supported"),
            "contested": len(contested),
            "unsupported": len(unsupported),
            "needs_verification": len(needs_verification),
            "shared_provenance_warnings": len(shared_provenance_warnings),
        },
        "quality_gate": {
            "passes": len(unsupported) == 0 and len(needs_verification) == 0,
            "blocking_issues": len(unsupported) + len(needs_verification),
        },
        "claims": mapped,
        "verification_queue": needs_verification,
        "shared_provenance_warnings": shared_provenance_warnings,
        "recommendations": _recommendations(mapped, needs_verification, contested),
    }


def _recommendations(mapped, needs_verification, contested) -> list[str]:
    recs = []
    if needs_verification:
        recs.append(f"Run verification loop on {len(needs_verification)} pivotal claims")
    if contested:
        recs.append(f"Apply steelman analysis to {len(contested)} contested claims")
    weak = [m for m in mapped if m["status"] in ("unsupported", "weakly_supported")]
    if weak:
        recs.append(f"Acquire additional sources for {len(weak)} weakly supported claims")
    if not recs:
        recs.append("Evidence mapping passes quality gate — proceed to synthesis")
    return recs


def format_text(result: dict[str, Any]) -> str:
    s = result["summary"]
    lines = [
        "=" * 72,
        "CLAIM-EVIDENCE MAPPING REPORT",
        f"Generated: {result['generated_at']}",
        "=" * 72,
        "",
        f"Total claims: {s['total_claims']}",
        f"Supported: {s['supported']} | Contested: {s['contested']} | Unsupported: {s['unsupported']}",
        f"Needs verification: {s['needs_verification']}",
        f"Quality gate: {'PASS' if result['quality_gate']['passes'] else 'FAIL'}",
        "",
        "## Recommendations",
    ]
    for r in result["recommendations"]:
        lines.append(f"  • {r}")

    lines.append("\n## Claim Matrix\n")
    for c in result["claims"]:
        marker = " [PIVOTAL]" if c["pivotal"] else ""
        lines.append(f"[{c['claim_id']}] {c['statement'][:100]}{marker}")
        lines.append(f"  Status: {c['status']} | Support: {c['supporting_count']} "
                     f"(high-integrity: {c['high_integrity_support_count']}) | "
                     f"Contradict: {c['contradicting_count']}")
        if c["supporting_sources"]:
            lines.append("  Supporting:")
            for src in c["supporting_sources"]:
                lines.append(f"    • [{src['source_id']}] {src['title'][:60]} ({src['rating']})")
        lines.append("")

    if result["verification_queue"]:
        lines.append("## Verification Queue")
        for v in result["verification_queue"]:
            lines.append(f"  • [{v['claim_id']}] {v['reason']}")

    lines.append("=" * 72)
    return "\n".join(lines)


DEMO = {
    "sources": [
        {"id": "s1", "title": "Gov Report A", "rating": "High", "url": "https://gov.example/report-a"},
        {"id": "s2", "title": "Journal Study B", "rating": "High", "url": "https://journal.example/study-b"},
        {"id": "s3", "title": "Blog Post C", "rating": "Low", "url": "https://blog.example/post-c"},
        {"id": "s4", "title": "Contrarian Study D", "rating": "Medium-High", "url": "https://journal.example/study-d"},
    ],
    "claims": [
        {
            "id": "c1",
            "statement": "Intervention X reduces outcome Y by 30% on average",
            "supporting_sources": ["s1", "s2"],
            "pivotal": True,
            "confidence_target": "High",
        },
        {
            "id": "c2",
            "statement": "Long-term effects remain uncertain due to limited follow-up data",
            "supporting_sources": ["s2"],
            "contradicting_sources": ["s4"],
            "pivotal": True,
            "confidence_target": "Medium",
        },
        {
            "id": "c3",
            "statement": "Industry claims widespread adoption",
            "supporting_sources": ["s3"],
            "pivotal": False,
        },
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Map claims to supporting and contradicting evidence")
    parser.add_argument("input", nargs="?", help="JSON with claims and sources arrays")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--output", "-o")

    args = parser.parse_args()

    if args.demo:
        data = DEMO
    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
    else:
        parser.error("Provide input file or --demo")

    result = map_claims(data)
    output = json.dumps(result, indent=2) if args.format == "json" else format_text(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
