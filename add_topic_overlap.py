#!/usr/bin/env python3
"""
add_topic_overlap.py — Fetch course embeddings from Supabase pgvector,
compute cosine similarity matrix, add TOPIC_OVERLAP edges to graph.json.

Similarity threshold: 0.82 (high precision — avoids noisy cross-topic edges)
Max edges per course: 5 (keeps graph sparse enough to visualize)

Outputs: updated graph.json with TOPIC_OVERLAP edges added
"""
import json
import os
from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv

load_dotenv("/var/www/cornell/.env")

BASE             = Path("/var/www/cornell")
SUPA_URL         = os.environ.get("SUPABASE_URL", "https://supabase.learnleadai.com")
# Try multiple env var names; fall back to known service role key
SUPA_KEY         = (
    os.environ.get("SUPABASE_SERVICE_KEY") or
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or
    os.environ.get("SUPA_KEY")
)
if not SUPA_KEY:
    raise RuntimeError("SUPABASE_SERVICE_KEY is required — set it in .env")
SIMILARITY_THRESH = 0.82
MAX_EDGES_COURSE  = 5


def supa_headers() -> dict:
    return {
        "apikey":        SUPA_KEY,
        "Authorization": f"Bearer {SUPA_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "count=none",
    }


def fetch_all_embeddings() -> list[dict]:
    """Paginate through ecornell_embeddings table."""
    rows: list[dict] = []
    page_size = 500
    offset    = 0
    print("Fetching course embeddings from Supabase...")

    with httpx.Client(timeout=120) as client:
        while True:
            resp = client.get(
                f"{SUPA_URL}/rest/v1/ecornell_embeddings",
                headers={
                    **supa_headers(),
                    "Range": f"{offset}-{offset + page_size - 1}",
                    "Range-Unit": "items",
                },
                params={"select": "title,url,embedding", "order": "id.asc"},
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            rows.extend(batch)
            print(f"  {len(rows)} courses fetched...")
            if len(batch) < page_size:
                break
            offset += page_size

    return rows


def parse_embedding(raw) -> list[float]:
    if isinstance(raw, str):
        # pgvector returns "[0.1,0.2,...]"
        return json.loads(raw)
    return raw  # already a list


def main():
    rows = fetch_all_embeddings()
    print(f"Total: {len(rows)} courses with embeddings")

    urls: list[str]  = []
    vecs: list[list] = []
    for r in rows:
        emb = parse_embedding(r["embedding"])
        if emb:
            urls.append(r.get("url", ""))
            vecs.append(emb)

    mat = np.array(vecs, dtype=np.float32)
    # Normalise rows for cosine similarity
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    mat_n = mat / norms

    print(f"Computing {len(mat)}×{len(mat)} similarity matrix (this takes a few seconds)...")
    sim: np.ndarray = mat_n @ mat_n.T  # shape (N, N)
    np.fill_diagonal(sim, 0.0)        # exclude self-similarity
    print("Done.")

    # Load graph — build URL → node-id index
    with open(BASE / "graph.json") as f:
        graph = json.load(f)

    url_to_node: dict[str, str] = {
        n["url"]: n["id"]
        for n in graph["nodes"]
        if n.get("url") and n.get("type") == "course"
    }

    # Build TOPIC_OVERLAP edges
    new_links: list[dict] = []
    seen_pairs: set[tuple] = set()
    n = len(urls)

    for i in range(n):
        row = sim[i]
        # Find candidates above threshold
        cands = np.where(row >= SIMILARITY_THRESH)[0]
        # Sort by similarity, take top MAX_EDGES_COURSE
        cands = sorted(cands.tolist(), key=lambda j: -float(row[j]))[:MAX_EDGES_COURSE]

        for j in cands:
            pair = (min(i, j), max(i, j))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            src_id = url_to_node.get(urls[i])
            tgt_id = url_to_node.get(urls[j])
            if src_id and tgt_id and src_id != tgt_id:
                new_links.append({
                    "source":   src_id,
                    "target":   tgt_id,
                    "relation": "TOPIC_OVERLAP",
                    "score":    round(float(row[j]), 3),
                })

    print(f"TOPIC_OVERLAP edges found: {len(new_links)}  (threshold={SIMILARITY_THRESH})")

    # Replace any existing TOPIC_OVERLAP links
    graph["links"] = [l for l in graph["links"] if l.get("relation") != "TOPIC_OVERLAP"]
    graph["links"].extend(new_links)

    with open(BASE / "graph.json", "w") as f:
        json.dump(graph, f, ensure_ascii=False, separators=(",", ":"))

    from collections import Counter
    rel_counts = Counter(l["relation"] for l in graph["links"])
    print(f"\nUpdated graph.json:")
    print(f"  Nodes: {len(graph['nodes'])}")
    print(f"  Links: {len(graph['links'])}")
    for rel, cnt in sorted(rel_counts.items()):
        print(f"    {rel:<25} {cnt}")


if __name__ == "__main__":
    main()
