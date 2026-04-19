"""Phase 1: Embed eCornell courses locally, save to file."""
import json
import os
import time

from openai import OpenAI

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
BATCH_SIZE = 200
MODEL = "text-embedding-3-large"
DIMENSIONS = 1536  # truncated for pgvector index compat, large model quality
INPUT = os.environ.get("COURSES_INPUT", "courses_for_embedding.json")
OUTPUT = os.environ.get("COURSES_OUTPUT", "courses_embedded.jsonl")


def main():
    with open(INPUT) as f:
        courses = json.load(f)

    client = OpenAI(api_key=OPENAI_API_KEY)
    total = len(courses)
    print(f"Embedding {total} courses with {MODEL}...")

    with open(OUTPUT, "w") as out:
        for i in range(0, total, BATCH_SIZE):
            batch = courses[i:i + BATCH_SIZE]
            texts = [c["text"] for c in batch]

            resp = client.embeddings.create(input=texts, model=MODEL, dimensions=DIMENSIONS)
            embeddings = [d.embedding for d in resp.data]

            for c, emb in zip(batch, embeddings):
                row = {**c, "embedding": emb}
                out.write(json.dumps(row) + "\n")

            done = min(i + BATCH_SIZE, total)
            print(f"  [{done}/{total}] embedded")
            time.sleep(0.2)

    print(f"\nSaved to {OUTPUT}")


if __name__ == "__main__":
    main()
