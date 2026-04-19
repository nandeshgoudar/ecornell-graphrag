#!/usr/bin/env python3
"""
build_communities.py — Discover program communities via Louvain algorithm on
the SHARES_INSTRUCTOR graph, then generate LLM summaries per community.

Outputs: communities.json
[{
  "id": "community_0",
  "program_ids": [...],
  "programs": [...names...],
  "size": 12,
  "summary": "LLM-generated 2-3 sentence description"
}]

Run after embed_programs.py. Requires networkx >= 3.0.
"""
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import networkx as nx

BASE   = Path("/var/www/cornell")
CLAUDE = "/usr/bin/claude"
SUMMARY_BATCH = 30  # generate summaries for top-N communities


def build_louvain_communities(programs: dict[str, str], links: list[dict]) -> list[list[str]]:
    """Run Louvain community detection on SHARES_INSTRUCTOR subgraph."""
    G = nx.Graph()
    for pid in programs:
        G.add_node(pid)
    for l in links:
        if l.get("relation") == "SHARES_INSTRUCTOR":
            s, t = l["source"], l["target"]
            if s in programs and t in programs:
                G.add_edge(s, t)

    print(f"Instructor-sharing graph: {G.number_of_nodes()} programs, {G.number_of_edges()} edges")

    # Louvain is available in networkx >= 3.0
    try:
        from networkx.algorithms.community import louvain_communities
        raw = louvain_communities(G, seed=42)
        return [list(c) for c in raw if len(c) > 1]
    except AttributeError:
        # Fallback: greedy modularity
        from networkx.algorithms.community import greedy_modularity_communities
        raw = greedy_modularity_communities(G)
        return [list(c) for c in raw if len(c) > 1]


def generate_summary(programs: list[str]) -> str:
    """Use Claude Haiku to generate a 2-3 sentence community summary."""
    prog_list = ", ".join(programs[:12])
    prompt = (
        f"These eCornell professional programs cluster together based on shared instructors "
        f"and curriculum overlap:\n\nPrograms: {prog_list}\n\n"
        "Write exactly 2-3 sentences:\n"
        "1. What is this cluster's unified learning theme?\n"
        "2. What career stage and role does it serve?\n"
        "3. What is the natural learning progression within it?\n\n"
        "Be specific and concrete. No generic statements. No bullet points."
    )
    result = subprocess.run(
        [CLAUDE, "-p", "--model", "claude-haiku-4-5-20251001"],
        input=prompt.encode(),
        capture_output=True,
        timeout=60,
    )
    return result.stdout.decode().strip()


def main():
    with open(BASE / "graph.json") as f:
        graph = json.load(f)

    programs = {
        n["id"]: n.get("name", n["id"].replace("program:", ""))
        for n in graph["nodes"]
        if n["type"] == "program"
    }
    print(f"Loaded {len(programs)} programs")

    comms_raw = build_louvain_communities(programs, graph["links"])
    print(f"Discovered {len(comms_raw)} communities (>1 member)")

    # Sort by size descending
    comms_raw.sort(key=lambda c: -len(c))

    communities = []
    for i, prog_ids in enumerate(comms_raw):
        prog_names = [programs.get(pid, pid.replace("program:", "")) for pid in prog_ids]
        communities.append({
            "id": f"community_{i}",
            "program_ids": prog_ids,
            "programs": prog_names,
            "size": len(prog_ids),
            "summary": "",
        })

    print(f"\nTop 10 community sizes: {[c['size'] for c in communities[:10]]}")
    print(f"\nGenerating summaries for top {SUMMARY_BATCH} communities...")

    for j, comm in enumerate(communities[:SUMMARY_BATCH]):
        summary = generate_summary(comm["programs"])
        comm["summary"] = summary
        print(f"  [{j+1}/{SUMMARY_BATCH}] community_{j} ({comm['size']} progs): {summary[:90]}...")

    out = BASE / "communities.json"
    with open(out, "w") as f:
        json.dump(communities, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(communities)} communities → {out}")
    print("Next: run add_topic_overlap.py, then restart the API")


if __name__ == "__main__":
    main()
