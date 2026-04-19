# eCornell GraphRAG

A personalized learning-pathway recommender built on top of the eCornell course catalog. Takes a short onboarding intake, runs semantic search across 2,176 embedded courses, uses Claude to design a six-phase pathway, and emails the user a custom HTML summary + PDF report.

## Components

| File | Purpose |
|---|---|
| `api_server.py` | FastAPI backend — form submission, retry, admin, rate limits, email delivery |
| `index.html` | Single-page onboarding form + D3 knowledge-graph visualizer |
| `generate_report.py` | ReportLab PDF report generator |
| `send_email.py` | Brevo SMTP sender with PDF attachment |
| `embed_courses.py` | One-shot OpenAI `text-embedding-3-large` embedding of the catalog |
| `insert_embeddings.py` | Load embeddings into Postgres `pgvector` table |
| `embed_programs.py` | Program-level embeddings for the knowledge graph |
| `add_topic_overlap.py` | Add cosine-similarity edges between programs |
| `build_communities.py` | Louvain community detection + Claude summaries |
| `rebuild_graph.py` | Rebuild the NetworkX knowledge graph from Postgres |
| `search_courses.py` | CLI semantic search over the embedded catalog |
| `courses_lite.json` | Lightweight course catalog snapshot |
| `ONBOARDING_GUIDE.md` | Walkthrough of the onboarding questions and pathway design |

## Stack

- **Python 3.10+** — FastAPI, NetworkX, ReportLab, OpenAI SDK, psycopg
- **Postgres + pgvector** — vector store for semantic search
- **Brevo** — transactional email
- **Claude (Anthropic)** — pathway design and community summaries

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env — set OPENAI_API_KEY, SMTP_*, DB_*, ADMIN_KEY, SUPABASE_*
```

### Build the graph + embeddings

```bash
# 1. Embed the catalog (local JSONL)
python embed_courses.py

# 2. Load into pgvector
python insert_embeddings.py

# 3. Embed programs + build graph
python embed_programs.py
python build_communities.py
python add_topic_overlap.py
python rebuild_graph.py
```

### Run the app

```bash
uvicorn api_server:app --reload --port 8000
# Open http://localhost:8000/
```

### CLI search

```bash
python search_courses.py "behavioral science for executive coaching"
```

## Deploy notes

- Caddy recommended as reverse proxy (handles HSTS, X-Frame-Options, Referrer-Policy).
- Set `ADMIN_KEY` to something non-trivial — the server refuses to start with the default placeholder.
- Rate limiting, CORS, and HTML-escape are enforced in `api_server.py`.

## License

MIT — see `LICENSE`.
