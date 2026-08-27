#!/usr/bin/env python3
"""Citation Formatter — Format bibliographies in APA, MLA, Chicago, and Harvard styles.

Supports books, journal articles, web pages, reports, and government documents.
No external dependencies — stdlib only.

Usage:
    python3 citation_formatter.py bibliography.json --style apa --format text
    python3 citation_formatter.py --demo --style chicago --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any


def _authors_apa(authors: list[str]) -> str:
    if not authors:
        return "Unknown"
    if len(authors) == 1:
        parts = authors[0].split()
        if len(parts) >= 2:
            return f"{parts[-1]}, {parts[0][0]}."
        return authors[0]
    if len(authors) == 2:
        return f"{_authors_apa([authors[0]])[:-1]}, & {_authors_apa([authors[1]])}"
    return f"{_authors_apa([authors[0]])[:-1]}, et al."


def _authors_mla(authors: list[str]) -> str:
    if not authors:
        return "Unknown"
    if len(authors) == 1:
        parts = authors[0].split()
        if len(parts) >= 2:
            return f"{parts[-1]}, {parts[0]}"
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]}, and {authors[1]}"
    return f"{authors[0]}, et al."


def format_apa(entry: dict[str, Any]) -> str:
    etype = entry.get("type", "webpage")
    authors = entry.get("authors", [])
    title = entry.get("title", "Untitled")
    year = entry.get("year", "n.d.")
    url = entry.get("url", "")

    author_str = _authors_apa(authors)

    if etype == "journal":
        journal = entry.get("journal", "")
        volume = entry.get("volume", "")
        issue = entry.get("issue", "")
        pages = entry.get("pages", "")
        doi = entry.get("doi", "")
        vol_issue = f"{volume}"
        if issue:
            vol_issue += f"({issue})"
        cite = f"{author_str} ({year}). {title}. *{journal}*, {vol_issue}, {pages}."
        if doi:
            cite += f" https://doi.org/{doi}"
        return cite

    if etype in ("report", "government"):
        publisher = entry.get("publisher", entry.get("institution", ""))
        return f"{author_str} ({year}). *{title}* ({entry.get('report_number', '')}). {publisher}. {url}".strip()

    if etype == "book":
        publisher = entry.get("publisher", "")
        return f"{author_str} ({year}). *{title}*. {publisher}."

    accessed = entry.get("accessed", "")
    site = entry.get("site_name", entry.get("publisher", ""))
    cite = f"{author_str} ({year}). {title}. {site}."
    if url:
        cite += f" {url}"
    if accessed:
        cite += f" (Accessed {accessed})"
    return cite


def format_mla(entry: dict[str, Any]) -> str:
    authors = entry.get("authors", [])
    title = entry.get("title", "Untitled")
    year = entry.get("year", "n.d.")
    url = entry.get("url", "")
    author_str = _authors_mla(authors)
    etype = entry.get("type", "webpage")

    if etype == "journal":
        journal = entry.get("journal", "")
        vol = entry.get("volume", "")
        pages = entry.get("pages", "")
        return f'{author_str}. "{title}." *{journal}*, vol. {vol}, {year}, pp. {pages}.'

    if etype == "book":
        publisher = entry.get("publisher", "")
        return f'{author_str}. *{title}*. {publisher}, {year}.'

    site = entry.get("site_name", "")
    accessed = entry.get("accessed", "")
    cite = f'{author_str}. "{title}." *{site}*, {year}, {url}.'
    if accessed:
        cite += f" Accessed {accessed}."
    return cite


def format_chicago(entry: dict[str, Any]) -> str:
    authors = entry.get("authors", [])
    title = entry.get("title", "Untitled")
    year = entry.get("year", "n.d.")
    url = entry.get("url", "")
    author_str = ", ".join(authors) if authors else "Unknown"
    etype = entry.get("type", "webpage")

    if etype == "journal":
        journal = entry.get("journal", "")
        vol = entry.get("volume", "")
        no = entry.get("issue", "")
        pages = entry.get("pages", "")
        return f'{author_str}. "{title}." *{journal}* {vol}, no. {no} ({year}): {pages}.'

    if etype == "book":
        publisher = entry.get("publisher", "")
        place = entry.get("place", "")
        return f'{author_str}. *{title}*. {place}: {publisher}, {year}.'

    accessed = entry.get("accessed", "")
    cite = f'{author_str}. "{title}." Accessed {accessed or year}. {url}.'
    return cite


def format_harvard(entry: dict[str, Any]) -> str:
    authors = entry.get("authors", [])
    title = entry.get("title", "Untitled")
    year = entry.get("year", "n.d.")
    url = entry.get("url", "")
    if authors:
        parts = authors[0].split()
        first_author = f"{parts[-1]}, {parts[0][0]}." if len(parts) >= 2 else authors[0]
        if len(authors) > 1:
            first_author += " et al."
    else:
        first_author = "Unknown"

    etype = entry.get("type", "webpage")
    if etype == "journal":
        journal = entry.get("journal", "")
        vol = entry.get("volume", "")
        pages = entry.get("pages", "")
        return f"{first_author} ({year}) '{title}', *{journal}*, {vol}, pp. {pages}."

    if etype == "book":
        publisher = entry.get("publisher", "")
        return f"{first_author} ({year}) *{title}*. {publisher}."

    accessed = entry.get("accessed", "")
    cite = f"{first_author} ({year}) '{title}'. Available at: {url}"
    if accessed:
        cite += f" (Accessed: {accessed})"
    return cite


FORMATTERS = {
    "apa": format_apa,
    "mla": format_mla,
    "chicago": format_chicago,
    "harvard": format_harvard,
}


def format_bibliography(entries: list[dict], style: str) -> dict[str, Any]:
    formatter = FORMATTERS.get(style, format_apa)
    formatted = []
    for i, entry in enumerate(entries, 1):
        try:
            citation = formatter(entry)
        except Exception as e:
            citation = f"[ERROR formatting entry {i}: {e}]"
        formatted.append({
            "index": i,
            "id": entry.get("id", f"ref{i}"),
            "type": entry.get("type", "webpage"),
            "citation": citation,
            "in_text": _in_text(entry, style, i),
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "style": style,
        "count": len(formatted),
        "entries": formatted,
    }


def _in_text(entry: dict, style: str, index: int) -> str:
    authors = entry.get("authors", [])
    year = entry.get("year", "n.d.")
    if style == "apa":
        if authors:
            parts = authors[0].split()
            name = parts[-1] if parts else "Unknown"
            if len(authors) == 1:
                return f"({name}, {year})"
            return f"({name} et al., {year})"
        return f"(Unknown, {year})"
    if style == "mla":
        if authors:
            parts = authors[0].split()
            return f"({parts[-1]})" if parts else "(Unknown)"
        return "(Unknown)"
    if style in ("chicago", "harvard"):
        return f"[{index}]"
    return f"[{index}]"


DEMO = [
    {
        "id": "ref1",
        "type": "journal",
        "authors": ["Jane Smith", "John Doe"],
        "title": "Evidence synthesis in complex domains",
        "journal": "Journal of Research Methods",
        "year": "2025",
        "volume": "42",
        "issue": "3",
        "pages": "201-225",
        "doi": "10.1000/example.doi",
    },
    {
        "id": "ref2",
        "type": "government",
        "authors": ["World Health Organization"],
        "title": "Global Health Statistics 2025",
        "year": "2025",
        "institution": "WHO",
        "url": "https://www.who.int/data/example",
        "accessed": "2025-08-27",
    },
    {
        "id": "ref3",
        "type": "webpage",
        "authors": ["Alice Researcher"],
        "title": "Policy brief on emerging regulations",
        "site_name": "Policy Institute",
        "year": "2024",
        "url": "https://example.org/policy-brief",
        "accessed": "2025-08-27",
    },
]


def format_text(result: dict[str, Any]) -> str:
    lines = [
        "=" * 72,
        f"BIBLIOGRAPHY — {result['style'].upper()} Style",
        f"Generated: {result['generated_at']} | Entries: {result['count']}",
        "=" * 72,
        "",
        "## References",
        "",
    ]
    for e in result["entries"]:
        lines.append(f"[{e['index']}] {e['citation']}")
        lines.append(f"    In-text: {e['in_text']}")
        lines.append("")
    lines.append("=" * 72)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Format bibliographies in standard citation styles")
    parser.add_argument("input", nargs="?", help="JSON bibliography file")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--style", choices=list(FORMATTERS.keys()), default="apa")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--output", "-o")

    args = parser.parse_args()

    if args.demo:
        entries = DEMO
    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
        entries = data.get("entries", data if isinstance(data, list) else [])
    else:
        parser.error("Provide input file or --demo")

    result = format_bibliography(entries, args.style)
    output = json.dumps(result, indent=2) if args.format == "json" else format_text(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Bibliography written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
