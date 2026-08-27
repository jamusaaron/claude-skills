#!/usr/bin/env python3
"""Score source credibility with a 12-point research integrity rubric.

Auto-scores from URL, dates, and metadata flags; optional explicit dimension
overrides. Standard library only.

Usage:
    python source_credibility.py sources.json --as-of 2026-08-27
    python source_credibility.py sources.json --format json --min-integrity medium
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


DIMENSIONS = [
    ("provenance", "Provenance & authority"),
    ("recency", "Recency & relevance"),
    ("methods", "Methodological transparency"),
    ("corroboration", "Corroboration / independent replication"),
    ("funding", "Funding & conflicts"),
    ("framing", "Framing & language"),
    ("weight", "Evidential weight"),
    ("counter", "Counter-evidence handling"),
    ("access", "Accessibility & reproducibility"),
    ("review", "Peer review & editorial standards"),
    ("diversity", "Diversity of perspective"),
    ("integrity_self", "Self-reported caveats / limitations"),
]

INTEGRITY_BANDS = [
    (4.4, "High"),
    (3.6, "Medium-High"),
    (2.8, "Medium"),
    (2.0, "Medium-Low"),
    (0.0, "Low"),
]

GOV_SUFFIXES = (".gov", ".gov.au", ".gov.uk", ".europa.eu", ".int")
EDU_SUFFIXES = (".edu", ".ac.uk", ".ac.nz", ".edu.au")

LOADED_TERMS = {
    "shocking", "destroyed", "exposed", "wake up", "they don't want",
    "miracle", "secret", "hoax", "scam", "elites", "sheeple",
    "unprecedented disaster", "silver bullet",
}

PREDATORY_FLAGS = {"predatory", "hijacked journal", "unsolicited special issue"}


def parse_as_of(value: Optional[str]) -> date:
    if not value:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value)[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def host_class(url: str) -> str:
    host = urlparse(url or "").netloc.lower().lstrip("www.")
    if not host:
        return "unknown"
    if host.endswith(GOV_SUFFIXES) or host.endswith(".gov"):
        return "government"
    if host.endswith(EDU_SUFFIXES):
        return "academic"
    if any(host.endswith(s) for s in (".org", ".ngo")):
        return "ngo"
    if any(token in host for token in ("arxiv.org", "ssrn.com", "nber.org", "who.int", "oecd.org", "worldbank.org")):
        return "research_org"
    if any(token in host for token in ("nytimes.", "ft.com", "wsj.", "reuters.", "apnews.", "bbc.", "economist.")):
        return "quality_news"
    if any(token in host for token in ("medium.com", "substack.com", "wordpress.", "blogspot.")):
        return "blog"
    if any(token in host for token in ("twitter.", "x.com", "tiktok.", "reddit.", "facebook.")):
        return "social"
    return "other"


def clamp(score: float) -> float:
    return max(0.0, min(5.0, score))


def auto_dimensions(source: Dict[str, Any], as_of: date) -> Dict[str, float]:
    url = str(source.get("url") or "")
    hclass = host_class(url)
    stype = str(source.get("type") or source.get("source_type") or hclass).lower()
    peer = bool(source.get("peer_reviewed"))
    preprint = bool(source.get("preprint"))
    methods = str(source.get("methodology") or source.get("methods") or "")
    limitations = str(source.get("limitations") or "")
    funding = str(source.get("funding") or "")
    conflict = str(source.get("conflicts") or source.get("conflict_of_interest") or "")
    excerpt = " ".join([
        str(source.get("title") or ""),
        str(source.get("excerpt") or ""),
        str(source.get("notes") or ""),
    ]).lower()
    pub = parse_date(source.get("date") or source.get("published"))
    independent = int(source.get("independent_corroborations") or 0)
    sample = source.get("sample_size")
    open_data = bool(source.get("open_data") or source.get("reproducible"))
    engages_counter = bool(source.get("engages_counter_evidence"))
    unique_view = bool(source.get("unique_perspective"))
    retracted = bool(source.get("retracted") or any(f in excerpt for f in PREDATORY_FLAGS))

    provenance = 2.5
    if hclass in {"government", "academic", "research_org"}:
        provenance = 4.4
    elif hclass == "quality_news":
        provenance = 3.6
    elif hclass == "ngo":
        provenance = 3.2
    elif hclass == "blog":
        provenance = 1.8
    elif hclass == "social":
        provenance = 1.2
    if peer:
        provenance = max(provenance, 4.2)
    if retracted:
        provenance = min(provenance, 0.5)
    if source.get("author_expertise") == "high":
        provenance = min(5.0, provenance + 0.4)

    recency = 3.0
    if pub:
        age_days = (as_of - pub).days
        if age_days < 0:
            recency = 3.5  # dated in the future relative to as-of; treat cautiously
        elif age_days <= 365:
            recency = 4.8
        elif age_days <= 365 * 3:
            recency = 4.0
        elif age_days <= 365 * 8:
            recency = 3.0
        else:
            recency = 2.0
        if source.get("foundational"):
            recency = max(recency, 3.2)

    methods_score = 1.5
    if len(methods) > 80 or source.get("has_methods"):
        methods_score = 3.8
    if sample:
        try:
            if int(sample) >= 100:
                methods_score = max(methods_score, 4.0)
        except (TypeError, ValueError):
            pass
    if peer:
        methods_score = max(methods_score, 3.5)
    if preprint and not peer:
        methods_score = min(methods_score, 3.0)

    corroboration = 1.5 + min(3.0, independent * 1.0)
    if source.get("meta_analysis"):
        corroboration = max(corroboration, 4.2)

    funding_score = 3.0
    if funding and "undisclosed" not in funding.lower():
        funding_score = 3.8
    if conflict and any(w in conflict.lower() for w in ("industry", "paid", "sponsor")):
        funding_score = 2.2
    if source.get("conflict_undisclosed"):
        funding_score = 1.0
    if stype in {"government", "academic"} and not conflict:
        funding_score = max(funding_score, 3.5)

    framing = 3.5
    hits = sum(1 for term in LOADED_TERMS if term in excerpt)
    framing = clamp(4.2 - hits * 1.2)
    if source.get("opinion") or stype in {"blog", "social"}:
        framing = min(framing, 2.5)

    weight = 2.0
    if stype in {"government", "academic", "statistics", "legal"}:
        weight = 4.0
    if source.get("primary"):
        weight = max(weight, 4.3)
    if source.get("anecdote"):
        weight = min(weight, 1.8)
    if sample:
        try:
            if int(sample) >= 1000:
                weight = max(weight, 4.2)
        except (TypeError, ValueError):
            pass

    counter = 2.5 if engages_counter or "limitation" in limitations.lower() else 1.8
    if "no limitations" in excerpt:
        counter = 1.5
    if limitations:
        counter = max(counter, 3.4)

    access = 3.2 if url else 1.5
    if open_data:
        access = max(access, 4.4)
    if source.get("paywalled") and not source.get("open_version"):
        access = min(access, 2.6)

    review = 1.5
    if peer:
        review = 4.4
    elif hclass == "government":
        review = 3.6
    elif hclass == "quality_news":
        review = 3.3
    elif preprint:
        review = 2.4
    if retracted:
        review = 0.4

    diversity = 3.0 if unique_view else 2.4
    if source.get("echo_chamber"):
        diversity = 1.6

    caveats = 3.6 if limitations else 2.2
    if source.get("overclaim"):
        caveats = 1.4

    scores = {
        "provenance": provenance,
        "recency": recency,
        "methods": methods_score,
        "corroboration": corroboration,
        "funding": funding_score,
        "framing": framing,
        "weight": weight,
        "counter": counter,
        "access": access,
        "review": review,
        "diversity": diversity,
        "integrity_self": caveats,
    }
    overrides = source.get("dimension_scores") or {}
    for key in scores:
        if key in overrides:
            try:
                scores[key] = clamp(float(overrides[key]))
            except (TypeError, ValueError):
                pass
    return {k: round(clamp(v), 2) for k, v in scores.items()}


def band_for(avg: float) -> str:
    for threshold, label in INTEGRITY_BANDS:
        if avg >= threshold:
            return label
    return "Low"


def justify(source: Dict[str, Any], scores: Dict[str, float], band: str) -> str:
    hclass = host_class(str(source.get("url") or ""))
    weak = sorted(scores.items(), key=lambda kv: kv[1])[:2]
    strong = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]
    title = source.get("title") or source.get("id") or "Untitled source"
    weak_txt = ", ".join(f"{k} {v:.1f}" for k, v in weak)
    strong_txt = ", ".join(f"{k} {v:.1f}" for k, v in strong)
    return (
        f"{title}: {band} integrity ({hclass or 'unclassified'} host). "
        f"Strongest: {strong_txt}. Weakest: {weak_txt}."
    )


def score_source(source: Dict[str, Any], as_of: date) -> Dict[str, Any]:
    dims = auto_dimensions(source, as_of)
    avg = sum(dims.values()) / len(dims)
    band = band_for(avg)
    usable = band not in {"Low"}
    return {
        "id": source.get("id") or source.get("url") or source.get("title"),
        "title": source.get("title"),
        "url": source.get("url"),
        "type": source.get("type") or host_class(str(source.get("url") or "")),
        "host_class": host_class(str(source.get("url") or "")),
        "date": source.get("date") or source.get("published"),
        "dimension_scores": dims,
        "average": round(avg, 2),
        "integrity": band,
        "usable_as_evidence": usable,
        "illustrative_only": band == "Low",
        "justification": justify(source, dims, band),
    }


def load_sources(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("sources") or data.get("items") or []
    if not isinstance(data, list):
        raise ValueError("Input must be a list of sources or an object with 'sources'.")
    return data


def format_text(results: List[Dict[str, Any]], as_of: str) -> str:
    lines = [
        "SOURCE CREDIBILITY SCORES",
        "=" * 72,
        f"As of: {as_of}   Sources: {len(results)}",
        "",
    ]
    for item in results:
        lines.append(
            f"[{item['integrity']:11}] {item['average']:4.2f}  "
            f"{item.get('id')}  — {item.get('title') or ''}"
        )
        lines.append(f"    {item['justification']}")
    counts: Dict[str, int] = {}
    for item in results:
        counts[item["integrity"]] = counts.get(item["integrity"], 0) + 1
    lines.append("")
    lines.append("Integrity mix: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score sources on a 12-point credibility / integrity rubric."
    )
    parser.add_argument("input_file", help="JSON file of sources")
    parser.add_argument("--as-of", dest="as_of", help="As-of date YYYY-MM-DD")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument(
        "--min-integrity",
        choices=["High", "Medium-High", "Medium", "Medium-Low", "Low"],
        help="Only include sources at or above this band",
    )
    return parser


BAND_RANK = {"High": 4, "Medium-High": 3, "Medium": 2, "Medium-Low": 1, "Low": 0}


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        as_of = parse_as_of(args.as_of)
        sources = load_sources(args.input_file)
        results = [score_source(src, as_of) for src in sources]
        results.sort(key=lambda r: r["average"], reverse=True)
        if args.min_integrity:
            min_rank = BAND_RANK[args.min_integrity]
            results = [r for r in results if BAND_RANK[r["integrity"]] >= min_rank]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    payload = {"as_of": as_of.isoformat(), "count": len(results), "sources": results}
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(format_text(results, as_of.isoformat()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
