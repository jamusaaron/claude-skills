#!/usr/bin/env python3
"""Maintain a claim–evidence ledger for deep research.

Commands: init, add-claim, add-evidence, add-source, link, status, gaps,
contradictions, export-md. JSON file on disk. Offline.

Usage:
    python claim_ledger.py init --path ledger.json --query "..."
    python claim_ledger.py add-claim --path ledger.json --id C1 --statement "..." --type fact
    python claim_ledger.py add-evidence --path ledger.json --id E1 --claim C1 --stance supports --url https://example.gov/x
    python claim_ledger.py status --path ledger.json --json
    python claim_ledger.py export-md --path ledger.json
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

SCHEMA_VERSION = "1.0"
CLAIM_TYPES = ("fact", "interpretation", "mechanism", "forecast", "value")
CLAIM_STATUS = ("unverified", "supported", "contested", "refuted", "insufficient")
STANCES = ("supports", "contradicts", "qualifies", "context")
BANDS = ("high", "medium-high", "medium", "medium-low", "low", "unscored")

ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,31}$")


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def empty_ledger(query: str) -> Dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "query": query,
        "created": utcnow(),
        "updated": utcnow(),
        "claims": [],
        "evidence": [],
        "sources": [],
    }


def load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("ledger must be a JSON object")
    for key in ("claims", "evidence", "sources"):
        data.setdefault(key, [])
    return data


def save(path: str, data: Dict[str, Any]) -> None:
    data["updated"] = utcnow()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(tmp, path)


def require_id(value: str, kind: str) -> str:
    if not ID_RE.match(value):
        raise ValueError(f"{kind} id '{value}' must match {ID_RE.pattern}")
    return value


def find(items: List[Dict[str, Any]], _id: str) -> Optional[Dict[str, Any]]:
    for item in items:
        if item.get("id") == _id:
            return item
    return None


def index_or_die(items: List[Dict[str, Any]], _id: str, kind: str) -> Dict[str, Any]:
    item = find(items, _id)
    if not item:
        raise ValueError(f"{kind} '{_id}' not found")
    return item


def add_unique(items: List[Dict[str, Any]], obj: Dict[str, Any], kind: str) -> None:
    if find(items, obj["id"]):
        raise ValueError(f"{kind} id '{obj['id']}' already exists")
    items.append(obj)


def cmd_init(args: argparse.Namespace) -> Dict[str, Any]:
    if os.path.exists(args.path) and not args.force:
        raise ValueError(f"{args.path} exists (pass --force to overwrite)")
    data = empty_ledger(args.query)
    save(args.path, data)
    return {"ok": True, "path": args.path, "query": args.query}


def cmd_add_claim(args: argparse.Namespace) -> Dict[str, Any]:
    data = load(args.path)
    claim = {
        "id": require_id(args.id, "claim"),
        "statement": args.statement,
        "type": args.type,
        "status": args.status,
        "confidence": args.confidence,
        "evidence_ids": [],
        "notes": args.notes or "",
    }
    add_unique(data["claims"], claim, "claim")
    save(args.path, data)
    return {"ok": True, "claim": claim}


def cmd_add_source(args: argparse.Namespace) -> Dict[str, Any]:
    data = load(args.path)
    source = {
        "id": require_id(args.id, "source"),
        "title": args.title,
        "url": args.url or "",
        "date": args.date or "",
        "type": args.type or "unknown",
        "integrity_band": args.band,
        "notes": args.notes or "",
    }
    add_unique(data["sources"], source, "source")
    save(args.path, data)
    return {"ok": True, "source": source}


def cmd_add_evidence(args: argparse.Namespace) -> Dict[str, Any]:
    data = load(args.path)
    ev = {
        "id": require_id(args.id, "evidence"),
        "claim_ids": [],
        "source_id": args.source or "",
        "quote": args.quote or "",
        "url": args.url or "",
        "date": args.date or "",
        "stance": args.stance,
        "integrity_band": args.band,
        "notes": args.notes or "",
    }
    add_unique(data["evidence"], ev, "evidence")
    if args.claim:
        link_one(data, args.claim, ev["id"])
    if args.source and not find(data["sources"], args.source):
        data["sources"].append({
            "id": args.source,
            "title": args.source_title or args.source,
            "url": args.url or "",
            "date": args.date or "",
            "type": "unknown",
            "integrity_band": args.band,
            "notes": "auto-created from add-evidence",
        })
    save(args.path, data)
    return {"ok": True, "evidence": ev}


def link_one(data: Dict[str, Any], claim_id: str, evidence_id: str) -> None:
    claim = index_or_die(data["claims"], claim_id, "claim")
    ev = index_or_die(data["evidence"], evidence_id, "evidence")
    if evidence_id not in claim["evidence_ids"]:
        claim["evidence_ids"].append(evidence_id)
    if claim_id not in ev["claim_ids"]:
        ev["claim_ids"].append(claim_id)
    refresh_status(claim, data)


def cmd_link(args: argparse.Namespace) -> Dict[str, Any]:
    data = load(args.path)
    link_one(data, args.claim, args.evidence)
    save(args.path, data)
    return {"ok": True, "claim": args.claim, "evidence": args.evidence}


def refresh_status(claim: Dict[str, Any], data: Dict[str, Any]) -> None:
    evs = [e for e in data["evidence"] if e["id"] in claim["evidence_ids"]]
    if not evs:
        claim["status"] = "unverified"
        return
    stances = {e["stance"] for e in evs}
    if stances == {"contradicts"}:
        claim["status"] = "refuted"
    elif "supports" in stances and "contradicts" in stances:
        claim["status"] = "contested"
    elif "supports" in stances:
        claim["status"] = "supported"
    else:
        claim["status"] = "insufficient"


def independence_clusters(evs: List[Dict[str, Any]]) -> int:
    hosts = set()
    for ev in evs:
        host = urlparse(ev.get("url") or "").netloc.lower().lstrip("www.")
        if host:
            hosts.add(host)
        elif ev.get("source_id"):
            hosts.add(ev["source_id"])
        else:
            hosts.add(ev["id"])
    return len(hosts)


def analyze(data: Dict[str, Any]) -> Dict[str, Any]:
    gaps = []
    contradictions = []
    for claim in data["claims"]:
        evs = [e for e in data["evidence"] if e["id"] in claim["evidence_ids"]]
        supports = [e for e in evs if e["stance"] == "supports"]
        contradicts = [e for e in evs if e["stance"] == "contradicts"]
        if len(supports) < 2 and claim["type"] == "fact":
            gaps.append({
                "claim_id": claim["id"],
                "issue": "under_sourced",
                "detail": f"fact claim has {len(supports)} supporting evidence item(s); need ≥2",
            })
        if independence_clusters(supports) < 2 and len(supports) >= 2:
            gaps.append({
                "claim_id": claim["id"],
                "issue": "single_cluster",
                "detail": "supporting evidence shares one host/source cluster",
            })
        if not evs:
            gaps.append({
                "claim_id": claim["id"],
                "issue": "no_evidence",
                "detail": "claim has no linked evidence",
            })
        if supports and contradicts:
            contradictions.append({
                "claim_id": claim["id"],
                "statement": claim["statement"],
                "support_ids": [e["id"] for e in supports],
                "contradict_ids": [e["id"] for e in contradicts],
                "classification_needed": "factual | interpretive | value — not yet classified",
            })
    orphans = [e["id"] for e in data["evidence"] if not e.get("claim_ids")]
    unused_sources = []
    used_source_ids = {e.get("source_id") for e in data["evidence"] if e.get("source_id")}
    for src in data["sources"]:
        if src["id"] not in used_source_ids:
            unused_sources.append(src["id"])
    return {
        "claim_count": len(data["claims"]),
        "evidence_count": len(data["evidence"]),
        "source_count": len(data["sources"]),
        "status_counts": _counts(data["claims"], "status"),
        "gaps": gaps,
        "contradictions": contradictions,
        "orphan_evidence": orphans,
        "unused_sources": unused_sources,
        "query": data.get("query"),
        "updated": data.get("updated"),
    }


def _counts(items: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for item in items:
        out[item.get(key, "unknown")] = out.get(item.get(key, "unknown"), 0) + 1
    return out


def cmd_status(args: argparse.Namespace) -> Dict[str, Any]:
    return analyze(load(args.path))


def cmd_gaps(args: argparse.Namespace) -> Dict[str, Any]:
    result = analyze(load(args.path))
    return {"gaps": result["gaps"], "orphan_evidence": result["orphan_evidence"]}


def cmd_contradictions(args: argparse.Namespace) -> Dict[str, Any]:
    result = analyze(load(args.path))
    return {"contradictions": result["contradictions"]}


def export_markdown(data: Dict[str, Any]) -> str:
    lines = [
        f"# Claim ledger",
        "",
        f"Query: {data.get('query', '')}",
        f"Updated: {data.get('updated', '')}",
        "",
        "| ID | Type | Status | Statement | Evidence |",
        "|----|------|--------|-----------|----------|",
    ]
    for c in data["claims"]:
        stmt = c["statement"].replace("|", "\\|")
        lines.append(
            f"| {c['id']} | {c['type']} | {c['status']} | {stmt} | {', '.join(c['evidence_ids']) or '—'} |"
        )
    lines.extend(["", "## Evidence", "",
                  "| ID | Stance | Band | Claims | URL | Quote |",
                  "|----|--------|------|--------|-----|-------|"])
    for e in data["evidence"]:
        quote = (e.get("quote") or "").replace("|", "\\|")[:180]
        lines.append(
            f"| {e['id']} | {e['stance']} | {e['integrity_band']} | "
            f"{', '.join(e.get('claim_ids') or []) or '—'} | {e.get('url') or '—'} | {quote} |"
        )
    return "\n".join(lines) + "\n"


def cmd_export_md(args: argparse.Namespace) -> Dict[str, Any]:
    data = load(args.path)
    text = export_markdown(data)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        return {"ok": True, "out": args.out, "bytes": len(text)}
    return {"ok": True, "markdown": text}


def cmd_export_csv(args: argparse.Namespace) -> Dict[str, Any]:
    data = load(args.path)
    out = args.out or "claims.csv"
    with open(out, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["claim_id", "type", "status", "statement", "evidence_ids"])
        for c in data["claims"]:
            writer.writerow([c["id"], c["type"], c["status"], c["statement"], ";".join(c["evidence_ids"])])
    return {"ok": True, "out": out}


def render_human(cmd: str, result: Dict[str, Any]) -> str:
    if cmd == "export-md" and "markdown" in result:
        return result["markdown"]
    if cmd == "status":
        lines = [
            f"Query: {result.get('query')}",
            f"Updated: {result.get('updated')}",
            f"Claims: {result['claim_count']}  Evidence: {result['evidence_count']}  Sources: {result['source_count']}",
            f"Statuses: {result['status_counts']}",
            f"Gaps: {len(result['gaps'])}  Contradictions: {len(result['contradictions'])}",
            f"Orphan evidence: {result['orphan_evidence'] or 'none'}",
        ]
        for gap in result["gaps"]:
            lines.append(f"  [{gap['issue']}] {gap['claim_id']}: {gap['detail']}")
        return "\n".join(lines)
    if cmd == "gaps":
        if not result["gaps"]:
            return "No gaps detected."
        return "\n".join(f"[{g['issue']}] {g['claim_id']}: {g['detail']}" for g in result["gaps"])
    if cmd == "contradictions":
        if not result["contradictions"]:
            return "No contradictions detected."
        lines = []
        for c in result["contradictions"]:
            lines.append(f"{c['claim_id']}: {c['statement']}")
            lines.append(f"  supports: {c['support_ids']}  contradicts: {c['contradict_ids']}")
        return "\n".join(lines)
    return json.dumps(result, indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    json_flag = argparse.ArgumentParser(add_help=False)
    json_flag.add_argument("--json", action="store_true", help="JSON output")
    parser = argparse.ArgumentParser(
        description="Claim-evidence ledger for deep research.",
        parents=[json_flag],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create an empty ledger", parents=[json_flag])
    p_init.add_argument("--path", required=True)
    p_init.add_argument("--query", required=True)
    p_init.add_argument("--force", action="store_true")

    p_c = sub.add_parser("add-claim", parents=[json_flag])
    p_c.add_argument("--path", required=True)
    p_c.add_argument("--id", required=True)
    p_c.add_argument("--statement", required=True)
    p_c.add_argument("--type", choices=CLAIM_TYPES, default="fact")
    p_c.add_argument("--status", choices=CLAIM_STATUS, default="unverified")
    p_c.add_argument("--confidence", default="unscored")
    p_c.add_argument("--notes", default="")

    p_s = sub.add_parser("add-source", parents=[json_flag])
    p_s.add_argument("--path", required=True)
    p_s.add_argument("--id", required=True)
    p_s.add_argument("--title", required=True)
    p_s.add_argument("--url")
    p_s.add_argument("--date")
    p_s.add_argument("--type", default="unknown")
    p_s.add_argument("--band", choices=BANDS, default="unscored")
    p_s.add_argument("--notes", default="")

    p_e = sub.add_parser("add-evidence", parents=[json_flag])
    p_e.add_argument("--path", required=True)
    p_e.add_argument("--id", required=True)
    p_e.add_argument("--claim", help="Claim id to link immediately")
    p_e.add_argument("--source", help="Source id")
    p_e.add_argument("--source-title")
    p_e.add_argument("--quote")
    p_e.add_argument("--url")
    p_e.add_argument("--date")
    p_e.add_argument("--stance", choices=STANCES, default="supports")
    p_e.add_argument("--band", choices=BANDS, default="unscored")
    p_e.add_argument("--notes", default="")

    p_l = sub.add_parser("link", parents=[json_flag])
    p_l.add_argument("--path", required=True)
    p_l.add_argument("--claim", required=True)
    p_l.add_argument("--evidence", required=True)

    for name, help_text in (
        ("status", "Summary counts, gaps, contradictions"),
        ("gaps", "Under-sourced claims and orphans"),
        ("contradictions", "Claims with support + contradict evidence"),
    ):
        sp = sub.add_parser(name, help=help_text, parents=[json_flag])
        sp.add_argument("--path", required=True)

    p_md = sub.add_parser("export-md", parents=[json_flag])
    p_md.add_argument("--path", required=True)
    p_md.add_argument("--out")

    p_csv = sub.add_parser("export-csv", parents=[json_flag])
    p_csv.add_argument("--path", required=True)
    p_csv.add_argument("--out")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "init": cmd_init,
        "add-claim": cmd_add_claim,
        "add-source": cmd_add_source,
        "add-evidence": cmd_add_evidence,
        "link": cmd_link,
        "status": cmd_status,
        "gaps": cmd_gaps,
        "contradictions": cmd_contradictions,
        "export-md": cmd_export_md,
        "export-csv": cmd_export_csv,
    }
    try:
        result = dispatch[args.command](args)
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_human(args.command, result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
