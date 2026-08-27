#!/usr/bin/env python3
"""Deterministic search-query expander.

Builds boolean / site: / filetype: / scholarly query variants from a seed
question. No APIs. Packs cover web, academic, government, filings, code, docs,
news, and patents.

Usage:
    python query_expander.py --query "hybrid work productivity software teams"
    python query_expander.py --query "s351 adverse action" --pack legal --geo AU --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple


STOP = {
    "the", "a", "an", "of", "to", "and", "in", "on", "for", "is", "that", "with",
    "from", "about", "into", "over", "what", "how", "why", "does", "do", "are",
    "vs", "versus", "between",
}

SYNONYMS = {
    "productivity": ["output", "performance", "throughput", "efficiency"],
    "hybrid work": ["remote-hybrid", "work from home", "distributed teams", "WFH"],
    "software": ["engineering", "developer", "SWE", "dev teams"],
    "ai": ["artificial intelligence", "machine learning", "LLM", "foundation model"],
    "regulation": ["rulemaking", "compliance", "statute", "regulatory"],
    "employment": ["labour", "labor", "workplace", "industrial relations"],
    "dismissal": ["termination", "firing", "sacked", "adverse action"],
    "privacy": ["data protection", "GDPR", "PII", "personal information"],
    "climate": ["emissions", "net zero", "decarbonisation", "decarbonization"],
    "pricing": ["packaging", "ARPU", "discounting", "list price"],
    "security": ["vulnerability", "CVE", "exploit", "appsec"],
    "latency": ["p99", "response time", "tail latency"],
}

PACKS: Dict[str, Dict[str, Any]] = {
    "web": {
        "label": "Open web (precision + recall)",
        "sites": [],
        "filetypes": ["pdf"],
        "extras": [],
    },
    "academic": {
        "label": "Scholarly",
        "sites": ["arxiv.org", "pubmed.ncbi.nlm.nih.gov", "nih.gov", "jstor.org", "ssrn.com", "nber.org"],
        "filetypes": ["pdf"],
        "extras": ['"systematic review"', '"meta-analysis"', "author:", "intitle:"],
    },
    "government": {
        "label": "Government / official statistics",
        "sites": [],  # filled per geo
        "filetypes": ["pdf", "xlsx", "csv"],
        "extras": ['"official statistics"', "filetype:pdf"],
    },
    "filings": {
        "label": "Corporate / regulator filings",
        "sites": ["sec.gov", "asic.gov.au", "companieshouse.gov.uk"],
        "filetypes": ["pdf", "htm"],
        "extras": ['"10-K"', '"annual report"', "EDGAR", "form 8-K"],
    },
    "news": {
        "label": "Quality journalism",
        "sites": ["reuters.com", "apnews.com", "bbc.com", "ft.com", "economist.com", "propublica.org"],
        "filetypes": [],
        "extras": [],
    },
    "code": {
        "label": "Code, issues, RFCs",
        "sites": ["github.com", "gitlab.com", "rfc-editor.org", "datatracker.ietf.org"],
        "filetypes": [],
        "extras": ["site:github.com", "filename:README", "lang:python"],
    },
    "docs": {
        "label": "Product / technical docs",
        "sites": ["readthedocs.io", "developer.mozilla.org"],
        "filetypes": ["pdf"],
        "extras": ['"architecture"', "intitle:docs OR intitle:documentation"],
    },
    "patents": {
        "label": "Patents",
        "sites": ["patents.google.com", "worldwide.espacenet.com", "uspto.gov"],
        "filetypes": ["pdf"],
        "extras": ["CPC:", "assignee:"],
    },
    "legal": {
        "label": "Legal primary sources",
        "sites": [],
        "filetypes": ["pdf"],
        "extras": ['"explanatory memorandum"', 'judgment OR decision OR "full bench"'],
    },
    "contrarian": {
        "label": "Outlier / disconfirming",
        "sites": [],
        "filetypes": [],
        "extras": ['"failed to replicate"', 'critique OR rebuttal OR "we find no evidence"'],
    },
}

GEO_SITES = {
    "AU": {
        "government": [
            "abs.gov.au", "fairwork.gov.au", "fwc.gov.au", "legislation.gov.au",
            "pc.gov.au", "treasury.gov.au", "ato.gov.au", "asic.gov.au",
        ],
        "legal": ["austlii.edu.au", "legislation.gov.au", "fwc.gov.au", "jade.io"],
    },
    "US": {
        "government": ["census.gov", "bls.gov", "gao.gov", "cbo.gov", "congress.gov", "sec.gov"],
        "legal": ["law.cornell.edu", "supremecourt.gov", "govinfo.gov"],
    },
    "UK": {
        "government": ["gov.uk", "ons.gov.uk", "legislation.gov.uk", "parliament.uk"],
        "legal": ["legislation.gov.uk", "bailii.org"],
    },
    "EU": {
        "government": ["europa.eu", "eur-lex.europa.eu", "eurostat.ec.europa.eu"],
        "legal": ["eur-lex.europa.eu", "curia.europa.eu"],
    },
    "GLOBAL": {
        "government": ["oecd.org", "who.int", "imf.org", "worldbank.org", "un.org"],
        "legal": ["ohchr.org", "icc-cpi.int"],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tokenize(query: str) -> List[str]:
    parts = re.findall(r'"[^"]+"|\S+', query)
    return [p for p in parts if p.lower().strip('"') not in STOP]


def core_phrase(query: str) -> str:
    cleaned = re.sub(r"\s+", " ", query).strip().rstrip("?")
    if " " in cleaned and not cleaned.startswith('"'):
        return f'"{cleaned}"' if len(cleaned.split()) <= 8 else cleaned
    return cleaned


def synonyms_for(query: str) -> List[Tuple[str, str]]:
    hits = []
    low = query.lower()
    for key, alts in SYNONYMS.items():
        if key in low:
            for alt in alts[:3]:
                hits.append((key, alt))
    return hits


def or_group(terms: Sequence[str]) -> str:
    parts = []
    for t in terms:
        if " " in t and not t.startswith('"'):
            parts.append(f'"{t}"')
        else:
            parts.append(t)
    return "(" + " OR ".join(parts) + ")"


def site_or(sites: Sequence[str]) -> str:
    return "(" + " OR ".join(f"site:{s}" for s in sites) + ")"


def after_clause(after: Optional[str]) -> str:
    if not after:
        return ""
    # Google-style after: and Bing-ish since — emit both as separate variants later.
    return f"after:{after}"


def expand(query: str, packs: List[str], geo: str, after: Optional[str], limit: int) -> List[Dict[str, Any]]:
    tokens = tokenize(query)
    phrase = core_phrase(query)
    syns = synonyms_for(query)
    geo_sites = GEO_SITES.get(geo.upper(), GEO_SITES["GLOBAL"])
    variants: List[Dict[str, Any]] = []

    def add(qid: str, purpose: str, pack: str, q: str) -> None:
        q = re.sub(r"\s+", " ", q).strip()
        if after and "after:" not in q and "since:" not in q:
            q = f"{q} {after_clause(after)}"
        variants.append({
            "id": qid,
            "pack": pack,
            "purpose": purpose,
            "query": q,
        })

    add("q-core", "Exact-phrase precision", "web", phrase)
    add("q-broad", "Recall / horizon scan", "web", " ".join(t.strip('"') for t in tokens[:8]))
    if syns:
        swapped = query
        key, alt = syns[0]
        swapped = re.sub(re.escape(key), alt, swapped, count=1, flags=re.I)
        add("q-syn", f"Synonym swap ({key}→{alt})", "web", swapped)
        or_q = query
        for key, alt in syns[:2]:
            or_q = re.sub(re.escape(key), or_group([key, alt]), or_q, count=1, flags=re.I)
        add("q-or", "Boolean synonym OR-group", "web", or_q)

    add("q-intitle", "Title constraint", "web", f"intitle:{tokens[0] if tokens else phrase} {phrase}")
    add("q-pdf", "Document hunt", "web", f"{phrase} filetype:pdf")
    add("q-exclude-seo", "Reduce content-farm noise", "web", f"{phrase} -site:pinterest.com -site:reddit.com -inurl:signup")
    add("q-disconfirm", "Disconfirming evidence", "contrarian", f"{phrase} {PACKS['contrarian']['extras'][0]}")
    add("q-no-evidence", "Negative-result hunt", "contrarian", f"{phrase} \"no significant\" OR \"null result\" OR \"we find no\"")

    selected = packs or ["web", "academic", "government", "news", "contrarian"]
    for pack in selected:
        spec = PACKS.get(pack)
        if not spec:
            continue
        sites = list(spec["sites"])
        if pack in geo_sites:
            sites = list(geo_sites[pack]) + sites
        if sites:
            add(f"q-{pack}-sites", spec["label"] + " site pack", pack, f"{phrase} {site_or(sites[:6])}")
        for ft in spec["filetypes"][:2]:
            add(f"q-{pack}-{ft}", f"{spec['label']} filetype:{ft}", pack, f"{phrase} filetype:{ft}")
        for extra in spec["extras"][:2]:
            if extra.endswith(":") and extra.split(":")[0] in {"author", "CPC", "assignee"}:
                continue  # operator stub without a value is not useful
            add(f"q-{pack}-x-{re.sub(r'[^a-z0-9]+', '', extra)[:16]}", spec["label"] + " extra", pack, f"{phrase} {extra}")

    # Scholar-style
    add("q-scholar", "Scholarly operators", "academic", f"{phrase} source:nature OR source:science filetype:pdf")
    add("q-review", "Reviews first", "academic", f"{phrase} (\"systematic review\" OR \"meta-analysis\" OR Cochrane)")
    add("q-data", "Datasets", "government", f"{phrase} (dataset OR \"microdata\" OR filetype:csv OR filetype:xlsx)")
    add("q-primary", "Primary documents", "docs", f"{phrase} (legislation OR judgment OR \"technical report\" OR RFC) filetype:pdf")

    if after:
        add("q-since", "Recency (since:)", "web", f"{phrase} since:{after}")

    # Dedup by query string
    seen = set()
    unique = []
    for v in variants:
        key = v["query"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(v)
        if len(unique) >= limit:
            break
    return unique


def format_text(payload: Dict[str, Any]) -> str:
    lines = [
        "=" * 72,
        "EXPANDED SEARCH QUERIES",
        "=" * 72,
        f"Seed: {payload['seed']}",
        f"Geo:  {payload['geo']}    Packs: {', '.join(payload['packs'])}",
        f"n={payload['count']}   after={payload.get('after') or '—'}",
        "",
    ]
    for v in payload["queries"]:
        lines.append(f"[{v['id']:22} {v['pack']:11}] {v['purpose']}")
        lines.append(f"    {v['query']}")
        lines.append("")
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
        description="Expand a research question into boolean/site/filetype query variants.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python query_expander.py --query "four-day work week productivity RCT"
  python query_expander.py --query "adverse action disability" --pack legal --geo AU --after 2024-01-01
  python query_expander.py --query "vector database ANN recall" --pack academic --pack code --format json
""",
    )
    parser.add_argument("--query", "-q", required=True, help="Seed question or topic")
    parser.add_argument(
        "--pack",
        action="append",
        dest="packs",
        choices=sorted(PACKS),
        help="Repeatable source pack (default: web academic government news contrarian)",
    )
    parser.add_argument("--geo", default="GLOBAL", help="AU, US, UK, EU, GLOBAL")
    parser.add_argument("--after", help="Recency lower bound YYYY-MM-DD")
    parser.add_argument("--limit", type=int, default=24, help="Max queries to emit")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", "-o")
    args = parser.parse_args(argv)
    try:
        packs = args.packs or ["web", "academic", "government", "news", "contrarian"]
        queries = expand(args.query, packs, args.geo, args.after, args.limit)
        payload = {
            "skill": "deep-research",
            "artifact": "query_set",
            "generated_at": utc_now(),
            "seed": args.query,
            "geo": args.geo.upper(),
            "packs": packs,
            "after": args.after,
            "count": len(queries),
            "queries": queries,
            "notes": [
                "Deterministic expansion only — execute with your environment's web/search tools.",
                "Always pair a precision phrase query with a disconfirming query.",
                "site: packs are not exhaustive; add domain-specific hosts from the research plan.",
            ],
        }
        emit(payload, args.format, args.output)
        return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
