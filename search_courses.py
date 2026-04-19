"""Semantic search over eCornell course embeddings."""
import json
import os
import subprocess
import sys

from openai import OpenAI

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = "text-embedding-3-large"
DIMENSIONS = 1536

# SSH target running `docker exec -i supabase-db psql ...` — override via env
SSH_HOST = os.environ.get("PG_SSH_HOST", "db-server")
PSQL_CMD = os.environ.get(
    "PG_PSQL_CMD",
    "docker exec -i supabase-db psql -U postgres -t -A -F '|'",
)


def search(query: str, limit: int = 10) -> list:
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.embeddings.create(input=[query], model=MODEL, dimensions=DIMENSIONS)
    emb = resp.data[0].embedding
    emb_str = "[" + ",".join(str(x) for x in emb) + "]"

    sql = (
        f"SELECT title, program, instructor, instructor_role, "
        f"1 - (embedding <=> '{emb_str}'::vector) AS similarity "
        f"FROM ecornell_embeddings ORDER BY embedding <=> '{emb_str}'::vector "
        f"LIMIT {int(limit)};"
    )

    result = subprocess.run(
        ["ssh", SSH_HOST, PSQL_CMD],
        input=sql, capture_output=True, text=True, timeout=30,
    )

    rows = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|")
        if len(parts) >= 5:
            rows.append({
                "title": parts[0],
                "program": parts[1],
                "instructor": parts[2],
                "role": parts[3],
                "similarity": float(parts[4]),
            })
    return rows


def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "AI and machine learning for business leaders"
    print(f"Query: {query}\n")

    results = search(query)
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['similarity']:.3f}] {r['title']}")
        print(f"   Program: {r['program']} | Instructor: {r['instructor']}")
        print()


if __name__ == "__main__":
    main()
