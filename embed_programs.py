#!/usr/bin/env python3
"""
embed_programs.py — Embed all eCornell programs using OpenAI text-embedding-3-large.
Outputs: program_embeddings.json  {program_id: [float, ...]}

Run once on the server to enable embedding-based program matching in the API.
Cost: ~682 programs × $0.00013/1K tokens ≈ $0.01
"""
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv("/var/www/cornell/.env")

from openai import OpenAI

EMBED_MODEL = "text-embedding-3-large"
EMBED_DIMS  = 1536
BATCH_SIZE  = 200

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
BASE   = Path("/var/www/cornell")


def main():
    with open(BASE / "graph.json") as f:
        graph = json.load(f)

    programs = [n for n in graph["nodes"] if n["type"] == "program"]
    print(f"Embedding {len(programs)} programs with {EMBED_MODEL}...")

    embeddings: dict[str, list[float]] = {}

    for i in range(0, len(programs), BATCH_SIZE):
        batch = programs[i : i + BATCH_SIZE]
        # Enrich text with context so the embedding carries domain signal
        texts = [
            f"eCornell professional program: {p.get('name', p['id'].replace('program:', ''))}"
            for p in batch
        ]
        resp = client.embeddings.create(input=texts, model=EMBED_MODEL, dimensions=EMBED_DIMS)
        for prog, datum in zip(batch, resp.data):
            embeddings[prog["id"]] = datum.embedding

        done = min(i + BATCH_SIZE, len(programs))
        print(f"  [{done}/{len(programs)}] embedded")
        if done < len(programs):
            time.sleep(0.3)  # stay under rate limit

    out = BASE / "program_embeddings.json"
    with open(out, "w") as f:
        json.dump(embeddings, f, separators=(",", ":"))

    size_mb = out.stat().st_size / 1_048_576
    print(f"\nSaved {len(embeddings)} embeddings → {out}  ({size_mb:.1f} MB)")
    print("Next: run build_communities.py")


if __name__ == "__main__":
    main()
