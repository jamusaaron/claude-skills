#!/usr/bin/env python3
"""Heuristic bias audit for a research outline or report.

Scans markdown/text for loaded language, uncited assertions, single-source
clusters, missing perspective markers, and overconfident phrasing.
Offline. Recall-oriented: flags are candidates, not verdicts.

Usage:
    python bias_audit.py --input report.md
    python bias_audit.py --input report.md --domain legal --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

LOADED = {
    "alarming": "loaded",
    "devastating": "loaded",
    "slam dunk": "loaded",
    "obviously": "overconfident",
    "clearly": "overconfident",
    "undeniable": "overconfident",
    "everyone knows": "overconfident",
    "settled science": "overconfident",
    "nothingburger": "loaded",
    "so-called": "loaded",
    "regime": "loaded",
    "lamestream": "loaded",
    "woke": "loaded",
    "radical": "loaded",
    "elite": "loaded",
    "miracle": "loaded",
    "silver bullet": "loaded",
    "always": "absolutist",
    "never": "absolutist",
    "proves": "overconfident",
    "proof that": "overconfident",
    "no doubt": "overconfident",
    "beyond question": "overconfident",
}

WEASEL = (
    "some say", "critics argue", "it is said", "many believe", "experts claim",
    "studies show", "research suggests", "it is well known", "reportedly",
    "allegedly",  # alleged is fine in legal; still flag for missing citation
)

PERSPECTIVE_MARKERS = {
    "general": ["limitation", "uncertainty", "alternative", "counter", "however", "on the other hand"],
    "legal": ["respondent", "plaintiff", "regulator", "enforcement", "black-letter", "practice"],
    "medical": ["patient", "clinician", "regulator", "absolute risk", "harms", "subgroup"],
    "market": ["customer", "incumbent", "challenger", "pricing", "switching cost"],
    "scientific": ["replication", "confound", "null result", "methods", "conflict of interest"],
    "policy": ["incidence", "unintended", "implementation", "opposition", "affected community"],
    "geopolitical": ["local", "official statement", "opposition", "humanitarian"],
    "technical": ["failure mode", "benchmark", "vendor claim", "independent"],
}

CITATION_RE = re.compile(
    r"(\[[A-Z][A-Za-z0-9_-]{0,15}\]"
    r"|\(\s*[A-Z][A-Za-z\-]+,\s*\d{4}\s*\)"
    r"|https?://\S+"
    r"|\[\d+\]"
    r"|source\s+[A-Z0-9_-]+)",
    re.I,
)
URL_RE = re.compile(r"https?://[^\s)>\]]+")
SENTENCE_RE = re.compile(r"(?s)([^.!?\n]{20,}[.!?])")
ASSERTION_RE = re.compile(
    r"\b(\d+(\.\d+)?%|\bincreased\b|\bdecreased\b|\bcaused\b|\bproves\b|\bshows that\b|"
    r"\bis responsible\b|\bled to\b|\bfound that\b|\bthe evidence\b)",
    re.I,
)


def sentences(text: str) -> List[str]:
    found = [m.group(1).strip() for m in SENTENCE_RE.finditer(text)]
    return found or [line.strip() for line in text.splitlines() if len(line.strip()) > 20]


def scan_loaded(text: str) -> List[Dict[str, str]]:
    hits = []
    lower = text.lower()
    for phrase, kind in LOADED.items():
        if phrase in lower:
            hits.append({"phrase": phrase, "kind": kind})
    return hits


def scan_weasel(text: str) -> List[str]:
    lower = text.lower()
    return [w for w in WEASEL if w in lower]


def scan_uncited(text: str) -> List[Dict[str, str]]:
    flags = []
    for sent in sentences(text):
        if sent.lstrip().startswith(("#", ">", "|", "-", "*")):
            continue
        if ASSERTION_RE.search(sent) and not CITATION_RE.search(sent):
            flags.append({
                "issue": "uncited_assertion",
                "excerpt": sent[:240],
            })
    return flags[:40]


def scan_hosts(text: str) -> Dict[str, Any]:
    hosts = []
    for url in URL_RE.findall(text):
        host = urlparse(url).netloc.lower().lstrip("www.")
        if host:
            hosts.append(host)
    counts = Counter(hosts)
    total = sum(counts.values()) or 1
    clusters = [
        {"host": host, "count": n, "share": round(n / total, 3)}
        for host, n in counts.most_common(12)
    ]
    dominant = [c for c in clusters if c["share"] >= 0.4 and c["count"] >= 3]
    return {"unique_hosts": len(counts), "total_urls": sum(counts.values()), "clusters": clusters, "dominant": dominant}


def missing_perspectives(text: str, domain: str) -> List[str]:
    markers = PERSPECTIVE_MARKERS.get(domain, PERSPECTIVE_MARKERS["general"])
    lower = text.lower()
    return [m for m in markers if m not in lower]


def hedging_ratio(text: str) -> Dict[str, Any]:
    hedges = len(re.findall(r"\b(may|might|suggests|consistent with|uncertain|limited evidence)\b", text, re.I))
    certainties = len(re.findall(r"\b(proves|certainly|definitely|always|never|settled)\b", text, re.I))
    return {"hedge_hits": hedges, "certainty_hits": certainties, "overconfident": certainties > hedges and certainties >= 3}


def score(findings: Dict[str, Any]) -> Dict[str, Any]:
    deductions = 0
    deductions += min(20, 4 * len(findings["loaded_language"]))
    deductions += min(20, 3 * len(findings["uncited_assertions"]))
    deductions += min(15, 5 * len(findings["missing_perspectives"]))
    deductions += 15 if findings["source_clusters"]["dominant"] else 0
    deductions += 10 if findings["hedging"]["overconfident"] else 0
    deductions += min(10, 2 * len(findings["weasel"]))
    score_val = max(0, 100 - deductions)
    if score_val >= 80:
        band = "pass"
    elif score_val >= 60:
        band = "revise"
    else:
        band = "fail"
    return {"audit_score": score_val, "band": band, "deductions": deductions}


def audit(text: str, domain: str) -> Dict[str, Any]:
    findings = {
        "domain": domain,
        "char_count": len(text),
        "sentence_count": len(sentences(text)),
        "loaded_language": scan_loaded(text),
        "weasel": scan_weasel(text),
        "uncited_assertions": scan_uncited(text),
        "source_clusters": scan_hosts(text),
        "missing_perspectives": missing_perspectives(text, domain),
        "hedging": hedging_ratio(text),
    }
    findings["score"] = score(findings)
    findings["actions"] = actions(findings)
    findings["disclaimer"] = (
        "Heuristic scan only. Absence of a flag is not evidence of neutrality. "
        "Apply references/bias-and-adversarial-analysis.md before clearing."
    )
    return findings


def actions(findings: Dict[str, Any]) -> List[str]:
    acts = []
    if findings["loaded_language"]:
        acts.append("Replace loaded terms with operational language; steelman the opposing frame.")
    if findings["uncited_assertions"]:
        acts.append("Attach claim IDs or URLs to every quantitative or causal sentence.")
    if findings["source_clusters"]["dominant"]:
        acts.append("Break the dominant host cluster; add a second provenance family.")
    if findings["missing_perspectives"]:
        acts.append("Add missing perspective markers: " + ", ".join(findings["missing_perspectives"][:5]))
    if findings["hedging"]["overconfident"]:
        acts.append("Downgrade certainty language; run confidence_calibrator.py on pivotal claims.")
    if findings["weasel"]:
        acts.append("Replace weasel collectives ('studies show') with named sources.")
    if not acts:
        acts.append("No high-priority heuristic flags. Still run the human red-team checklist.")
    return acts


def render_human(result: Dict[str, Any]) -> str:
    s = result["score"]
    lines = [
        f"Bias audit: {s['audit_score']}/100 ({s['band']})",
        f"Domain: {result['domain']}  Sentences: {result['sentence_count']}",
        "",
        f"Loaded/overconfident phrases: {len(result['loaded_language'])}",
    ]
    for hit in result["loaded_language"][:12]:
        lines.append(f"  - {hit['phrase']} ({hit['kind']})")
    lines.append(f"Weasel: {', '.join(result['weasel']) or 'none'}")
    lines.append(f"Uncited assertions: {len(result['uncited_assertions'])}")
    for item in result["uncited_assertions"][:8]:
        lines.append(f"  - {item['excerpt']}")
    sc = result["source_clusters"]
    lines.append(f"URL hosts: {sc['unique_hosts']} unique / {sc['total_urls']} total")
    for c in sc["dominant"]:
        lines.append(f"  DOMINANT {c['host']} {c['share']*100:.0f}% ({c['count']})")
    lines.append("Missing perspective markers: " + (", ".join(result["missing_perspectives"]) or "none"))
    lines.append("")
    lines.append("Actions:")
    for a in result["actions"]:
        lines.append(f"  - {a}")
    lines.append("")
    lines.append(result["disclaimer"])
    return "\n".join(lines)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Heuristic bias audit of a research markdown file.")
    parser.add_argument("--input", required=True, help="Path to markdown or text")
    parser.add_argument("--domain", default="general",
                        choices=["general", "legal", "medical", "market", "scientific", "policy", "geopolitical", "technical"])
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        with open(args.input, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    result = audit(text, args.domain)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_human(result))
    return 0 if result["score"]["band"] != "fail" else 1


if __name__ == "__main__":
    sys.exit(main())
