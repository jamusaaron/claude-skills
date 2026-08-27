#!/usr/bin/env python3
"""Check citation integrity of a claim ledger (and optional report markdown).

Flags: claims below min sources, malformed URLs, missing dates, duplicate IDs,
orphan evidence, unused sources, citation IDs in prose that are not in the ledger.

Usage:
    python citation_integrity.py --ledger ledger.json
    python citation_integrity.py --ledger ledger.json --report report.md --min-sources 2 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

ID_IN_PROSE = re.compile(r"\[([A-Z][A-Za-z0-9_-]{0,31})\]")


def load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("ledger must be a JSON object")
    for key in ("claims", "evidence", "sources"):
        data.setdefault(key, [])
    return data


def url_ok(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def duplicate_ids(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues = []
    for kind in ("claims", "evidence", "sources"):
        ids = [item.get("id") for item in data.get(kind) or [] if item.get("id")]
        for _id, n in Counter(ids).items():
            if n > 1:
                issues.append({"kind": kind, "id": _id, "count": n})
    return issues


def inspect(data: Dict[str, Any], min_sources: int, report_text: str) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    claim_ids = {c.get("id") for c in data["claims"] if c.get("id")}
    evidence_ids = {e.get("id") for e in data["evidence"] if e.get("id")}
    source_ids = {s.get("id") for s in data["sources"] if s.get("id")}

    for dup in duplicate_ids(data):
        issues.append({
            "code": "duplicate_id",
            "severity": "error",
            "message": f"Duplicate {dup['kind']} id {dup['id']} (n={dup['count']})",
        })

    for claim in data["claims"]:
        cid = claim.get("id")
        ev_ids = claim.get("evidence_ids") or []
        unknown = [e for e in ev_ids if e not in evidence_ids]
        if unknown:
            issues.append({
                "code": "dangling_evidence_ref",
                "severity": "error",
                "claim_id": cid,
                "message": f"Claim {cid} references missing evidence {unknown}",
            })
        supporting = [
            e for e in data["evidence"]
            if e.get("id") in ev_ids and e.get("stance") == "supports"
        ]
        if claim.get("type") == "fact" and len(supporting) < min_sources:
            issues.append({
                "code": "under_sourced_claim",
                "severity": "error" if len(supporting) == 0 else "warning",
                "claim_id": cid,
                "message": f"Fact claim {cid} has {len(supporting)} supporting sources (min {min_sources})",
            })
        hosts: Set[str] = set()
        for e in supporting:
            host = urlparse(e.get("url") or "").netloc.lower().lstrip("www.")
            if host:
                hosts.add(host)
            elif e.get("source_id"):
                hosts.add(e["source_id"])
        if len(supporting) >= min_sources and len(hosts) < min(2, min_sources):
            issues.append({
                "code": "single_cluster",
                "severity": "warning",
                "claim_id": cid,
                "message": f"Claim {cid} supporting evidence is one provenance cluster",
            })

    for ev in data["evidence"]:
        eid = ev.get("id")
        if not ev.get("claim_ids"):
            issues.append({
                "code": "orphan_evidence",
                "severity": "warning",
                "evidence_id": eid,
                "message": f"Evidence {eid} is not linked to any claim",
            })
        url = ev.get("url") or ""
        if url and not url_ok(url):
            issues.append({
                "code": "malformed_url",
                "severity": "error",
                "evidence_id": eid,
                "message": f"Evidence {eid} URL is not well-formed: {url}",
            })
        if not url and not ev.get("source_id"):
            issues.append({
                "code": "no_locator",
                "severity": "warning",
                "evidence_id": eid,
                "message": f"Evidence {eid} has neither URL nor source_id",
            })
        if not ev.get("date"):
            issues.append({
                "code": "missing_date",
                "severity": "warning",
                "evidence_id": eid,
                "message": f"Evidence {eid} has no date",
            })
        sid = ev.get("source_id")
        if sid and sid not in source_ids:
            issues.append({
                "code": "missing_source",
                "severity": "warning",
                "evidence_id": eid,
                "message": f"Evidence {eid} points at unknown source {sid}",
            })
        for cid in ev.get("claim_ids") or []:
            if cid not in claim_ids:
                issues.append({
                    "code": "dangling_claim_ref",
                    "severity": "error",
                    "evidence_id": eid,
                    "message": f"Evidence {eid} references missing claim {cid}",
                })

    for src in data["sources"]:
        url = src.get("url") or ""
        if url and not url_ok(url):
            issues.append({
                "code": "malformed_url",
                "severity": "error",
                "source_id": src.get("id"),
                "message": f"Source {src.get('id')} URL is not well-formed: {url}",
            })
        if not src.get("date"):
            issues.append({
                "code": "missing_date",
                "severity": "info",
                "source_id": src.get("id"),
                "message": f"Source {src.get('id')} has no date",
            })

    used_sources = {e.get("source_id") for e in data["evidence"] if e.get("source_id")}
    for sid in source_ids - used_sources:
        issues.append({
            "code": "unused_source",
            "severity": "info",
            "source_id": sid,
            "message": f"Source {sid} is never cited by evidence",
        })

    if report_text:
        cited = set(ID_IN_PROSE.findall(report_text))
        known = claim_ids | evidence_ids | source_ids
        unknown = sorted(cited - known - {"TODO", "TBD", "sic", "emphasis"})
        for _id in unknown:
            if len(_id) <= 2 and _id.isupper():
                continue
            issues.append({
                "code": "uncited_in_ledger",
                "severity": "warning",
                "message": f"Report cites [{_id}] which is not in the ledger",
            })
        for cid in claim_ids:
            if cid not in cited and f"[{cid}]" not in report_text:
                issues.append({
                    "code": "claim_missing_from_report",
                    "severity": "info",
                    "claim_id": cid,
                    "message": f"Ledger claim {cid} is not cited in the report text",
                })

    errors = sum(1 for i in issues if i["severity"] == "error")
    warnings = sum(1 for i in issues if i["severity"] == "warning")
    return {
        "ok": errors == 0,
        "error_count": errors,
        "warning_count": warnings,
        "issue_count": len(issues),
        "issues": issues,
        "min_sources": min_sources,
        "claim_count": len(data["claims"]),
        "evidence_count": len(data["evidence"]),
        "source_count": len(data["sources"]),
    }


def render_human(result: Dict[str, Any]) -> str:
    status = "PASS" if result["ok"] else "FAIL"
    lines = [
        f"Citation integrity: {status}",
        f"Errors: {result['error_count']}  Warnings: {result['warning_count']}  Other: {result['issue_count'] - result['error_count'] - result['warning_count']}",
        f"Min supporting sources per fact claim: {result['min_sources']}",
        "",
    ]
    if not result["issues"]:
        lines.append("No issues.")
        return "\n".join(lines)
    order = {"error": 0, "warning": 1, "info": 2}
    for issue in sorted(result["issues"], key=lambda i: order.get(i["severity"], 9)):
        lines.append(f"[{issue['severity']}] {issue['code']}: {issue['message']}")
    return "\n".join(lines)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate claim-ledger citation integrity.")
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--report", help="Optional markdown report to cross-check IDs")
    parser.add_argument("--min-sources", type=int, default=2)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        data = load(args.ledger)
        report_text = ""
        if args.report:
            with open(args.report, "r", encoding="utf-8") as handle:
                report_text = handle.read()
        result = inspect(data, args.min_sources, report_text)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_human(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
