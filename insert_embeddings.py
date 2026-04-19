"""Phase 2: Insert embeddings into Supabase pgvector via docker exec psql."""
import json
import subprocess
import sys

INPUT = "/tmp/courses_embedded.jsonl"
BATCH_SIZE = 20


def escape_sql(s):
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''").replace("\\", "\\\\") + "'"


def insert_batch(rows):
    values = []
    for r in rows:
        emb = "[" + ",".join(str(x) for x in r["embedding"]) + "]"
        val = f"({escape_sql(r['id'])},{escape_sql(r['title'])},{escape_sql(r.get('program',''))},{escape_sql(r.get('instructor',''))},{escape_sql(r.get('instructor_role',''))},{escape_sql(r.get('url',''))},{escape_sql(r.get('status',''))},{escape_sql(r.get('banner',''))},{escape_sql(r['text'])},'{emb}')"
        values.append(val)

    sql = f"""INSERT INTO ecornell_embeddings (id,title,program,instructor,instructor_role,url,status,banner,content,embedding) VALUES {','.join(values)} ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title,program=EXCLUDED.program,instructor=EXCLUDED.instructor,content=EXCLUDED.content,embedding=EXCLUDED.embedding;"""

    result = subprocess.run(
        ["docker", "exec", "-i", "supabase-db", "psql", "-U", "postgres"],
        input=sql, capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr[:200]}", file=sys.stderr)
        return False
    return True


def main():
    count = 0
    batch = []

    with open(INPUT) as f:
        for line in f:
            row = json.loads(line)
            batch.append(row)

            if len(batch) >= BATCH_SIZE:
                if insert_batch(batch):
                    count += len(batch)
                    print(f"  [{count}] inserted")
                else:
                    print(f"  FAILED at {count}", file=sys.stderr)
                    sys.exit(1)
                batch = []

        if batch:
            insert_batch(batch)
            count += len(batch)

    print(f"\nDone! {count} courses inserted.")


if __name__ == "__main__":
    main()
