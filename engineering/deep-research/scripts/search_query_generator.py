#!/usr/bin/env python3
"""Generate diversified search-query sets for horizon scanning.

Produces direct, synonym, contradiction, academic, government, PDF,
recency, stakeholder, and dataset queries from a topic. Offline, no APIs.

Usage:
    python search_query_generator.py --topic "agentic RAG evaluation" --domain scientific
    python search_query_generator.py --topic "gig economy classification" --domain legal --jurisdiction AU --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DOMAINS = (
    "general",
    "scientific",
    "legal",
    "policy",
    "market",
    "medical",
    "geopolitical",
    "technical",
)

SYNONYM_MAP = {
    "ai": ["artificial intelligence", "machine learning", "foundation model"],
    "rag": ["retrieval augmented generation", "retrieval-augmented generation", "grounded generation"],
    "agentic": ["autonomous agent", "multi-agent", "tool-using agent"],
    "employment": ["labour", "labor", "workplace", "industrial relations"],
    "regulation": ["rulemaking", "statutory instrument", "regulatory framework"],
    "climate": ["global warming", "greenhouse gas", "net zero"],
    "inflation": ["CPI", "price growth", "cost of living"],
    "misinformation": ["disinformation", "false claim", "rumor cascade"],
    "privacy": ["data protection", "GDPR", "personal information"],
    "security": ["cybersecurity", "infosec", "vulnerability"],
    "market": ["industry", "competitive landscape", "sector"],
    "efficacy": ["effectiveness", "clinical benefit", "treatment effect"],
}

CONTRADICTION_TEMPLATES = [
    '"{topic}" criticism OR limitations OR "failed to" OR "does not"',
    '"{topic}" debunked OR "contrary evidence" OR replication crisis',
    '"{topic}" vs OR versus OR "compared with" controversy',
    '"{topic}" overestimated OR "selection bias" OR confounders',
]

ACADEMIC_SITES = {
    "general": ["site:arxiv.org", "site:.edu", "site:scholar.google.com"],
    "scientific": ["site:arxiv.org", "site:nature.com", "site:science.org", "site:pubmed.ncbi.nlm.nih.gov"],
    "legal": ["site:ssrn.com", "site:scholar.google.com", "site:jstor.org"],
    "policy": ["site:oecd.org", "site:nber.org", "site:brookings.edu"],
    "market": ["site:ssrn.com", "site:hbr.org", "site:.edu"],
    "medical": ["site:pubmed.ncbi.nlm.nih.gov", "site:cochranelibrary.com", "site:who.int"],
    "geopolitical": ["site:jstor.org", "site:cfr.org", "site:sipri.org"],
    "technical": ["site:arxiv.org", "site:acm.org", "site:ieee.org", "site:usenix.org"],
}

GOV_SITES = {
    "general": ["site:.gov", "site:who.int", "site:un.org"],
    "scientific": ["site:nsf.gov", "site:nasa.gov", "site:.gov"],
    "legal": ["site:.gov", "site:legislation.gov.uk", "site:congress.gov"],
    "policy": ["site:.gov", "site:oecd.org", "site:worldbank.org"],
    "market": ["site:sec.gov", "site:census.gov", "site:bls.gov"],
    "medical": ["site:cdc.gov", "site:fda.gov", "site:nih.gov", "site:who.int"],
    "geopolitical": ["site:state.gov", "site:un.org", "site:europa.eu"],
    "technical": ["site:nist.gov", "site:cisa.gov", "site:.gov"],
}

JURISDICTION_SITES = {
    "AU": ["site:.gov.au", "site:austlii.edu.au", "site:abs.gov.au", "site:legislation.gov.au"],
    "UK": ["site:.gov.uk", "site:legislation.gov.uk", "site:ons.gov.uk"],
    "US": ["site:.gov", "site:congress.gov", "site:gao.gov"],
    "EU": ["site:europa.eu", "site:eur-lex.europa.eu", "site:ec.europa.eu"],
    "CA": ["site:.gc.ca", "site:statcan.gc.ca"],
    "NZ": ["site:.govt.nz", "site:legislation.govt.nz"],
    "IN": ["site:.gov.in", "site:indiacode.nic.in"],
    "SG": ["site:.gov.sg"],
}

STAKEHOLDERS = {
    "general": ["regulator", "industry group", "civil society", "academic critic"],
    "scientific": ["corresponding author", "replication team", "methods critic", "funding agency"],
    "legal": ["plaintiff", "respondent", "regulator", "bar association", "union", "employer group"],
    "policy": ["ministry", "opposition", "think tank left", "think tank right", "affected community"],
    "market": ["incumbent", "challenger", "customer review", "analyst", "former employee"],
    "medical": ["clinician society", "patient group", "regulator", "manufacturer", "independent trialist"],
    "geopolitical": ["government statement", "opposition", "IO", "local journalist", "diaspora"],
    "technical": ["vendor", "independent researcher", "CVE reporter", "large customer", "standards body"],
}

DATASET_HINTS = {
    "general": ["dataset", "open data", "statistics", "microdata"],
    "scientific": ["supplementary data", "replication package", "OSF", "dryad"],
    "legal": ["case law database", "decision record", "FOI release"],
    "policy": ["administrative data", "survey microdata", "budget papers"],
    "market": ["10-K", "filing", "market share table", "pricing page archive"],
    "medical": ["clinicaltrials.gov", "registry", "surveillance dataset"],
    "geopolitical": ["ACLED", "UCDP", "trade statistics"],
    "technical": ["benchmark", "telemetry", "CVE feed", "SPECint"],
}


def tokenize(topic: str) -> List[str]:
    return [t for t in re.split(r"[^a-z0-9]+", topic.lower()) if t]


def synonyms_for(topic: str) -> List[str]:
    tokens = tokenize(topic)
    extras: List[str] = []
    for token in tokens:
        extras.extend(SYNONYM_MAP.get(token, []))
    variants = []
    for extra in extras[:4]:
        swapped = topic
        for token in extra.split():
            if token.lower() in tokens:
                swapped = re.sub(rf"\b{re.escape(token)}\b", extra, topic, count=1, flags=re.I)
                break
        if swapped == topic:
            swapped = f"{topic} OR \"{extra}\""
        variants.append(swapped)
    if not variants:
        variants = [f'"{topic}" overview', f"{topic} explained OR primer"]
    return variants[:4]


def year_floor(as_of: datetime, recency_years: int) -> int:
    return as_of.year - recency_years


def generate(topic: str, domain: str, jurisdiction: Optional[str], as_of: datetime, recency_years: int) -> Dict[str, Any]:
    quoted = f'"{topic}"'
    syn = synonyms_for(topic)
    contradiction = [t.format(topic=topic) for t in CONTRADICTION_TEMPLATES]
    academic = [f"{quoted} {site}" for site in ACADEMIC_SITES[domain][:3]]
    gov_sites = list(GOV_SITES[domain])
    if jurisdiction and jurisdiction.upper() in JURISDICTION_SITES:
        gov_sites = JURISDICTION_SITES[jurisdiction.upper()] + gov_sites
    government = [f"{quoted} {site}" for site in gov_sites[:4]]
    pdfs = [
        f"{quoted} filetype:pdf",
        f"{topic} report filetype:pdf",
        f"{topic} methodology filetype:pdf",
    ]
    after = year_floor(as_of, recency_years)
    recency = [
        f"{quoted} after:{after}-01-01",
        f"{topic} {as_of.year} update OR revision OR latest",
        f"{topic} since:{after}",
    ]
    stakeholders = [f'"{topic}" "{who}"' for who in STAKEHOLDERS[domain]]
    datasets = [f"{topic} {hint}" for hint in DATASET_HINTS[domain]]
    multilingual = [
        f"{topic} (site:.cn OR site:.de OR site:.fr OR site:.jp) -inurl:translate",
        f"{topic} official English translation OR bilingual",
    ]
    queries = {
        "direct": [quoted, f"{topic} evidence", f"{topic} primary source"],
        "synonym": syn,
        "contradiction": contradiction,
        "site_academic": academic,
        "site_gov": government,
        "filetype_pdf": pdfs,
        "recency": recency,
        "stakeholder": stakeholders,
        "dataset": datasets,
        "multilingual": multilingual,
    }
    ordered = []
    for family, items in queries.items():
        for item in items:
            ordered.append({"family": family, "query": item})
    return {
        "topic": topic,
        "domain": domain,
        "jurisdiction": jurisdiction,
        "as_of": as_of.strftime("%Y-%m-%d"),
        "recency_years": recency_years,
        "query_count": len(ordered),
        "families": queries,
        "flat": ordered,
        "horizon_scan_batch": ordered[:8],
        "notes": [
            "Run families in parallel where the tool allows independent calls.",
            "Do not stop at page 1. Prefer government, academic, and primary-document hits.",
            "Contradiction queries are mandatory even when the user has a preferred answer.",
            "Treat social/search snippets as leads, not evidence.",
        ],
    }


def render_human(result: Dict[str, Any]) -> str:
    lines = [
        f"Topic:        {result['topic']}",
        f"Domain:       {result['domain']}",
        f"Jurisdiction: {result['jurisdiction'] or '(global)'}",
        f"As of:        {result['as_of']}",
        f"Queries:      {result['query_count']}",
        "",
    ]
    for family, items in result["families"].items():
        lines.append(f"[{family}]")
        for item in items:
            lines.append(f"  - {item}")
        lines.append("")
    lines.append("Notes:")
    for note in result["notes"]:
        lines.append(f"  - {note}")
    return "\n".join(lines)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate diversified search queries for deep-research horizon scans."
    )
    parser.add_argument("--topic", required=True)
    parser.add_argument("--domain", choices=DOMAINS, default="general")
    parser.add_argument("--jurisdiction", help="Optional ISO-ish pack: AU, UK, US, EU, CA, NZ, IN, SG")
    parser.add_argument("--as-of", dest="as_of", help="YYYY-MM-DD (default: today UTC)")
    parser.add_argument("--recency-years", type=int, default=2)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.as_of:
        try:
            as_of = datetime.strptime(args.as_of, "%Y-%m-%d")
        except ValueError:
            print("error: --as-of must be YYYY-MM-DD", file=sys.stderr)
            return 2
    else:
        as_of = datetime.now(timezone.utc).replace(tzinfo=None)
    result = generate(args.topic, args.domain, args.jurisdiction, as_of, args.recency_years)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_human(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
