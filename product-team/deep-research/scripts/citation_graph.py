#!/usr/bin/env python3
"""Build a citation / provenance graph from structured sources.

Detects hubs, isolated nodes, shared-lineage clusters, and circular citation
risk from explicit cites edges.

Usage:
    python citation_graph.py sources.json
    python citation_graph.py sources.json --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse


def load_sources(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("sources") or data.get("nodes") or []
    if not isinstance(data, list):
        raise ValueError("Expected a source list or object with 'sources'.")
    return data


def node_id(src: Dict[str, Any]) -> str:
    return str(src.get("id") or src.get("url") or src.get("title"))


def org_key(src: Dict[str, Any]) -> str:
    if src.get("organization") or src.get("lineage") or src.get("dataset"):
        return str(src.get("organization") or src.get("lineage") or src.get("dataset")).lower()
    host = urlparse(str(src.get("url") or "")).netloc.lower().lstrip("www.")
    return host or "unknown"


def edges_from(src: Dict[str, Any]) -> List[str]:
    raw = src.get("cites") or src.get("cites_ids") or src.get("references") or []
    if isinstance(raw, str):
        return [p.strip() for p in raw.split(",") if p.strip()]
    return [str(x) for x in raw]


def components(nodes: Set[str], adj: Dict[str, Set[str]]) -> List[List[str]]:
    remaining = set(nodes)
    groups: List[List[str]] = []
    while remaining:
        start = remaining.pop()
        q = deque([start])
        group = [start]
        seen = {start}
        while q:
            cur = q.popleft()
            for nxt in adj[cur]:
                if nxt not in seen and nxt in nodes:
                    seen.add(nxt)
                    remaining.discard(nxt)
                    group.append(nxt)
                    q.append(nxt)
        groups.append(sorted(group))
    groups.sort(key=len, reverse=True)
    return groups


def build_graph(sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes = {}
    for src in sources:
        nid = node_id(src)
        nodes[nid] = {
            "id": nid,
            "title": src.get("title"),
            "url": src.get("url"),
            "integrity": src.get("integrity"),
            "org": org_key(src),
            "out": edges_from(src),
        }

    ids = set(nodes)
    inbound: Dict[str, List[str]] = defaultdict(list)
    outbound: Dict[str, List[str]] = defaultdict(list)
    missing_targets: List[Tuple[str, str]] = []
    undirected: Dict[str, Set[str]] = defaultdict(set)

    for nid, node in nodes.items():
        for target in node["out"]:
            if target not in ids:
                missing_targets.append((nid, target))
                continue
            outbound[nid].append(target)
            inbound[target].append(nid)
            undirected[nid].add(target)
            undirected[target].add(nid)

    degree = []
    for nid, node in nodes.items():
        indeg = len(inbound[nid])
        outdeg = len(outbound[nid])
        degree.append({
            "id": nid,
            "title": node["title"],
            "org": node["org"],
            "in_degree": indeg,
            "out_degree": outdeg,
            "degree": indeg + outdeg,
            "integrity": node["integrity"],
        })
    degree.sort(key=lambda d: d["degree"], reverse=True)

    isolates = [d["id"] for d in degree if d["degree"] == 0]
    hubs = [d for d in degree if d["in_degree"] >= 2][:8]

    org_clusters: Dict[str, List[str]] = defaultdict(list)
    for nid, node in nodes.items():
        org_clusters[node["org"]].append(nid)
    shared_lineage = [
        {"org": org, "sources": sorted(members), "count": len(members)}
        for org, members in org_clusters.items()
        if len(members) >= 2
    ]
    shared_lineage.sort(key=lambda x: x["count"], reverse=True)

    comps = components(ids, undirected)
    circular_risk = []
    for nid, node in nodes.items():
        for target in outbound[nid]:
            if nid in outbound.get(target, []):
                pair = tuple(sorted([nid, target]))
                if pair not in circular_risk:
                    circular_risk.append(pair)

    return {
        "node_count": len(nodes),
        "edge_count": sum(len(v) for v in outbound.values()),
        "nodes": degree,
        "hubs": hubs,
        "isolates": isolates,
        "shared_lineage_clusters": shared_lineage,
        "weakly_connected_components": comps,
        "component_count": len(comps),
        "mutual_citations": [{"a": a, "b": b} for a, b in circular_risk],
        "missing_cite_targets": [{"from": a, "to": b} for a, b in missing_targets],
        "warnings": _warnings(isolates, shared_lineage, hubs, circular_risk),
    }


def _warnings(isolates, shared_lineage, hubs, circular_risk) -> List[str]:
    warnings = []
    if isolates:
        warnings.append(
            f"{len(isolates)} sources have no cite edges — they cannot corroborate each other via graph structure."
        )
    for cluster in shared_lineage:
        warnings.append(
            f"Shared lineage '{cluster['org']}' appears {cluster['count']} times; do not count as independent."
        )
    if hubs:
        warnings.append(
            f"Citation hubs: {', '.join(h['id'] for h in hubs[:3])}. Downstream sources may not be independent."
        )
    if circular_risk:
        warnings.append("Mutual citations detected; treat as a single lineage until independence is shown.")
    return warnings


def format_text(graph: Dict[str, Any]) -> str:
    lines = [
        "CITATION / PROVENANCE GRAPH",
        "=" * 72,
        f"Nodes: {graph['node_count']}   Edges: {graph['edge_count']}   "
        f"Components: {graph['component_count']}",
        "",
        "Top degree",
    ]
    for node in graph["nodes"][:10]:
        lines.append(
            f"  {node['id']:20} in={node['in_degree']} out={node['out_degree']}  "
            f"org={node['org']}  {node.get('integrity') or ''}"
        )
    if graph["hubs"]:
        lines.append("")
        lines.append("Hubs (in-degree ≥ 2): " + ", ".join(h["id"] for h in graph["hubs"]))
    if graph["isolates"]:
        lines.append("Isolates: " + ", ".join(graph["isolates"]))
    if graph["shared_lineage_clusters"]:
        lines.append("")
        lines.append("Shared-lineage clusters")
        for cluster in graph["shared_lineage_clusters"]:
            lines.append(f"  {cluster['org']}: {', '.join(cluster['sources'])}")
    if graph["mutual_citations"]:
        lines.append("")
        lines.append("Mutual citations")
        for pair in graph["mutual_citations"]:
            lines.append(f"  {pair['a']} ↔ {pair['b']}")
    if graph["warnings"]:
        lines.append("")
        lines.append("Warnings")
        for w in graph["warnings"]:
            lines.append(f"  - {w}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze citation/provenance graph structure for independence risk."
    )
    parser.add_argument("sources_file", help="JSON sources with optional 'cites' edges")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        sources = load_sources(args.sources_file)
        graph = build_graph(sources)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(graph, indent=2))
    else:
        print(format_text(graph))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
