#!/usr/bin/env python3
"""Citation and bibliography normalizer.

Parses URLs, DOIs, BibTeX snippets, markdown links, and loose APA-like strings
into a compact bibliographic record. Emits APA, BibTeX, and CSL-JSON-ish forms.
Deduplicates by DOI, URL, or title+year.

Usage:
    python citation_normalizer.py --input citations.txt
    python citation_normalizer.py --doi 10.1038/nature14539 --format json
    python citation_normalizer.py --input store.jsonl --style apa
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse, unquote


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
URL_RE = re.compile(r"https?://[^\s\]>)\"]+", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
BIBTEX_RE = re.compile(r"@(\w+)\s*\{\s*([^,]+)\s*,(.*?)\n\}", re.S | re.I)
BIB_FIELD_RE = re.compile(r"(\w+)\s*=\s*[{\"']?(.*?)[}\"']?\s*,?\s*(?=\n)", re.S)
APA_RE = re.compile(
    r"^(?P<authors>.+?)\s*\((?P<year>19|20\d{2})\)\.\s*(?P<title>.+?)(?:\.\s*(?P<rest>.*))?$",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def host_of(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def citekey(record: Dict[str, Any]) -> str:
    authors = record.get("authors") or ["anon"]
    last = re.sub(r"[^a-z]", "", authors[0].split(",")[0].split()[-1].lower()) or "anon"
    year = record.get("year") or "nd"
    slug = re.sub(r"[^a-z0-9]+", "", (record.get("title") or "untitled").lower())[:18]
    return f"{last}{year}{slug}"


def split_authors(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(a).strip() for a in raw if str(a).strip()]
    text = str(raw)
    text = text.replace(" and ", "; ").replace(" & ", "; ")
    parts = re.split(r"\s*;\s*|\s+,\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


def parse_bibtex_block(kind: str, key: str, body: str) -> Dict[str, Any]:
    fields = {}
    for match in BIB_FIELD_RE.finditer(body):
        fields[match.group(1).lower()] = match.group(2).strip().strip("{}, ")
    authors = split_authors(fields.get("author") or fields.get("editor"))
    year = None
    if fields.get("year") and YEAR_RE.search(fields["year"]):
        year = YEAR_RE.search(fields["year"]).group(0)
    rec = {
        "id": key,
        "type": kind.lower(),
        "title": fields.get("title"),
        "authors": authors,
        "year": year,
        "container": fields.get("journal") or fields.get("booktitle") or fields.get("publisher"),
        "doi": None,
        "url": fields.get("url"),
        "volume": fields.get("volume"),
        "issue": fields.get("number"),
        "pages": fields.get("pages"),
        "publisher": fields.get("publisher"),
        "raw_type": "bibtex",
    }
    doi = fields.get("doi") or ""
    m = DOI_RE.search(doi) or DOI_RE.search(fields.get("url") or "")
    if m:
        rec["doi"] = m.group(0).rstrip(".")
        rec["url"] = rec["url"] or f"https://doi.org/{rec['doi']}"
    return rec


def parse_apa(line: str) -> Optional[Dict[str, Any]]:
    m = APA_RE.match(line.strip())
    if not m:
        return None
    year_full = m.group("year")
    # group includes only '19' or '20' plus rest via regex — fix
    year_m = YEAR_RE.search(line)
    year = year_m.group(0) if year_m else None
    title = (m.group("title") or "").strip(" .")
    authors = split_authors(m.group("authors"))
    rest = (m.group("rest") or "").strip(" .")
    doi = DOI_RE.search(line)
    url = URL_RE.search(line)
    return {
        "id": None,
        "type": "article",
        "title": title,
        "authors": authors,
        "year": year,
        "container": rest.split(".")[0] if rest else None,
        "doi": doi.group(0) if doi else None,
        "url": url.group(0) if url else (f"https://doi.org/{doi.group(0)}" if doi else None),
        "raw_type": "apa",
        "year_hint": year_full,
    }


def record_from_url(url: str, title: Optional[str] = None) -> Dict[str, Any]:
    url = url.rstrip(").,]")
    doi = DOI_RE.search(url)
    host = host_of(url)
    inferred_title = title
    if not inferred_title:
        path = unquote(urlparse(url).path or "").strip("/")
        slug = path.split("/")[-1] if path else host
        inferred_title = re.sub(r"[-_]+", " ", re.sub(r"\.\w+$", "", slug)).strip() or host
    year_m = YEAR_RE.search(url)
    return {
        "id": None,
        "type": "webpage",
        "title": inferred_title,
        "authors": [],
        "year": year_m.group(0) if year_m else None,
        "container": host,
        "doi": doi.group(0) if doi else None,
        "url": url,
        "raw_type": "url",
    }


def record_from_doi(doi: str, title: Optional[str] = None) -> Dict[str, Any]:
    doi = doi.strip().lstrip("doi:").strip()
    return {
        "id": None,
        "type": "article",
        "title": title or doi,
        "authors": [],
        "year": None,
        "container": None,
        "doi": doi,
        "url": f"https://doi.org/{doi}",
        "raw_type": "doi",
    }


def record_from_object(obj: Dict[str, Any]) -> Dict[str, Any]:
    doi = obj.get("doi")
    if isinstance(doi, str):
        m = DOI_RE.search(doi)
        doi = m.group(0) if m else doi
    url = obj.get("url")
    if not doi and url:
        m = DOI_RE.search(url)
        doi = m.group(0) if m else None
    authors = obj.get("authors") or obj.get("author") or []
    if isinstance(authors, str):
        authors = split_authors(authors)
    year = obj.get("year") or obj.get("published")
    if year:
        ym = YEAR_RE.search(str(year))
        year = ym.group(0) if ym else str(year)[:4]
    return {
        "id": obj.get("id"),
        "type": obj.get("type") or obj.get("source_type") or "document",
        "title": obj.get("title"),
        "authors": authors,
        "year": year,
        "container": obj.get("container") or obj.get("journal") or host_of(url or ""),
        "doi": doi,
        "url": url or (f"https://doi.org/{doi}" if doi else None),
        "volume": obj.get("volume"),
        "issue": obj.get("issue"),
        "pages": obj.get("pages"),
        "publisher": obj.get("publisher"),
        "raw_type": "object",
    }


def parse_text_blob(text: str) -> List[Dict[str, Any]]:
    recs: List[Dict[str, Any]] = []
    for match in BIBTEX_RE.finditer(text):
        recs.append(parse_bibtex_block(match.group(1), match.group(2).strip(), match.group(3)))
    if recs:
        return recs
    for match in MD_LINK_RE.finditer(text):
        recs.append(record_from_url(match.group(2), match.group(1)))
    remaining = MD_LINK_RE.sub("", text)
    for url in URL_RE.findall(remaining):
        recs.append(record_from_url(url))
    for doi in DOI_RE.findall(remaining):
        if not any((r.get("doi") or "").lower() == doi.lower() for r in recs):
            recs.append(record_from_doi(doi))
    if not recs:
        for line in text.splitlines():
            line = line.strip(" -*\t")
            if not line:
                continue
            apa = parse_apa(line)
            recs.append(apa if apa else {"id": None, "type": "note", "title": line, "authors": [], "year": None, "doi": None, "url": None, "raw_type": "raw"})
    return recs


def load_input(path: str) -> List[Dict[str, Any]]:
    raw = open(path, "r", encoding="utf-8").read()
    if path.endswith(".jsonl"):
        recs = []
        for line in raw.splitlines():
            if line.strip():
                recs.append(record_from_object(json.loads(line)))
        return recs
    stripped = raw.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        data = json.loads(stripped)
        if isinstance(data, list):
            return [record_from_object(x) if isinstance(x, dict) else record_from_url(str(x)) for x in data]
        if isinstance(data, dict):
            for key in ("sources", "records", "items", "evidence", "citations"):
                if isinstance(data.get(key), list):
                    return [record_from_object(x) for x in data[key] if isinstance(x, dict)]
            return [record_from_object(data)]
    return parse_text_blob(raw)


def dedupe(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = {}
    out = []
    for rec in records:
        doi = (rec.get("doi") or "").lower().rstrip(".")
        url = (rec.get("url") or "").rstrip("/").lower()
        title_year = ((rec.get("title") or "").lower().strip(), rec.get("year"))
        key = doi or url or title_year
        if key in seen:
            prev = seen[key]
            for field in ("title", "year", "container", "doi", "url"):
                if not prev.get(field) and rec.get(field):
                    prev[field] = rec[field]
            if rec.get("authors") and len(rec["authors"]) > len(prev.get("authors") or []):
                prev["authors"] = rec["authors"]
            continue
        seen[key] = rec
        out.append(rec)
    for rec in out:
        rec["id"] = rec.get("id") or citekey(rec)
    return out


def format_apa(rec: Dict[str, Any]) -> str:
    authors = rec.get("authors") or []
    if not authors:
        who = rec.get("container") or host_of(rec.get("url") or "") or "Unknown"
    elif len(authors) == 1:
        who = authors[0]
    elif len(authors) == 2:
        who = f"{authors[0]} & {authors[1]}"
    else:
        who = f"{authors[0]} et al."
    year = rec.get("year") or "n.d."
    title = rec.get("title") or "[Untitled]"
    container = rec.get("container")
    tail = []
    if container:
        tail.append(container)
    if rec.get("doi"):
        tail.append(f"https://doi.org/{rec['doi']}")
    elif rec.get("url"):
        tail.append(rec["url"])
    rest = ". ".join(tail)
    return f"{who} ({year}). {title}. {rest}".strip()


def format_bibtex(rec: Dict[str, Any]) -> str:
    kind = "article" if rec.get("doi") or rec.get("type") == "article" else "misc"
    fields = [f"  title = {{{rec.get('title') or 'Untitled'}}}"]
    if rec.get("authors"):
        fields.append("  author = {" + " and ".join(rec["authors"]) + "}")
    if rec.get("year"):
        fields.append(f"  year = {{{rec['year']}}}")
    if rec.get("container"):
        key = "journal" if kind == "article" else "howpublished"
        fields.append(f"  {key} = {{{rec['container']}}}")
    if rec.get("doi"):
        fields.append(f"  doi = {{{rec['doi']}}}")
    if rec.get("url"):
        fields.append(f"  url = {{{rec['url']}}}")
    return "@{}{{{},\n{}\n}}".format(kind, rec["id"], ",\n".join(fields))


def format_csl(rec: Dict[str, Any]) -> Dict[str, Any]:
    authors = []
    for a in rec.get("authors") or []:
        if "," in a:
            family, given = [p.strip() for p in a.split(",", 1)]
            authors.append({"family": family, "given": given})
        else:
            parts = a.split()
            authors.append({"family": parts[-1], "given": " ".join(parts[:-1])} if len(parts) > 1 else {"family": a})
    issued = {"year": int(rec["year"])} if rec.get("year") and str(rec["year"]).isdigit() else None
    return {
        "id": rec["id"],
        "type": "article-journal" if rec.get("type") == "article" else "webpage",
        "title": rec.get("title"),
        "author": authors,
        "issued": issued,
        "DOI": rec.get("doi"),
        "URL": rec.get("url"),
        "container-title": rec.get("container"),
    }


def format_text(payload: Dict[str, Any], style: str) -> str:
    lines = [
        "=" * 72,
        "NORMALIZED BIBLIOGRAPHY",
        "=" * 72,
        f"Generated: {payload['generated_at']}   n={payload['count']}   duplicates_merged={payload['duplicates_merged']}",
        "",
    ]
    for rec in payload["records"]:
        if style == "bibtex":
            lines.append(rec["bibtex"])
            lines.append("")
        elif style == "csl":
            lines.append(json.dumps(rec["csl"], ensure_ascii=False))
        else:
            lines.append(f"- {rec['apa']}")
    lines.append("=" * 72)
    return "\n".join(lines)


def emit(payload: Dict[str, Any], fmt: str, style: str, output: Optional[str]) -> None:
    if fmt == "json":
        text = json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        text = format_text(payload, style)
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(text + ("" if text.endswith("\n") else "\n"))
    else:
        print(text)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Normalize citations from URLs, DOIs, BibTeX, APA, or evidence stores.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python citation_normalizer.py --doi 10.1038/nature14539 --title "A paper"
  python citation_normalizer.py --input cites.txt --style apa
  python citation_normalizer.py --input store.jsonl --format json
""",
    )
    parser.add_argument("--input", "-i", help="File: txt, bib, json, jsonl")
    parser.add_argument("--url", help="Single URL")
    parser.add_argument("--doi", help="Single DOI")
    parser.add_argument("--title", help="Title override for single URL/DOI")
    parser.add_argument("--style", choices=["apa", "bibtex", "csl"], default="apa", help="Text bibliography style")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", "-o")
    args = parser.parse_args(argv)
    try:
        recs: List[Dict[str, Any]] = []
        if args.input:
            recs.extend(load_input(args.input))
        if args.url:
            recs.append(record_from_url(args.url, args.title))
        if args.doi:
            recs.append(record_from_doi(args.doi, args.title))
        if not recs:
            raise ValueError("Provide --input, --url, and/or --doi")
        before = len(recs)
        recs = dedupe(recs)
        enriched = []
        for rec in recs:
            rec = dict(rec)
            rec["apa"] = format_apa(rec)
            rec["bibtex"] = format_bibtex(rec)
            rec["csl"] = format_csl(rec)
            enriched.append(rec)
        payload = {
            "skill": "deep-research",
            "artifact": "bibliography",
            "generated_at": utc_now(),
            "count": len(enriched),
            "duplicates_merged": max(0, before - len(enriched)),
            "records": enriched,
        }
        emit(payload, args.format, args.style, args.output)
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
