#!/usr/bin/env python3
"""Score a research source against the 12-point credibility rubric.

Offline-first. Accepts CLI flags or a JSON object. Does not fetch URLs.
Outputs a 0-100 integrity score, credibility band, weaknesses, and
required corroboration. Matches references/source-evaluation-framework.md.

Usage:
    python source_scorer.py --title "ABS labour force" --type government --date 2026-02-01
    python source_scorer.py --input source.json --json
    python source_scorer.py --title "Blog post" --type blog --provenance 2 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

DIMENSIONS = [
    "provenance",
    "recency",
    "methodology",
    "corroboration",
    "conflicts",
    "framing",
    "evidential_weight",
    "counter_evidence",
    "reproducibility",
    "editorial",
    "perspective_diversity",
    "integrity_override",  # unused in weighted sum; informational
]

WEIGHTS = {
    "provenance": 1.2,
    "recency": 0.9,
    "methodology": 1.3,
    "corroboration": 1.3,
    "conflicts": 1.1,
    "framing": 0.8,
    "evidential_weight": 1.3,
    "counter_evidence": 1.0,
    "reproducibility": 1.0,
    "editorial": 0.9,
    "perspective_diversity": 0.7,
}

TYPE_PRIORS = {
    "primary_legal": {
        "provenance": 9, "methodology": 6, "conflicts": 8, "framing": 7,
        "evidential_weight": 9, "editorial": 8, "reproducibility": 8,
        "perspective_diversity": 4, "counter_evidence": 5, "corroboration": 6,
    },
    "government": {
        "provenance": 8, "methodology": 7, "conflicts": 7, "framing": 6,
        "evidential_weight": 8, "editorial": 8, "reproducibility": 7,
        "perspective_diversity": 4, "counter_evidence": 5, "corroboration": 6,
    },
    "peer_reviewed": {
        "provenance": 8, "methodology": 8, "conflicts": 6, "framing": 7,
        "evidential_weight": 8, "editorial": 9, "reproducibility": 7,
        "perspective_diversity": 5, "counter_evidence": 6, "corroboration": 6,
    },
    "dataset": {
        "provenance": 7, "methodology": 7, "conflicts": 6, "framing": 8,
        "evidential_weight": 8, "editorial": 6, "reproducibility": 8,
        "perspective_diversity": 4, "counter_evidence": 4, "corroboration": 5,
    },
    "ngo_thinktank": {
        "provenance": 6, "methodology": 5, "conflicts": 4, "framing": 5,
        "evidential_weight": 6, "editorial": 6, "reproducibility": 5,
        "perspective_diversity": 5, "counter_evidence": 4, "corroboration": 5,
    },
    "news": {
        "provenance": 5, "methodology": 4, "conflicts": 5, "framing": 5,
        "evidential_weight": 5, "editorial": 6, "reproducibility": 4,
        "perspective_diversity": 5, "counter_evidence": 4, "corroboration": 4,
    },
    "corporate": {
        "provenance": 5, "methodology": 4, "conflicts": 3, "framing": 4,
        "evidential_weight": 5, "editorial": 4, "reproducibility": 4,
        "perspective_diversity": 3, "counter_evidence": 3, "corroboration": 4,
    },
    "preprint": {
        "provenance": 5, "methodology": 7, "conflicts": 6, "framing": 6,
        "evidential_weight": 6, "editorial": 4, "reproducibility": 6,
        "perspective_diversity": 5, "counter_evidence": 5, "corroboration": 3,
    },
    "trade_press": {
        "provenance": 4, "methodology": 3, "conflicts": 4, "framing": 4,
        "evidential_weight": 4, "editorial": 5, "reproducibility": 3,
        "perspective_diversity": 4, "counter_evidence": 3, "corroboration": 3,
    },
    "blog": {
        "provenance": 3, "methodology": 2, "conflicts": 3, "framing": 3,
        "evidential_weight": 3, "editorial": 2, "reproducibility": 2,
        "perspective_diversity": 4, "counter_evidence": 2, "corroboration": 2,
    },
    "social": {
        "provenance": 2, "methodology": 1, "conflicts": 2, "framing": 2,
        "evidential_weight": 2, "editorial": 1, "reproducibility": 1,
        "perspective_diversity": 6, "counter_evidence": 1, "corroboration": 1,
    },
    "unknown": {
        "provenance": 4, "methodology": 4, "conflicts": 4, "framing": 4,
        "evidential_weight": 4, "editorial": 4, "reproducibility": 4,
        "perspective_diversity": 4, "counter_evidence": 4, "corroboration": 4,
    },
}

RED_FLAG_DEDUCTIONS = {
    "retracted": ("provenance", 6, "Retracted or expression of concern"),
    "predatory": ("editorial", 7, "Predatory or pay-to-publish venue"),
    "undisclosed_funding": ("conflicts", 5, "Funding or conflicts not disclosed"),
    "anonymous": ("provenance", 4, "Anonymous or unauditable authorship"),
    "paywalled_unverified": ("reproducibility", 3, "Paywalled and not independently verified"),
    "single_anecdote": ("evidential_weight", 5, "Single anecdote presented as general fact"),
    "loaded_language": ("framing", 3, "Loaded or advocacy framing"),
    "no_methods": ("methodology", 4, "No methods, sample, or data description"),
    "circular_citation": ("corroboration", 4, "Cites only itself or a closed citation ring"),
}

BANDS = [
    (85, "High"),
    (70, "Medium-High"),
    (55, "Medium"),
    (40, "Medium-Low"),
    (0, "Low"),
]


def clamp(value: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def recency_score(pub_date: Optional[datetime], as_of: datetime, half_life_days: int) -> float:
    if pub_date is None:
        return 5.0
    age_days = max(0, (as_of - pub_date).days)
    if age_days <= 90:
        return 10.0
    if age_days <= 365:
        return 8.5
    ratio = age_days / float(half_life_days)
    score = 8.0 - (ratio * 3.0)
    return clamp(score)


def infer_type_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    host = urlparse(url).netloc.lower()
    path = urlparse(url).path.lower()
    if host.endswith(".gov") or host.endswith(".gov.au") or host.endswith(".gov.uk"):
        return "government"
    if "arxiv.org" in host or "biorxiv" in host or "medrxiv" in host:
        return "preprint"
    if "pubmed" in host or "doi.org" in host or "nature.com" in host or "science.org" in host:
        return "peer_reviewed"
    if host.endswith(".edu") or "scholar" in host:
        return "peer_reviewed"
    if any(x in host for x in ("twitter.com", "x.com", "reddit.com", "facebook.com")):
        return "social"
    if path.endswith(".pdf") and ("legislation" in path or "judgment" in path or "act" in path):
        return "primary_legal"
    return None


def band_for(score: float) -> str:
    for threshold, name in BANDS:
        if score >= threshold:
            return name
    return "Low"


def corroboration_requirement(band: str, pivotal: bool) -> str:
    table = {
        "High": "No extra corroboration required for background; still require 1 independent source if the claim is pivotal.",
        "Medium-High": "Require 1 independent high/medium-integrity source before treating as established.",
        "Medium": "Require 2 independent sources; do not let this source carry a pivotal claim alone.",
        "Medium-Low": "Treat as narrative or hypothesis only. Need 2 high-integrity independents before any factual use.",
        "Low": "Illustrative only. Never use as sole evidence of a fact. Quote as a claim-about-a-claim.",
    }
    base = table[band]
    if pivotal and band in ("Medium", "Medium-Low", "Low"):
        return base + " Pivotal-claim flag is set: verification loop is mandatory."
    return base


def apply_red_flags(scores: Dict[str, float], flags: List[str]) -> List[str]:
    notes = []
    for flag in flags:
        if flag not in RED_FLAG_DEDUCTIONS:
            notes.append(f"Unknown red flag ignored: {flag}")
            continue
        dim, deduct, reason = RED_FLAG_DEDUCTIONS[flag]
        scores[dim] = clamp(scores[dim] - deduct)
        notes.append(reason)
    return notes


def weighted_score(scores: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    total = 0.0
    weight_sum = 0.0
    contrib = {}
    for dim, weight in WEIGHTS.items():
        value = clamp(scores.get(dim, 4.0))
        contrib[dim] = round(value * weight, 2)
        total += value * weight
        weight_sum += 10.0 * weight
    return round((total / weight_sum) * 100.0, 1), contrib


def weaknesses(scores: Dict[str, float]) -> List[Dict[str, Any]]:
    items = []
    for dim, value in scores.items():
        if dim == "integrity_override":
            continue
        if value <= 4:
            items.append({
                "dimension": dim,
                "score": value,
                "severity": "critical" if value <= 2 else "high",
                "note": f"{dim.replace('_', ' ')} is weak ({value}/10)",
            })
        elif value <= 6:
            items.append({
                "dimension": dim,
                "score": value,
                "severity": "moderate",
                "note": f"{dim.replace('_', ' ')} is only moderate ({value}/10)",
            })
    items.sort(key=lambda x: x["score"])
    return items


def allowed_uses(band: str) -> List[str]:
    mapping = {
        "High": ["anchor_source", "pivotal_claim_support", "quantitative_citation", "primary_extract"],
        "Medium-High": ["anchor_source", "supporting_citation", "triangulation_leg"],
        "Medium": ["supporting_citation", "context", "stakeholder_view"],
        "Medium-Low": ["narrative_illustration", "hypothesis_generation"],
        "Low": ["narrative_illustration"],
    }
    return mapping[band]


def load_input(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object")
    return data


def build_scores(args: argparse.Namespace, payload: Dict[str, Any]) -> Tuple[Dict[str, float], str]:
    source_type = (payload.get("type") or args.type or "unknown").lower().replace("-", "_")
    if source_type not in TYPE_PRIORS:
        source_type = "unknown"
    url = payload.get("url") or args.url or ""
    inferred = infer_type_from_url(url)
    if inferred and (not payload.get("type") and args.type == "unknown"):
        source_type = inferred
    scores = dict(TYPE_PRIORS[source_type])

    as_of = parse_date(payload.get("as_of") or args.as_of) or datetime.now(timezone.utc).replace(tzinfo=None)
    pub = parse_date(payload.get("date") or args.date)
    half_life = int(payload.get("half_life_days") or args.half_life_days)
    scores["recency"] = recency_score(pub, as_of, half_life)

    provided = payload.get("scores") or {}
    for dim in WEIGHTS:
        cli_val = getattr(args, dim, None)
        if dim in provided and provided[dim] is not None:
            scores[dim] = clamp(float(provided[dim]))
        elif cli_val is not None:
            scores[dim] = clamp(float(cli_val))

    if args.peer_reviewed or payload.get("peer_reviewed"):
        scores["editorial"] = max(scores["editorial"], 8)
        scores["methodology"] = max(scores["methodology"], 6)
    if args.open_data or payload.get("open_data"):
        scores["reproducibility"] = min(10, scores["reproducibility"] + 2)
    if args.discloses_funding or payload.get("discloses_funding"):
        scores["conflicts"] = min(10, scores["conflicts"] + 1.5)
    return scores, source_type


def evaluate(args: argparse.Namespace) -> Dict[str, Any]:
    payload = load_input(args.input) if args.input else {}
    scores, source_type = build_scores(args, payload)
    flags = list(args.red_flag or [])
    flags.extend(payload.get("red_flags") or [])
    flag_notes = apply_red_flags(scores, flags)

    overall, contrib = weighted_score(scores)
    band = band_for(overall)
    title = payload.get("title") or args.title or "(untitled)"
    url = payload.get("url") or args.url or ""
    result = {
        "title": title,
        "url": url,
        "type": source_type,
        "date": payload.get("date") or args.date,
        "overall_score": overall,
        "band": band,
        "dimension_scores": {k: round(v, 2) for k, v in scores.items()},
        "weighted_contributions": contrib,
        "weaknesses": weaknesses(scores),
        "red_flags": flag_notes,
        "required_corroboration": corroboration_requirement(band, args.pivotal or payload.get("pivotal", False)),
        "allowed_uses": allowed_uses(band),
        "justification": (
            f"{band} integrity ({overall}/100) as a {source_type} source. "
            f"Weakest dimensions: "
            + ", ".join(w["dimension"] for w in weaknesses(scores)[:3])
            if weaknesses(scores) else f"{band} integrity ({overall}/100); no critical dimension gaps."
        ),
        "offline": True,
        "fetched": False,
    }
    if url:
        parsed = urlparse(url)
        result["url_well_formed"] = bool(parsed.scheme in ("http", "https") and parsed.netloc)
    else:
        result["url_well_formed"] = None
    return result


def render_human(result: Dict[str, Any]) -> str:
    lines = [
        f"Source: {result['title']}",
        f"Type:   {result['type']}",
        f"URL:    {result['url'] or '(none)'}",
        f"Date:   {result['date'] or '(unknown)'}",
        f"Score:  {result['overall_score']}/100  Band: {result['band']}",
        "",
        "Dimension scores (0-10):",
    ]
    for dim, value in result["dimension_scores"].items():
        lines.append(f"  {dim:24} {value:>5}")
    lines.append("")
    lines.append("Weaknesses:")
    if not result["weaknesses"]:
        lines.append("  none above moderate")
    else:
        for item in result["weaknesses"]:
            lines.append(f"  [{item['severity']}] {item['note']}")
    if result["red_flags"]:
        lines.append("Red flags applied:")
        for note in result["red_flags"]:
            lines.append(f"  - {note}")
    lines.append("")
    lines.append("Required corroboration:")
    lines.append(f"  {result['required_corroboration']}")
    lines.append("Allowed uses: " + ", ".join(result["allowed_uses"]))
    lines.append("")
    lines.append("Justification: " + result["justification"])
    return "\n".join(lines)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score a source on the 12-point deep-research credibility rubric (offline)."
    )
    parser.add_argument("--input", help="JSON file with title/url/type/date/scores/red_flags")
    parser.add_argument("--title")
    parser.add_argument("--url")
    parser.add_argument("--date", help="Publication date YYYY-MM-DD, YYYY-MM, or YYYY")
    parser.add_argument("--as-of", dest="as_of", help="Scoring date (default: now UTC)")
    parser.add_argument(
        "--type",
        default="unknown",
        choices=sorted(TYPE_PRIORS.keys()),
        help="Source type prior (overridden by --input.type)",
    )
    parser.add_argument("--half-life-days", type=int, default=730, help="Recency half-life. Default 730.")
    parser.add_argument("--pivotal", action="store_true", help="Mark as carrying a pivotal claim")
    parser.add_argument("--peer-reviewed", action="store_true")
    parser.add_argument("--open-data", action="store_true")
    parser.add_argument("--discloses-funding", action="store_true")
    parser.add_argument(
        "--red-flag",
        action="append",
        choices=sorted(RED_FLAG_DEDUCTIONS.keys()),
        help="Repeatable. Deducts from matching dimensions.",
    )
    for dim in WEIGHTS:
        parser.add_argument(f"--{dim.replace('_', '-')}", type=float, dest=dim, metavar="0-10")
    parser.add_argument("--json", action="store_true", help="JSON output")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        result = evaluate(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_human(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
