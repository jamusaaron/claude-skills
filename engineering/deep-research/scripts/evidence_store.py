#!/usr/bin/env python3
"""Evidence store with merge/resume.

JSON or JSONL store for research evidence cards. Supports init, add, merge,
query, stats, and export. Deduplicates by id, DOI, URL, or content hash so
continuing research can resume without losing prior work.

Usage:
    python evidence_store.py init --output store.jsonl
    python evidence_store.py add --store store.jsonl --title "..." --url "..." --claim "..."
    python evidence_store.py merge --store store.jsonl --incoming more.json
    python evidence_store.py query --store store.jsonl --question Q1 --format json
    python evidence_store.py stats --store store.jsonl
    python evidence_store.py export --store store.jsonl --output snapshot.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse


SCHEMA_VERSION = 1
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def content_hash(rec: Dict[str, Any]) -> str:
    key = {
        "title": (rec.get("title") or "").strip().lower(),
        "url": normalize_url(rec.get("url") or ""),
        "doi": (rec.get("doi") or "").lower(),
        "claims": rec.get("claims") or [],
    }
    blob = json.dumps(key, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    raw = url if "://" in url else "https://" + url
    try:
        p = urlparse(raw)
    except ValueError:
        return url.rstrip("/").lower()
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = (p.path or "").rstrip("/")
    return f"{host}{path}"


def extract_doi(rec: Dict[str, Any]) -> Optional[str]:
    for field in (rec.get("doi"), rec.get("url"), rec.get("id")):
        if not field:
            continue
        m = DOI_RE.search(str(field))
        if m:
            return m.group(0).rstrip(".").lower()
    return None


def identity_keys(rec: Dict[str, Any]) -> List[str]:
    keys = []
    if rec.get("id"):
        keys.append("id:" + str(rec["id"]).lower())
    doi = extract_doi(rec)
    if doi:
        keys.append("doi:" + doi)
        rec["doi"] = rec.get("doi") or doi
    url = normalize_url(rec.get("url") or "")
    if url:
        keys.append("url:" + url)
    keys.append("hash:" + (rec.get("hash") or content_hash(rec)))
    return [k for k in keys if k]


def default_card(**kwargs: Any) -> Dict[str, Any]:
    rec = {
        "id": kwargs.get("id"),
        "url": kwargs.get("url"),
        "doi": kwargs.get("doi"),
        "title": kwargs.get("title"),
        "authors": kwargs.get("authors") or [],
        "published": kwargs.get("published"),
        "retrieved": kwargs.get("retrieved") or utc_now(),
        "source_type": kwargs.get("source_type") or "other",
        "question_id": kwargs.get("question_id"),
        "claims": kwargs.get("claims") or [],
        "quotes": kwargs.get("quotes") or [],
        "credibility": kwargs.get("credibility") or {},
        "tags": kwargs.get("tags") or [],
        "persona": kwargs.get("persona") or "analyst",
        "notes": kwargs.get("notes") or "",
        "schema_version": SCHEMA_VERSION,
    }
    rec["hash"] = content_hash(rec)
    if not rec["id"]:
        rec["id"] = "ev-" + rec["hash"][:10]
    return rec


def normalize_card(raw: Dict[str, Any]) -> Dict[str, Any]:
    claims = raw.get("claims") or []
    if isinstance(claims, str):
        claims = [{"text": claims, "polarity": "supports"}]
    norm_claims = []
    for c in claims:
        if isinstance(c, str):
            norm_claims.append({"text": c, "polarity": "supports", "question_id": raw.get("question_id")})
        elif isinstance(c, dict) and (c.get("text") or c.get("claim")):
            norm_claims.append({
                "id": c.get("id"),
                "text": c.get("text") or c.get("claim"),
                "polarity": (c.get("polarity") or "supports").lower(),
                "question_id": c.get("question_id") or raw.get("question_id"),
            })
    authors = raw.get("authors") or raw.get("author") or []
    if isinstance(authors, str):
        authors = [a.strip() for a in re.split(r";| and | & ", authors) if a.strip()]
    tags = raw.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    rec = default_card(
        id=raw.get("id"),
        url=raw.get("url"),
        doi=raw.get("doi"),
        title=raw.get("title"),
        authors=authors,
        published=raw.get("published") or raw.get("date") or raw.get("year"),
        retrieved=raw.get("retrieved"),
        source_type=raw.get("source_type") or raw.get("type") or "other",
        question_id=raw.get("question_id"),
        claims=norm_claims,
        quotes=raw.get("quotes") or [],
        credibility=raw.get("credibility") if isinstance(raw.get("credibility"), dict) else (
            {"band": raw["band"]} if raw.get("band") else {}
        ),
        tags=tags,
        persona=raw.get("persona") or "analyst",
        notes=raw.get("notes") or "",
    )
    if raw.get("hash"):
        rec["hash"] = raw["hash"]
    return rec


def read_store(path: str) -> List[Dict[str, Any]]:
    try:
        raw = open(path, "r", encoding="utf-8").read().strip()
    except FileNotFoundError:
        return []
    if not raw:
        return []
    recs: List[Dict[str, Any]]
    if path.endswith(".jsonl") or raw[:1] not in "{[":
        recs = [json.loads(line) for line in raw.splitlines() if line.strip()]
    else:
        data = json.loads(raw)
        if isinstance(data, list):
            recs = data
        elif isinstance(data, dict):
            recs = data.get("evidence") or data.get("records") or data.get("items") or [data]
        else:
            raise ValueError("Unsupported store shape")
    return [normalize_card(r) for r in recs if isinstance(r, dict)]


def write_store(path: str, records: List[Dict[str, Any]], as_json: Optional[bool] = None) -> None:
    json_mode = as_json if as_json is not None else path.endswith(".json") and not path.endswith(".jsonl")
    if json_mode:
        payload = {
            "skill": "deep-research",
            "artifact": "evidence_store",
            "schema_version": SCHEMA_VERSION,
            "updated_at": utc_now(),
            "count": len(records),
            "evidence": records,
        }
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def merge_pair(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(old)
    for field in ("url", "doi", "title", "published", "source_type", "question_id", "persona", "notes"):
        if not merged.get(field) and new.get(field):
            merged[field] = new[field]
    for field in ("authors", "tags", "quotes"):
        combined = list(merged.get(field) or [])
        for item in new.get(field) or []:
            if item not in combined:
                combined.append(item)
        merged[field] = combined
    claims = list(merged.get("claims") or [])
    seen = {(c.get("text") or "").lower() for c in claims}
    for c in new.get("claims") or []:
        key = (c.get("text") or "").lower()
        if key and key not in seen:
            claims.append(c)
            seen.add(key)
    merged["claims"] = claims
    cred = dict(merged.get("credibility") or {})
    incoming = new.get("credibility") or {}
    if incoming:
        cred.update({k: v for k, v in incoming.items() if v not in (None, "", [], {})})
    merged["credibility"] = cred
    merged["retrieved"] = new.get("retrieved") or merged.get("retrieved") or utc_now()
    merged["hash"] = content_hash(merged)
    return merged


def merge_records(base: List[Dict[str, Any]], incoming: List[Dict[str, Any]]) -> Dict[str, Any]:
    index: Dict[str, int] = {}
    records = list(base)
    for i, rec in enumerate(records):
        for k in identity_keys(rec):
            index[k] = i
    added = 0
    merged_n = 0
    for rec in incoming:
        rec = normalize_card(rec)
        match = None
        for k in identity_keys(rec):
            if k in index:
                match = index[k]
                break
        if match is None:
            records.append(rec)
            idx = len(records) - 1
            for k in identity_keys(rec):
                index[k] = idx
            added += 1
        else:
            records[match] = merge_pair(records[match], rec)
            for k in identity_keys(records[match]):
                index[k] = match
            merged_n += 1
    return {"records": records, "added": added, "merged": merged_n, "total": len(records)}


def matches(rec: Dict[str, Any], args: argparse.Namespace) -> bool:
    if args.question and rec.get("question_id") != args.question:
        claims = rec.get("claims") or []
        if not any(c.get("question_id") == args.question for c in claims if isinstance(c, dict)):
            return False
    if args.source_type and rec.get("source_type") != args.source_type:
        return False
    if args.tag:
        tags = [str(t).lower() for t in rec.get("tags") or []]
        if args.tag.lower() not in tags:
            return False
    if args.persona and rec.get("persona") != args.persona:
        return False
    if args.contains:
        blob = json.dumps(rec, ensure_ascii=False).lower()
        if args.contains.lower() not in blob:
            return False
    return True


def stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    types: Dict[str, int] = {}
    questions: Dict[str, int] = {}
    personas: Dict[str, int] = {}
    claims_n = 0
    with_url = 0
    for rec in records:
        types[rec.get("source_type") or "other"] = types.get(rec.get("source_type") or "other", 0) + 1
        if rec.get("question_id"):
            questions[rec["question_id"]] = questions.get(rec["question_id"], 0) + 1
        personas[rec.get("persona") or "analyst"] = personas.get(rec.get("persona") or "analyst", 0) + 1
        claims_n += len(rec.get("claims") or [])
        if rec.get("url") or rec.get("doi"):
            with_url += 1
    return {
        "count": len(records),
        "claims": claims_n,
        "with_locator": with_url,
        "source_types": types,
        "questions": questions,
        "personas": personas,
    }


def format_stats(payload: Dict[str, Any]) -> str:
    s = payload["stats"]
    lines = [
        "=" * 72,
        "EVIDENCE STORE",
        "=" * 72,
        f"Updated: {payload.get('generated_at')}",
        f"Records: {s['count']}   Claims: {s['claims']}   With URL/DOI: {s['with_locator']}",
        f"Types: {s['source_types']}",
        f"Questions: {s['questions'] or '{}'}",
        f"Personas: {s['personas']}",
        "=" * 72,
    ]
    return "\n".join(lines)


def format_query(records: List[Dict[str, Any]]) -> str:
    lines = [f"{len(records)} record(s)", ""]
    for rec in records:
        lines.append(f"- [{rec.get('id')}] {rec.get('title') or '(untitled)'}")
        if rec.get("url"):
            lines.append(f"    {rec['url']}")
        for c in rec.get("claims") or []:
            lines.append(f"    claim ({c.get('polarity')}): {c.get('text')}")
    return "\n".join(lines)


def emit(payload: Any, fmt: str, output: Optional[str], text_fn=None) -> None:
    if fmt == "json":
        text = json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        text = text_fn(payload) if text_fn else json.dumps(payload, indent=2)
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(text + ("" if text.endswith("\n") else "\n"))
    else:
        print(text)


def parse_claim(text: Optional[str], question_id: Optional[str], polarity: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    return [{"text": text, "polarity": polarity, "question_id": question_id}]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="JSON/JSONL evidence store with merge and resume.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python evidence_store.py init --output store.jsonl
  python evidence_store.py add --store store.jsonl --title "ABS Labour Force" --url https://abs.gov.au --question Q1 --claim "Unemployment was 4.1%"
  python evidence_store.py merge --store store.jsonl --incoming extra.json
  python evidence_store.py query --store store.jsonl --question Q1 --format json
""",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Create an empty store")
    p_init.add_argument("--output", "-o", required=True)

    p_add = sub.add_parser("add", help="Append or merge one evidence card")
    p_add.add_argument("--store", required=True)
    p_add.add_argument("--id")
    p_add.add_argument("--title")
    p_add.add_argument("--url")
    p_add.add_argument("--doi")
    p_add.add_argument("--source-type", dest="source_type", default="other")
    p_add.add_argument("--question", dest="question_id")
    p_add.add_argument("--claim")
    p_add.add_argument("--polarity", default="supports", choices=["supports", "refutes", "neutral"])
    p_add.add_argument("--quote")
    p_add.add_argument("--published")
    p_add.add_argument("--tags")
    p_add.add_argument("--persona", default="analyst")
    p_add.add_argument("--notes")
    p_add.add_argument("--format", choices=["text", "json"], default="text")

    p_merge = sub.add_parser("merge", help="Merge an incoming JSON/JSONL into the store")
    p_merge.add_argument("--store", required=True)
    p_merge.add_argument("--incoming", required=True)
    p_merge.add_argument("--format", choices=["text", "json"], default="text")

    p_query = sub.add_parser("query", help="Filter records")
    p_query.add_argument("--store", required=True)
    p_query.add_argument("--question")
    p_query.add_argument("--source-type", dest="source_type")
    p_query.add_argument("--tag")
    p_query.add_argument("--persona")
    p_query.add_argument("--contains")
    p_query.add_argument("--format", choices=["text", "json"], default="text")
    p_query.add_argument("--output", "-o")

    p_stats = sub.add_parser("stats", help="Store summary")
    p_stats.add_argument("--store", required=True)
    p_stats.add_argument("--format", choices=["text", "json"], default="text")

    p_export = sub.add_parser("export", help="Write a snapshot JSON store")
    p_export.add_argument("--store", required=True)
    p_export.add_argument("--output", "-o", required=True)
    p_export.add_argument("--format", choices=["text", "json"], default="json")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "init":
            write_store(args.output, [])
            payload = {"ok": True, "path": args.output, "count": 0, "generated_at": utc_now()}
            emit(payload, "json" if args.output.endswith(".json") else "text", None, lambda p: f"Initialized empty store at {p['path']}")
            return 0

        if args.cmd == "add":
            records = read_store(args.store)
            tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
            quotes = [args.quote] if args.quote else []
            card = default_card(
                id=args.id,
                title=args.title,
                url=args.url,
                doi=args.doi,
                source_type=args.source_type,
                question_id=args.question_id,
                claims=parse_claim(args.claim, args.question_id, args.polarity),
                quotes=quotes,
                published=args.published,
                tags=tags,
                persona=args.persona,
                notes=args.notes,
            )
            result = merge_records(records, [card])
            write_store(args.store, result["records"])
            payload = {"ok": True, "added": result["added"], "merged": result["merged"], "total": result["total"], "id": card["id"]}
            emit(payload, args.format, None, lambda p: f"Stored {p['id']} (added={p['added']} merged={p['merged']} total={p['total']})")
            return 0

        if args.cmd == "merge":
            base = read_store(args.store)
            incoming = read_store(args.incoming)
            result = merge_records(base, incoming)
            write_store(args.store, result["records"])
            payload = {
                "ok": True,
                "added": result["added"],
                "merged": result["merged"],
                "total": result["total"],
                "generated_at": utc_now(),
            }
            emit(payload, args.format, None, lambda p: f"Merge complete: added={p['added']} merged={p['merged']} total={p['total']}")
            return 0

        if args.cmd == "query":
            records = [r for r in read_store(args.store) if matches(r, args)]
            payload = {"count": len(records), "evidence": records, "generated_at": utc_now()}
            emit(payload, args.format, args.output, lambda p: format_query(p["evidence"]))
            return 0

        if args.cmd == "stats":
            records = read_store(args.store)
            payload = {"generated_at": utc_now(), "stats": stats(records)}
            emit(payload, args.format, None, format_stats)
            return 0

        if args.cmd == "export":
            records = read_store(args.store)
            write_store(args.output, records, as_json=True)
            payload = {"ok": True, "path": args.output, "count": len(records)}
            emit(payload, args.format, None, lambda p: f"Exported {p['count']} records to {p['path']}")
            return 0

        raise ValueError(f"Unknown command {args.cmd}")
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
