#!/usr/bin/env python3
"""Source credibility and evidence-quality scorer.

Applies a 12-dimension rubric (provenance, recency, methods, corroboration,
funding, framing, evidential weight, counter-evidence handling, reproducibility,
peer review, perspective diversity, overall integrity) to source records.

Deterministic heuristics from URL, dates, source_type, and metadata — no network
and no LLM calls.

Usage:
    python source_scorer.py --input sources.json
    python source_scorer.py --url https://abs.gov.au/report --title "..." --published 2025-06-01
    python source_scorer.py --input store.jsonl --as-of 2026-08-27 --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse


DIMENSIONS = [
    "provenance",
    "recency",
    "methodology",
    "corroboration",
    "funding",
    "framing",
    "evidential_weight",
    "counter_evidence",
    "reproducibility",
    "peer_review",
    "perspective_diversity",
    "integrity",
]

WEIGHTS = {
    "provenance": 1.2,
    "recency": 1.0,
    "methodology": 1.3,
    "corroboration": 1.1,
    "funding": 1.0,
    "framing": 0.8,
    "evidential_weight": 1.2,
    "counter_evidence": 0.9,
    "reproducibility": 0.9,
    "peer_review": 1.1,
    "perspective_diversity": 0.5,
    "integrity": 0.4,
}

GOV_TLDS = (
    ".gov", ".gov.au", ".gov.uk", ".govt.nz", ".gc.ca", ".europa.eu",
    ".mil", ".fed.us",
)
EDU_TLDS = (".edu", ".ac.uk", ".ac.nz", ".edu.au", ".ac.jp")
PREPRINT_HOSTS = (
    "arxiv.org", "ssrn.com", "biorxiv.org", "medrxiv.org", "osf.io", "zenodo.org",
    "researchsquare.com", "preprints.org",
)
SCHOLAR_HOSTS = (
    "nature.com", "science.org", "nejm.org", "thelancet.com", "cell.com",
    "pnas.org", "springer.com", "wiley.com", "tandfonline.com", "oup.com",
    "acm.org", "ieee.org", "jstor.org", "nih.gov", "pubmed.ncbi.nlm.nih.gov",
    "who.int", "oecd.org", "nber.org", "bmj.com", "jamanetwork.com",
)
STATS_HOSTS = (
    "abs.gov.au", "ons.gov.uk", "census.gov", "bls.gov", "eurostat.ec.europa.eu",
    "stats.govt.nz", "statcan.gc.ca", "worldbank.org", "imf.org", "ourworldindata.org",
)
REGULATOR_HOSTS = (
    "sec.gov", "asic.gov.au", "fairwork.gov.au", "fwc.gov.au", "fda.gov",
    "ema.europa.eu", "ftc.gov", "cfpb.gov", "gao.gov", "ico.org.uk",
)
QUALITY_NEWS = (
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "economist.com",
    "ft.com", "wsj.com", "nytimes.com", "washingtonpost.com", "abc.net.au",
    "theguardian.com", "npr.org", "propublica.org",
)
LOW_HOSTS = (
    "medium.com", "substack.com", "wordpress.com", "blogspot.com", "tumblr.com",
    "reddit.com", "quora.com", "wikipedia.org", "facebook.com", "twitter.com",
    "x.com", "tiktok.com", "youtube.com", "linkedin.com",
)
LOADED_TERMS = (
    "shocking", "destroyed", "slaughtered", "miracle", "secret", "they don't want",
    "woke", "radical", "hoax", "scam", "must-read", "unbelievable", "proof that",
    "debunked forever", "scientists hate", "the truth about",
)
METHOD_TERMS = (
    "sample", "n=", "confidence interval", "p-value", "methodology", "limitations",
    "preregister", "randomi", "control group", "effect size", "open data",
    "replication", "systematic review", "meta-analysis",
)
FUNDING_TERMS = ("funded by", "conflict of interest", "disclosure", "sponsor", "grant")
COUNTER_TERMS = ("however", "limitation", "contrary", "failed to replicate", "caveat", "uncertainty")

BANDS = [
    (85, "high"),
    (70, "medium-high"),
    (55, "medium"),
    (40, "medium-low"),
    (0, "low"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    for fmt, n in (("%Y-%m-%d", 10), ("%Y/%m/%d", 10), ("%Y-%m", 7), ("%Y", 4)):
        try:
            dt = datetime.strptime(text[:n], fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    match = re.search(r"(20\d{2}|19\d{2})", str(value))
    if match:
        return datetime(int(match.group(1)), 1, 1, tzinfo=timezone.utc)
    return None


def host_of(url: str) -> str:
    if not url:
        return ""
    raw = url if "://" in url else "https://" + url
    try:
        host = urlparse(raw).netloc.lower()
    except ValueError:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def load_records(path: str) -> List[Dict[str, Any]]:
    text = open(path, "r", encoding="utf-8").read().strip()
    if not text:
        return []
    if path.endswith(".jsonl"):
        recs = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            recs.append(json.loads(line))
        return recs
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("sources", "records", "items", "evidence"):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]
    raise ValueError("Unsupported JSON shape")


def score_provenance(rec: Dict[str, Any]) -> Tuple[float, str]:
    host = host_of(rec.get("url") or rec.get("doi") or "")
    stype = (rec.get("source_type") or rec.get("type") or "").lower()
    if any(host.endswith(t) or host.endswith(t.lstrip(".")) for t in GOV_TLDS) or host in REGULATOR_HOSTS or host in STATS_HOSTS:
        return 9.4, "Government / official statistics or regulator domain"
    if any(host.endswith(t.lstrip(".")) or host.endswith(t) for t in EDU_TLDS) or host in SCHOLAR_HOSTS:
        return 8.6, "Academic / scholarly publisher"
    if stype in {"primary", "legislation", "judgment", "filing", "dataset"}:
        return 8.8, f"Declared primary source type: {stype}"
    if host in PREPRINT_HOSTS or stype == "preprint":
        return 6.2, "Preprint server — not peer reviewed by default"
    if host in QUALITY_NEWS or stype in {"news", "journalism"}:
        return 6.8, "Established newsroom (still secondary)"
    if host in LOW_HOSTS or stype in {"blog", "social", "forum"}:
        return 3.2, "User-generated or weakly edited venue"
    if host.endswith(".org"):
        return 6.0, "Generic .org — treat as advocacy until proven otherwise"
    return 5.0, "Unclassified host; default mid score pending metadata"


def score_recency(rec: Dict[str, Any], as_of: datetime) -> Tuple[float, str]:
    published = parse_date(rec.get("published") or rec.get("date") or rec.get("year"))
    if not published:
        return 4.5, "No publication date — recency unknown"
    days = max(0, (as_of - published).days)
    years = days / 365.25
    foundational = bool(rec.get("foundational"))
    if years <= 1:
        return 9.5, f"Published {published.date()} (≤1y)"
    if years <= 3:
        return 8.2, f"Published {published.date()} (≤3y)"
    if years <= 7:
        score = 6.5 if not foundational else 7.8
        return score, f"Published {published.date()} ({years:.1f}y){' — marked foundational' if foundational else ''}"
    if foundational:
        return 6.4, f"Older foundational source ({published.date()})"
    return 3.4, f"Stale for a current-state claim ({published.date()})"


def blob(rec: Dict[str, Any]) -> str:
    parts = [
        rec.get("title") or "",
        rec.get("abstract") or rec.get("summary") or "",
        rec.get("notes") or "",
        " ".join(rec.get("quotes") or []) if isinstance(rec.get("quotes"), list) else str(rec.get("quotes") or ""),
        rec.get("methodology") or "",
        rec.get("limitations") or "",
    ]
    return " ".join(str(p) for p in parts).lower()


def count_hits(text: str, terms: Iterable[str]) -> int:
    return sum(1 for t in terms if t in text)


def score_methodology(rec: Dict[str, Any]) -> Tuple[float, str]:
    text = blob(rec)
    hits = count_hits(text, METHOD_TERMS)
    declared = rec.get("methods_transparent")
    if declared is True or hits >= 4:
        return 8.7, f"Method signals present ({hits} terms) or declared transparent"
    if declared is False:
        return 3.0, "Methods marked non-transparent"
    if hits >= 2:
        return 6.8, f"Partial method signals ({hits})"
    stype = (rec.get("source_type") or "").lower()
    if stype in {"opinion", "blog", "social"}:
        return 2.5, "Opinion/social — little method to evaluate"
    return 4.8, "No method metadata; conservative mid-low score"


def score_corroboration(rec: Dict[str, Any]) -> Tuple[float, str]:
    n = rec.get("independent_corroborations")
    if isinstance(n, int):
        if n >= 2:
            return 8.8, f"{n} independent corroborations declared"
        if n == 1:
            return 6.5, "Single independent corroboration"
        return 3.5, "No independent corroboration declared"
    cites = rec.get("citations") or rec.get("outbound_citations")
    if isinstance(cites, list) and len(cites) >= 5:
        return 6.4, f"{len(cites)} outbound citations (not the same as independent replication)"
    return 5.0, "Corroboration not scored from network; default mid until matrix is built"


def score_funding(rec: Dict[str, Any]) -> Tuple[float, str]:
    text = blob(rec)
    coi = rec.get("conflict_of_interest")
    funded = rec.get("industry_funded")
    if coi is True or funded is True:
        return 3.8, "Conflict or industry funding declared — keep, but down-weight"
    if rec.get("funding_disclosed") is True or count_hits(text, FUNDING_TERMS) >= 1:
        return 7.5, "Funding/COI disclosure present"
    host = host_of(rec.get("url") or "")
    if host in STATS_HOSTS or any(host.endswith(t) for t in GOV_TLDS):
        return 8.0, "Public-sector producer; still check political framing"
    return 5.2, "Funding undisclosed"


def score_framing(rec: Dict[str, Any]) -> Tuple[float, str]:
    text = blob(rec) + " " + (rec.get("title") or "").lower()
    loaded = count_hits(text, LOADED_TERMS)
    if loaded >= 2:
        return 2.8, f"Loaded marketing/advocacy language ({loaded} hits)"
    if loaded == 1:
        return 4.6, "Some loaded language"
    if rec.get("source_type") in {"advocacy", "opinion", "blog"}:
        return 4.2, "Advocacy/opinion genre"
    return 7.4, "No obvious loaded-language flags"


def score_evidential_weight(rec: Dict[str, Any]) -> Tuple[float, str]:
    stype = (rec.get("source_type") or "").lower()
    mapping = {
        "meta-analysis": 9.4,
        "systematic-review": 9.0,
        "rct": 8.8,
        "dataset": 8.4,
        "primary": 8.2,
        "legislation": 8.6,
        "judgment": 8.5,
        "filing": 8.0,
        "government": 8.0,
        "observational": 6.8,
        "news": 5.6,
        "preprint": 5.8,
        "think-tank": 5.5,
        "opinion": 3.2,
        "social": 2.4,
        "blog": 3.0,
    }
    if stype in mapping:
        return mapping[stype], f"Type prior for '{stype}'"
    if rec.get("has_data") or rec.get("quantitative"):
        return 7.0, "Quantitative flag set"
    return 5.0, "Unspecified evidential class"


def score_counter(rec: Dict[str, Any]) -> Tuple[float, str]:
    text = blob(rec)
    hits = count_hits(text, COUNTER_TERMS)
    if rec.get("engages_counterevidence") is True or hits >= 3:
        return 8.0, "Engages limitations or counter-evidence"
    if rec.get("engages_counterevidence") is False:
        return 3.0, "Explicitly ignores counter-evidence"
    if hits == 0:
        return 4.4, "No limitation language detected"
    return 6.2, "Some caveat language"


def score_repro(rec: Dict[str, Any]) -> Tuple[float, str]:
    if rec.get("open_data") or rec.get("open_code") or rec.get("doi"):
        return 8.2, "DOI and/or open data/code flag"
    url = rec.get("url") or ""
    if url:
        return 6.0, "URL present — claims can be re-fetched"
    return 3.2, "No locator (URL/DOI) — poor audit trail"


def score_peer(rec: Dict[str, Any]) -> Tuple[float, str]:
    host = host_of(rec.get("url") or "")
    if rec.get("peer_reviewed") is True or host in SCHOLAR_HOSTS:
        return 8.8, "Peer-reviewed or major scholarly venue"
    if host in PREPRINT_HOSTS or rec.get("peer_reviewed") is False:
        return 4.0, "Not peer-reviewed"
    if host in QUALITY_NEWS:
        return 6.0, "Editorial standards, not peer review"
    if any(host.endswith(t) for t in GOV_TLDS) or host in STATS_HOSTS or host in REGULATOR_HOSTS:
        return 7.2, "Official production process (not academic peer review)"
    return 5.0, "Unknown editorial standard"


def score_diversity(rec: Dict[str, Any]) -> Tuple[float, str]:
    if rec.get("outlier"):
        return 8.0, "Marked as outlier / contrarian voice — useful for coverage, not weight"
    stance = (rec.get("stance") or rec.get("perspective") or "").lower()
    if stance in {"contrarian", "minority", "critical"}:
        return 7.2, f"Perspective: {stance}"
    return 5.5, "Mainstream or unspecified perspective"


def score_integrity(dim_scores: Dict[str, float]) -> Tuple[float, str]:
    core = (dim_scores["provenance"] + dim_scores["methodology"] + dim_scores["evidential_weight"]) / 3
    penalty = 0.0
    if dim_scores["framing"] < 4:
        penalty += 1.5
    if dim_scores["funding"] < 4:
        penalty += 1.0
    val = max(0.0, min(10.0, core - penalty))
    return val, "Composite of provenance/methods/weight with framing/funding penalties"


def band_for(score_100: float) -> str:
    for threshold, name in BANDS:
        if score_100 >= threshold:
            return name
    return "low"


def score_record(rec: Dict[str, Any], as_of: datetime) -> Dict[str, Any]:
    dims: Dict[str, Dict[str, Any]] = {}
    numeric: Dict[str, float] = {}

    def put(name: str, pair: Tuple[float, str]) -> None:
        numeric[name] = pair[0]
        dims[name] = {"score": round(pair[0], 2), "rationale": pair[1]}

    put("provenance", score_provenance(rec))
    put("recency", score_recency(rec, as_of))
    put("methodology", score_methodology(rec))
    put("corroboration", score_corroboration(rec))
    put("funding", score_funding(rec))
    put("framing", score_framing(rec))
    put("evidential_weight", score_evidential_weight(rec))
    put("counter_evidence", score_counter(rec))
    put("reproducibility", score_repro(rec))
    put("peer_review", score_peer(rec))
    put("perspective_diversity", score_diversity(rec))
    put("integrity", score_integrity(numeric))

    total_w = sum(WEIGHTS[k] for k in numeric)
    weighted = sum(numeric[k] * WEIGHTS[k] for k in numeric) / total_w
    score_100 = round(weighted * 10, 1)
    band = band_for(score_100)
    caveated = band in {"medium-low", "low"}
    return {
        "id": rec.get("id") or rec.get("url") or rec.get("title") or "unknown",
        "title": rec.get("title"),
        "url": rec.get("url"),
        "source_type": rec.get("source_type") or rec.get("type"),
        "host": host_of(rec.get("url") or ""),
        "score": score_100,
        "band": band,
        "use": (
            "illustrative only — do not treat as evidence"
            if band == "low"
            else "cite with credibility caveat"
            if caveated
            else "eligible as supporting/pivotal evidence"
        ),
        "dimensions": dims,
        "as_of": as_of.date().isoformat(),
    }


def format_text(payload: Dict[str, Any]) -> str:
    lines = [
        "=" * 72,
        "SOURCE CREDIBILITY SCORES",
        "=" * 72,
        f"Scored: {payload['generated_at']}   as_of={payload['as_of']}   n={payload['count']}",
        f"Mean score: {payload['summary']['mean_score']}   High+: {payload['summary']['high_or_better']}",
        "",
    ]
    for item in payload["results"]:
        lines.append(f"[{item['band'].upper():12} {item['score']:5.1f}] {item.get('title') or item['id']}")
        if item.get("url"):
            lines.append(f"    {item['url']}")
        lines.append(f"    Use: {item['use']}")
        top = sorted(item["dimensions"].items(), key=lambda kv: kv[1]["score"])
        worst = top[0]
        best = top[-1]
        lines.append(f"    Weakest: {worst[0]}={worst[1]['score']} ({worst[1]['rationale']})")
        lines.append(f"    Strongest: {best[0]}={best[1]['score']} ({best[1]['rationale']})")
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


def collect_records(args: argparse.Namespace) -> List[Dict[str, Any]]:
    recs: List[Dict[str, Any]] = []
    if args.input:
        recs.extend(load_records(args.input))
    if args.url or args.title:
        recs.append({
            "id": args.id or args.url or args.title,
            "url": args.url,
            "title": args.title,
            "published": args.published,
            "source_type": args.source_type,
            "peer_reviewed": args.peer_reviewed,
            "foundational": args.foundational,
        })
    if not recs:
        raise ValueError("Provide --input and/or --url/--title")
    return recs


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score source credibility with a 12-dimension research rubric.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python source_scorer.py --url https://abs.gov.au/statistics --title "Labour Force" --published 2026-01-01 --source-type government
  python source_scorer.py --input ../assets/sample_evidence_store.json --format json
""",
    )
    parser.add_argument("--input", "-i", help="JSON/JSONL of sources or an evidence store")
    parser.add_argument("--url", help="Single source URL")
    parser.add_argument("--title", help="Single source title")
    parser.add_argument("--id", help="Single source id")
    parser.add_argument("--published", help="Publication date")
    parser.add_argument("--source-type", dest="source_type", help="primary, government, news, preprint, ...")
    parser.add_argument("--peer-reviewed", dest="peer_reviewed", action="store_true")
    parser.add_argument("--foundational", action="store_true")
    parser.add_argument("--as-of", dest="as_of", help="Score recency relative to this date (YYYY-MM-DD)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", "-o")
    args = parser.parse_args(argv)
    try:
        as_of = parse_date(args.as_of) or datetime.now(timezone.utc)
        recs = collect_records(args)
        results = [score_record(r, as_of) for r in recs]
        scores = [r["score"] for r in results]
        payload = {
            "skill": "deep-research",
            "artifact": "source_scores",
            "generated_at": utc_now(),
            "as_of": as_of.date().isoformat(),
            "count": len(results),
            "summary": {
                "mean_score": round(sum(scores) / len(scores), 1) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "high_or_better": sum(1 for r in results if r["band"] in {"high", "medium-high"}),
                "low": sum(1 for r in results if r["band"] == "low"),
            },
            "results": results,
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
