"""
eCornell GraphRAG API Server
POST /api/analyze        — streaming pathway generation
POST /api/search         — semantic course search
POST /api/submit-profile — collect profile, ack email, background pathway
POST /api/retry          — admin: re-trigger failed submission
POST /api/chat           — follow-up chat
GET  /api/courses        — browse/search 2,176 courses
GET  /api/health         — status
"""

import asyncio
import html as _html
import json
import logging
import os
import re
import smtplib
import subprocess
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import AsyncGenerator, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ──────────────────────────────────────────────
# CONFIG — all secrets from environment
# ──────────────────────────────────────────────
load_dotenv("/var/www/cornell/.env")

OPENAI_KEY   = os.environ.get("OPENAI_API_KEY", "")
EMBED_MODEL  = "text-embedding-3-large"
EMBED_DIMS   = 1536
COGNEE_BASE  = "http://localhost:8110"
DB_CONTAINER = "supabase-db"
CLAUDE_BIN      = "/usr/bin/claude"
# Isolated Claude config home — no MCPs, no personal data, no tools.
# Pathway generation must only use the prompt (course catalog + user form inputs).
CLAUDE_CLEAN_HOME = "/var/www/cornell/.claude_subprocess"

SMTP_HOST    = os.environ.get("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT    = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER    = os.environ.get("SMTP_USER", "")
SMTP_PASS    = os.environ.get("SMTP_PASS", "")
FROM_EMAIL   = os.environ.get("FROM_EMAIL", "no-reply@example.com")
FROM_NAME    = os.environ.get("FROM_NAME", "eCornell GraphRAG")
ADMIN_EMAIL  = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_KEY    = os.environ.get("ADMIN_KEY", "")
if not ADMIN_KEY or ADMIN_KEY == "change-me":
    raise RuntimeError("ADMIN_KEY must be set in .env and must not be 'change-me'")

SUPA_URL     = os.environ.get("SUPABASE_URL", "https://supabase.learnleadai.com")
SUPA_KEY     = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not SUPA_KEY:
    raise RuntimeError("SUPABASE_SERVICE_KEY is required — set it in .env")

# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("cornell-api")

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
def _esc(s: str) -> str:
    return _html.escape(str(s or ""), quote=True)

_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def _clean_email(email: str) -> str:
    return email.replace("\n", "").replace("\r", "").strip()

def _valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(_clean_email(email)))

def _clean_name(name: str) -> str:
    return name.replace("\n", "").replace("\r", "").strip()[:100]

# ──────────────────────────────────────────────
# APP + RATE LIMITER
# ──────────────────────────────────────────────
embed_client = AsyncOpenAI(api_key=OPENAI_KEY)
app = FastAPI(title="eCornell GraphRAG API")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cornell.learnleadai.com"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# ──────────────────────────────────────────────
# COURSE CATALOG + KNOWLEDGE GRAPH (in-memory)
# ──────────────────────────────────────────────
_COURSES_LITE: list = []

# Graph adjacency structures
_GRAPH_NODES:       dict = {}   # id → node dict
_GRAPH_ADJ:         dict = {}   # id → list of (neighbor_id, relation)
_DOMAIN_PROGRAMS:   dict = {}   # domain_id → list of program_ids
_PROGRAM_COURSES:   dict = {}   # program_name → list of course dicts
_INSTRUCTOR_COURSES: dict = {}  # instructor_name → list of program_names
_URL_TO_NODE_ID:    dict = {}   # course url → course node id
_COURSE_PROGRAM_ID: dict = {}   # course node id → program node id

# Embedding-based program search (loaded from program_embeddings.json)
_PROG_EMB_IDS:    list = []     # program ids in matrix row order
_PROG_EMB_MATRIX        = None  # numpy (N, 1536) normalised, or None if unavailable

# Discovered curriculum communities (loaded from communities.json)
_COMMUNITIES: list = []


@app.on_event("startup")
async def load_courses():
    global _COURSES_LITE, _GRAPH_NODES, _GRAPH_ADJ
    global _DOMAIN_PROGRAMS, _PROGRAM_COURSES, _INSTRUCTOR_COURSES
    global _URL_TO_NODE_ID, _COURSE_PROGRAM_ID
    global _PROG_EMB_IDS, _PROG_EMB_MATRIX, _COMMUNITIES

    # ── courses_lite.json ──
    path = os.path.join(os.path.dirname(__file__), "courses_lite.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        _COURSES_LITE = data["courses"] if isinstance(data, dict) else data
        logger.info(f"Loaded {len(_COURSES_LITE)} courses")

    # ── graph.json ──
    gpath = os.path.join(os.path.dirname(__file__), "graph.json")
    if os.path.exists(gpath):
        with open(gpath) as f:
            g = json.load(f)
        for n in g.get("nodes", []):
            _GRAPH_NODES[n["id"]] = n
            _GRAPH_ADJ[n["id"]] = []
            if n.get("type") == "course" and n.get("url"):
                _URL_TO_NODE_ID[n["url"]] = n["id"]
        for lnk in g.get("links", []):
            s, t, rel = lnk["source"], lnk["target"], lnk.get("relation", "")
            _GRAPH_ADJ.setdefault(s, []).append((t, rel))
            _GRAPH_ADJ.setdefault(t, []).append((s, rel))
            if rel == "BELONGS_TO_DOMAIN":
                _DOMAIN_PROGRAMS.setdefault(t, []).append(s)
            if rel == "BELONGS_TO":
                _COURSE_PROGRAM_ID[s] = t  # course → program

        # Build program→courses and instructor→programs from catalog
        for c in _COURSES_LITE:
            _PROGRAM_COURSES.setdefault(c.get("program", ""), []).append(c)
            _INSTRUCTOR_COURSES.setdefault(c.get("instructor", ""), set()).add(c.get("program", ""))
        _INSTRUCTOR_COURSES = {k: list(v) for k, v in _INSTRUCTOR_COURSES.items()}
        logger.info(f"Graph loaded: {len(_GRAPH_NODES)} nodes, {sum(len(v) for v in _GRAPH_ADJ.values())//2} edges")

    # ── program_embeddings.json → numpy matrix ──
    pepath = os.path.join(os.path.dirname(__file__), "program_embeddings.json")
    if os.path.exists(pepath):
        try:
            import numpy as np
            with open(pepath) as f:
                raw_emb = json.load(f)
            _PROG_EMB_IDS[:] = list(raw_emb.keys())
            mat = np.array([raw_emb[pid] for pid in _PROG_EMB_IDS], dtype=np.float32)
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1.0, norms)
            _PROG_EMB_MATRIX = mat / norms  # L2-normalised for cosine via dot product
            logger.info(f"Program embeddings: {len(_PROG_EMB_IDS)} programs indexed")
        except ImportError:
            logger.warning("numpy not installed — program embedding search disabled (run: pip3 install numpy)")
        except Exception as e:
            logger.warning(f"Failed to load program embeddings: {e}")

    # ── communities.json ──
    cpath = os.path.join(os.path.dirname(__file__), "communities.json")
    if os.path.exists(cpath):
        with open(cpath) as f:
            _COMMUNITIES[:] = json.load(f)
        logger.info(f"Communities: {len(_COMMUNITIES)} loaded")

    # ── Isolated Claude subprocess config ──
    # Write a clean settings.json with zero MCP servers so the Claude CLI
    # subprocess used for pathway generation has no access to personal tools,
    # Notion, Gmail, memory plugins, or any external data source.
    # Generation must be grounded solely in the course catalog + user form inputs.
    import stat
    os.makedirs(CLAUDE_CLEAN_HOME, exist_ok=True)
    clean_dot_claude = os.path.join(CLAUDE_CLEAN_HOME, ".claude")
    os.makedirs(clean_dot_claude, exist_ok=True)
    clean_settings = {"model": "claude-sonnet-4-6", "mcpServers": {}}
    with open(os.path.join(clean_dot_claude, "settings.json"), "w") as f:
        json.dump(clean_settings, f)
    # Copy credentials so Claude CLI subprocess can authenticate.
    # settings.json is rewritten above (no MCPs), so credentials are the only
    # file we carry over from the real HOME.
    real_creds = os.path.expanduser("~/.claude/.credentials.json")
    if os.path.exists(real_creds):
        import shutil
        shutil.copy2(real_creds, os.path.join(clean_dot_claude, ".credentials.json"))
    os.chmod(CLAUDE_CLEAN_HOME, stat.S_IRWXU)
    logger.info("Claude subprocess isolation: clean home created (no MCPs)")

# ──────────────────────────────────────────────
# MODELS
# ──────────────────────────────────────────────
class OnboardingAnswers(BaseModel):
    q1:  Optional[str] = ""
    q2:  Optional[str] = ""
    q3:  Optional[str] = ""
    q4:  Optional[str] = ""
    q5:  Optional[str] = ""
    q6:  Optional[str] = ""
    q7:  Optional[str] = ""
    q8:  Optional[str] = ""
    q9:  Optional[str] = ""
    q10: Optional[str] = ""
    q11: Optional[str] = ""
    q12: Optional[str] = ""
    q13: Optional[str] = ""
    q14: Optional[str] = ""

class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=15, ge=1, le=100)

class ProfileSubmission(BaseModel):
    name:  str
    email: str
    q1:  Optional[str] = ""
    q2:  Optional[str] = ""
    q3:  Optional[str] = ""
    q4:  Optional[str] = ""
    q5:  Optional[str] = ""
    q6:  Optional[str] = ""
    q7:  Optional[str] = ""
    q8:  Optional[str] = ""
    q9:  Optional[str] = ""
    q10: Optional[str] = ""
    q11: Optional[str] = ""
    q12: Optional[str] = ""
    q13: Optional[str] = ""
    q14: Optional[str] = ""

class ChatRequest(BaseModel):
    context:  str
    question: str
    profile:  str = ""

class SendPathwayRequest(BaseModel):
    to_email:     str
    pathway_text: str
    subject: str = "Your eCornell Learning Pathway - 6 Phases Built for You"

class RetryRequest(BaseModel):
    sub_id:    str
    admin_key: str

# ──────────────────────────────────────────────
# SUPABASE PERSISTENCE
# ──────────────────────────────────────────────
def _supa_headers() -> dict:
    return {
        "apikey": SUPA_KEY,
        "Authorization": f"Bearer {SUPA_KEY}",
        "Content-Type": "application/json",
    }

def _db_insert_submission(name: str, email: str, answers: OnboardingAnswers) -> str:
    sub_id = str(uuid.uuid4())
    answers_dict = {f"q{i}": getattr(answers, f"q{i}", "") for i in range(1, 15)}
    with httpx.Client(timeout=10) as client:
        resp = client.post(
            f"{SUPA_URL}/rest/v1/cornell_submissions",
            headers=_supa_headers(),
            json={"id": sub_id, "name": name, "email": email, "answers": answers_dict},
        )
        resp.raise_for_status()
    return sub_id

def _db_update_status(sub_id: str, status: str):
    payload: dict = {"status": status}
    if status == "sent":
        payload["sent_at"] = datetime.now(timezone.utc).isoformat()
    with httpx.Client(timeout=10) as client:
        resp = client.patch(
            f"{SUPA_URL}/rest/v1/cornell_submissions?id=eq.{sub_id}",
            headers=_supa_headers(),
            json=payload,
        )
        resp.raise_for_status()

# ──────────────────────────────────────────────
# PGVECTOR SEARCH
# ──────────────────────────────────────────────
async def embed_query(text: str) -> list[float]:
    resp = await embed_client.embeddings.create(
        input=[text], model=EMBED_MODEL, dimensions=EMBED_DIMS
    )
    return resp.data[0].embedding

def pgvector_search(embedding: list[float], limit: int = 12) -> list[dict]:
    import math
    # Clamp limit — never allow unbounded SQL injection via limit param
    limit = max(1, min(int(limit), 200))
    # Validate embedding: must be correct dimension, all finite floats
    if len(embedding) != EMBED_DIMS:
        raise ValueError(f"Embedding must be {EMBED_DIMS}-dimensional, got {len(embedding)}")
    clean_emb = [float(x) for x in embedding]
    for v in clean_emb:
        if not math.isfinite(v):
            raise ValueError("Embedding contains non-finite value")
    # Format as fixed-precision floats — no SQL metacharacters possible in %f output
    emb_str = "[" + ",".join(f"{v:.8f}" for v in clean_emb) + "]"
    sql = (
        f"SELECT title, program, instructor, instructor_role, url, "
        f"1 - (embedding <=> '{emb_str}'::vector) AS similarity "
        f"FROM ecornell_embeddings "
        f"ORDER BY embedding <=> '{emb_str}'::vector "
        f"LIMIT {limit};"
    )
    result = subprocess.run(
        ["docker", "exec", "-i", DB_CONTAINER, "psql", "-U", "postgres", "-t", "-A", "-F", "|"],
        input=sql, capture_output=True, text=True, timeout=30
    )
    rows = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|")
        if len(parts) >= 6:
            rows.append({
                "title":      parts[0],
                "program":    parts[1],
                "instructor": parts[2],
                "role":       parts[3],
                "url":        parts[4],
                "similarity": float(parts[5]) if parts[5] else 0.0,
            })
    return rows

def find_programs_by_embedding(user_emb: list[float], k: int = 20) -> list[tuple]:
    """
    Return top-k (program_id, cosine_score) pairs by comparing user embedding
    against the pre-built program embedding matrix.
    Falls back to empty list if numpy / embeddings unavailable.
    """
    if _PROG_EMB_MATRIX is None or not _PROG_EMB_IDS:
        return []
    import numpy as np
    q = np.array(user_emb, dtype=np.float32)
    norm = float(np.linalg.norm(q))
    if norm > 0:
        q /= norm
    scores = _PROG_EMB_MATRIX @ q          # cosine similarity (both normalised)
    top_idx = np.argsort(-scores)[:k]
    return [(_PROG_EMB_IDS[int(i)], float(scores[i])) for i in top_idx]


def graph_guided_expansion(
    anchor_courses: list[dict],
    nearest_programs: list[tuple],
    answers: Optional[OnboardingAnswers] = None,
) -> dict:
    """
    Core GraphRAG retrieval — a single unified pipeline:

    1. Map anchor courses (from pgvector) to their program nodes in the graph
    2. Add nearest programs (from embedding cosine search)
    3. BFS expand 2 hops via SHARES_INSTRUCTOR / SAME_DOMAIN / TOPIC_OVERLAP
    4. Find which discovered communities contain the anchor programs
    5. Build domain clusters from the expanded program set
    6. Identify cross-domain bridge programs and bridge instructors
    """
    from collections import defaultdict

    def prog_name(pid: str) -> str:
        return _GRAPH_NODES.get(pid, {}).get("name", pid.replace("program:", ""))

    # ── Step 1: anchor courses → program nodes ──
    anchor_program_ids: set[str] = set()
    for c in anchor_courses:
        url = c.get("url", "")
        course_node_id = _URL_TO_NODE_ID.get(url)
        if course_node_id:
            prog_id = _COURSE_PROGRAM_ID.get(course_node_id)
            if prog_id:
                anchor_program_ids.add(prog_id)

    # ── Step 2: add embedding-nearest programs ──
    for pid, score in nearest_programs[:15]:
        if score >= 0.55:   # only include reasonably similar programs
            anchor_program_ids.add(pid)

    # ── Step 3: BFS 2-hop expansion ──
    expanded: set[str] = set(anchor_program_ids)
    hop1: set[str] = set()
    for pid in list(anchor_program_ids)[:40]:
        for (nb, rel) in _GRAPH_ADJ.get(pid, []):
            if rel in ("SHARES_INSTRUCTOR", "SAME_DOMAIN") and nb.startswith("program:"):
                hop1.add(nb)
    for pid in list(hop1)[:60]:
        expanded.add(pid)
        for (nb, rel) in _GRAPH_ADJ.get(pid, []):
            if rel in ("SHARES_INSTRUCTOR", "SAME_DOMAIN") and nb.startswith("program:"):
                expanded.add(nb)

    # ── Step 4: community matching ──
    matched_communities: list[dict] = []
    for comm in _COMMUNITIES:
        comm_set = set(comm.get("program_ids", []))
        overlap = comm_set & anchor_program_ids
        if len(overlap) >= 2:
            matched_communities.append({
                "summary":       comm.get("summary", ""),
                "programs":      comm.get("programs", [])[:8],
                "size":          comm.get("size", 0),
                "overlap_count": len(overlap),
            })
    matched_communities.sort(key=lambda c: -c["overlap_count"])

    # ── Step 5: domain clusters from expanded programs ──
    domain_hit_count: dict[str, list[str]] = defaultdict(list)
    for pid in expanded:
        for (nb, rel) in _GRAPH_ADJ.get(pid, []):
            if rel == "BELONGS_TO_DOMAIN":
                domain_hit_count[nb].append(pid)

    top_domains = sorted(domain_hit_count.items(), key=lambda x: -len(x[1]))[:4]
    top_domain_ids = {did for did, _ in top_domains}

    domain_clusters: list[dict] = []
    for did, prog_ids in top_domains:
        dnode = _GRAPH_NODES.get(did, {})
        progs = []
        for pid in prog_ids[:6]:
            pname = prog_name(pid)
            courses = _PROGRAM_COURSES.get(pname, [])[:3]
            progs.append({
                "program": pname,
                "courses": [{"title": c["title"], "url": c.get("url", "")} for c in courses],
            })
        domain_clusters.append({"domain": dnode.get("name", did), "programs": progs})

    # ── Step 6: cross-domain bridges and bridge instructors ──
    top_domain_prog_ids = {pid for _, pids in top_domains for pid in pids}
    cross_bridges = [
        prog_name(pid)
        for pid in expanded - top_domain_prog_ids
        if _GRAPH_NODES.get(pid, {}).get("type") == "program"
    ][:8]

    bridge_instructors: list[dict] = []
    for instructor, progs in _INSTRUCTOR_COURSES.items():
        domain_hits: set[str] = set()
        for prog in progs:
            prog_id = f"program:{prog}"
            for (nb, rel) in _GRAPH_ADJ.get(prog_id, []):
                if rel == "BELONGS_TO_DOMAIN" and nb in top_domain_ids:
                    domain_hits.add(nb)
        if len(domain_hits) >= 2:
            bridge_instructors.append({
                "instructor":   instructor,
                "domain_count": len(domain_hits),
                "programs":     progs[:4],
            })
    bridge_instructors.sort(key=lambda x: -x["domain_count"])

    return {
        "matched_communities":      matched_communities[:3],
        "domain_clusters":          domain_clusters,
        "cross_domain_bridges":     cross_bridges,
        "bridge_instructors":       bridge_instructors[:4],
        "anchor_program_count":     len(anchor_program_ids),
        "expanded_program_count":   len(expanded),
    }


# ── Legacy keyword-based graph_search kept for stream_pathway fallback ──
def _keyword_graph_search(answers: OnboardingAnswers) -> dict:
    """Fast keyword domain matching — used when embeddings unavailable."""
    from collections import defaultdict
    combined = " ".join(filter(None, [
        answers.q1, answers.q2, answers.q3, answers.q4, answers.q5, answers.q9, answers.q14
    ])).lower()
    DOMAIN_KEYWORDS = {
        "domain:ai_tech":    ["ai","machine learning","technology","data science","automation"],
        "domain:marketing":  ["marketing","brand","sales","advertising","content"],
        "domain:leadership": ["leadership","executive","strategy","management","coaching"],
        "domain:finance":    ["finance","financial","accounting","investment","budget"],
        "domain:hr":         ["hr","human resources","hiring","diversity","talent"],
        "domain:healthcare": ["healthcare","health","medical","clinical","nursing"],
        "domain:legal":      ["law","legal","compliance","regulatory","ethics"],
        "domain:esg":        ["sustainability","climate","esg","environmental"],
        "domain:ops":        ["project management","agile","operations","supply chain"],
        "domain:startup":    ["entrepreneur","startup","venture","innovation"],
        "domain:comms":      ["communication","writing","presentation","storytelling"],
        "domain:data":       ["data","analytics","statistics","visualization","excel"],
        "domain:realestate": ["real estate","property","construction"],
        "domain:education":  ["education","teaching","learning","training"],
    }
    scored = [(did, sum(1 for k in keys if k in combined)) for did, keys in DOMAIN_KEYWORDS.items()]
    top_ids = [d for d, s in sorted(scored, key=lambda x: -x[1]) if s > 0][:4]

    relevant_pids: list[str] = []
    for did in top_ids:
        relevant_pids.extend(_DOMAIN_PROGRAMS.get(did, [])[:15])

    seen = set(relevant_pids)
    cross_bridges: list[str] = []
    for pid in relevant_pids[:30]:
        for (nb, rel) in _GRAPH_ADJ.get(pid, []):
            if rel in ("SHARES_INSTRUCTOR", "SAME_DOMAIN") and nb not in seen:
                if _GRAPH_NODES.get(nb, {}).get("type") == "program":
                    cross_bridges.append(nb)
                    seen.add(nb)

    def prog_name(pid):
        return _GRAPH_NODES.get(pid, {}).get("name", pid.replace("program:", ""))

    domain_clusters = []
    for did in top_ids:
        dnode = _GRAPH_NODES.get(did, {})
        progs = [{"program": prog_name(pid), "courses": [
            {"title": c["title"], "url": c.get("url", "")}
            for c in _PROGRAM_COURSES.get(prog_name(pid), [])[:3]
        ]} for pid in _DOMAIN_PROGRAMS.get(did, [])[:8]]
        domain_clusters.append({"domain": dnode.get("name", did), "programs": progs})

    bridge_instrs = []
    for instr, progs in _INSTRUCTOR_COURSES.items():
        d_hits = {nb for p in progs for (nb, r) in _GRAPH_ADJ.get(f"program:{p}", [])
                  if r == "BELONGS_TO_DOMAIN" and nb in set(top_ids)}
        if len(d_hits) >= 2:
            bridge_instrs.append({"instructor": instr, "domain_count": len(d_hits), "programs": progs[:4]})
    bridge_instrs.sort(key=lambda x: -x["domain_count"])

    return {
        "matched_communities":    [],
        "domain_clusters":        domain_clusters,
        "cross_domain_bridges":   [prog_name(p) for p in cross_bridges[:6]],
        "bridge_instructors":     bridge_instrs[:4],
        "anchor_program_count":   0,
        "expanded_program_count": len(relevant_pids),
    }

# ──────────────────────────────────────────────
# THEME EXTRACTION
# ──────────────────────────────────────────────
def extract_search_themes(answers: OnboardingAnswers) -> list[str]:
    combined = " ".join([
        answers.q1 or "", answers.q2 or "", answers.q3 or "",
        answers.q4 or "", answers.q9 or "", answers.q14 or ""
    ]).lower()

    domain_map = [
        (["project manag", "pm ", "pmo"],                        "project management and organizational systems"),
        (["notion", "clickup", "monday", "asana", "airtable"],   "productivity tools and workflow automation"),
        (["ai ", "artificial intelligence", "machine learning"],  "AI adoption for business teams"),
        (["coach", "coaching"],                                   "coaching and organizational performance"),
        (["real estate", "property"],                             "real estate marketing and operations"),
        (["marketing", "brand", "funnel", "content", "linkedin"], "marketing strategy and brand building"),
        (["product", "digital product", "template"],              "digital product development and packaging"),
        (["behav", "psychology", "cognitive", "decision"],        "behavioral science and decision making"),
        (["productiv", "performance", "efficiency"],              "organizational productivity and performance"),
        (["change", "transform", "adopt", "implement"],           "change management and implementation"),
        (["sales", "cold outreach", "pipeline", "revenue"],       "sales strategy and revenue growth"),
        (["leader", "executive", "manag", "organiz"],             "leadership and organizational strategy"),
        (["data", "analytic", "insight", "metric"],               "data analytics and business intelligence"),
        (["sustainab", "esg", "climate"],                         "sustainable business strategy"),
        (["startup", "entrepreneur", "venture", "freelanc"],      "entrepreneurship and business building"),
        (["consult", "advisory", "agency"],                       "consulting and professional services"),
        (["community", "b2b", "saas"],                            "community management and B2B SaaS"),
        (["cold email", "outreach", "email market"],              "cold email marketing and outreach strategy"),
        (["personal brand", "thought leader"],                    "personal branding and executive presence"),
        (["stakeholder", "c-suite", "board"],                     "stakeholder management and executive communication"),
    ]

    themes = []
    for keywords, query in domain_map:
        if any(kw in combined for kw in keywords):
            themes.append(query)
    if answers.q14:
        themes.append(answers.q14[:120])
    if answers.q3:
        themes.append(answers.q3[:120])
    return list(dict.fromkeys(themes))[:8]

# ──────────────────────────────────────────────
# PROMPTS
# ──────────────────────────────────────────────
def build_analysis_prompt(answers: OnboardingAnswers, pgvector_results: dict, cognee_results: list) -> str:
    course_sections = []
    for theme, courses in pgvector_results.items():
        if courses:
            lines = [f"Theme: {theme}"]
            for c in courses[:8]:
                lines.append(f"  - [{c['similarity']:.2f}] {c['title']} | {c['program']} | {c['instructor']} | {c['url']}")
            course_sections.append("\n".join(lines))
    cognee_section = ""
    if cognee_results:
        lines = ["Cognee Results:"]
        for r in cognee_results[:10]:
            if r.get("type") != "error":
                lines.append(f"  - [{r.get('type','')}] {r.get('title','')} - {r.get('content','')[:100]}")
        cognee_section = "\n".join(lines)
    return f"""You are a world-class learning pathway architect for eCornell GraphRAG.

STUDENT PROFILE:
Leadership direction: {answers.q1}
2-year vision: {answers.q2}
Biggest bottleneck: {answers.q3}
Who they lead/serve: {answers.q4}
AI/transformation challenges: {answers.q5}
Accountable for: {answers.q6}
Revenue target: {answers.q7}
Value generation: {answers.q8}
Next initiative: {answers.q9}
Credentials: {answers.q10 or 'None'}
Target institution: {answers.q11 or 'None'}
Strengths/gaps: {answers.q12}
Hours/week: {answers.q13}
Known for: {answers.q14}

COURSE RETRIEVAL:
{chr(10).join(course_sections)}

{cognee_section}

Build a personalized 6-phase eCornell learning pathway. For each phase: name, timeline, 4-6 courses with why/deliverable/LinkedIn angle, strategic reason.
Career narrative: where they are now (para 1), who they become (para 2).
Future roles this pathway positions them for.
Be direct, specific, commercially minded."""


def build_json_prompt(answers: OnboardingAnswers, anchor_courses: list[dict], graph_context: dict) -> str:
    """
    Build the pathway generation prompt with full GraphRAG context:
    - Community summaries (instructor-validated curriculum clusters)
    - Domain clusters from graph expansion
    - Cross-domain bridges
    - Semantic anchor courses (exact URLs)
    """
    # ── Community summaries ──
    comm_lines: list[str] = []
    for comm in graph_context.get("matched_communities", []):
        if comm.get("summary"):
            prog_preview = ", ".join(comm["programs"][:4])
            comm_lines.append(f"  [{prog_preview}...]\n  -> {comm['summary']}")
    community_section = "\n\n".join(comm_lines) if comm_lines else "  (run build_communities.py to generate)"

    # ── Domain clusters ──
    cluster_lines: list[str] = []
    for cl in graph_context.get("domain_clusters", []):
        cluster_lines.append(f"  [{cl['domain']}]")
        for p in cl["programs"][:5]:
            titles = ", ".join(c["title"] for c in p["courses"][:2])
            cluster_lines.append(f"    - {p['program']}: {titles}")
    cluster_section = "\n".join(cluster_lines)

    # ── Cross-domain bridges ──
    bridges_section = "\n".join(f"  - {p}" for p in graph_context.get("cross_domain_bridges", []))

    # ── Bridge instructors ──
    instr_section = "\n".join(
        f"  - {bi['instructor']}: spans {bi['domain_count']} domains, "
        f"teaches {', '.join(bi['programs'][:3])}"
        for bi in graph_context.get("bridge_instructors", [])
    )

    # ── Semantic anchor courses (exact URLs for citation) ──
    course_lines: list[str] = []
    for c in anchor_courses[:50]:
        course_lines.append(
            f"  - {c['title']} | {c['program']} | {c['instructor']} ({c.get('role','')}) "
            f"| {c['url']} | score:{c['similarity']:.2f}"
        )
    courses_section = "\n".join(course_lines)

    stats = (
        f"Searched {graph_context.get('expanded_program_count', 0)} programs "
        f"(anchored from {graph_context.get('anchor_program_count', 0)} semantic matches)"
    )

    return f"""You are a learning pathway architect for eCornell GraphRAG (2,176 Cornell courses).

STUDENT PROFILE:
- Leadership direction: {answers.q1}
- 2-year vision: {answers.q2}
- Biggest bottleneck: {answers.q3}
- Who they lead/serve: {answers.q4}
- AI/transformation challenges: {answers.q5}
- Accountable for: {answers.q6}
- Revenue target: {answers.q7}
- Value generation: {answers.q8}
- Next initiative: {answers.q9}
- Credentials: {answers.q10 or 'None'}
- Target institution: {answers.q11 or 'None'}
- Strengths/gaps: {answers.q12}
- Hours/week: {answers.q13}
- Known for: {answers.q14}

KNOWLEDGE GRAPH CONTEXT ({stats}):

Discovered Curriculum Communities (instructor-validated clusters — use these to group phases):
{community_section}

Domain Clusters:
{cluster_section}

Cross-Domain Bridges (programs spanning multiple domains - highest strategic leverage):
{bridges_section}

Bridge Instructors (teach across multiple relevant domains - use for phase transitions):
{instr_section}

SEMANTIC COURSE MATCHES (use EXACT URLs in output - do not alter):
{courses_section}

Return ONLY valid JSON. No markdown. No fences. No explanation. Use hyphens not em dashes.

{{
  "narrative_now": "2-3 sentences: where they are right now and what's holding them back",
  "narrative_future": "2-3 sentences: who they become after completing this pathway",
  "phases": [
    {{
      "number": 1,
      "name": "Phase name",
      "timeline": "Month 1-2",
      "strategic_reason": "One sentence: why this phase comes first, tied to their bottleneck",
      "courses": [
        {{
          "title": "Exact course title from the matches above",
          "program": "Program name",
          "instructor": "Instructor name",
          "url": "https://ecornell.cornell.edu/...",
          "why": "2 sentences: specific to their role, initiative, and revenue target",
          "deliverable": "One concrete asset they can ship, sell, or present after this course"
        }}
      ]
    }}
  ],
  "future_roles": ["Role 1", "Role 2", "Role 3", "Role 4"]
}}

Rules: exactly 6 phases, 4-5 courses each, all URLs from the matches above, ROI-focused, no fluff."""

# ──────────────────────────────────────────────
# CLAUDE CLI STREAMING
# ──────────────────────────────────────────────
async def _run_claude_stream(prompt: str) -> AsyncGenerator[str, None]:
    cmd = [CLAUDE_BIN, "-p", "--output-format", "stream-json", "--verbose",
           "--include-partial-messages", "--model", "claude-sonnet-4-6"]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        env={**os.environ, "HOME": CLAUDE_CLEAN_HOME},
    )
    proc.stdin.write(prompt.encode())
    await proc.stdin.drain()
    proc.stdin.close()
    sent_result = False
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        try:
            event = json.loads(line.decode().strip())
        except Exception:
            continue
        etype = event.get("type")
        if etype == "stream_event":
            inner = event.get("event", {})
            if inner.get("type") == "content_block_delta":
                delta = inner.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        sent_result = True
                        yield text
        elif etype == "result" and not sent_result:
            result_text = event.get("result", "")
            if result_text:
                yield result_text
            break
        elif etype == "result":
            break
    await proc.wait()


async def stream_pathway(answers: OnboardingAnswers) -> AsyncGenerator[str, None]:
    loop = asyncio.get_event_loop()

    yield f"data: {json.dumps({'type': 'status', 'text': 'Embedding your profile...'})}\n\n"
    profile_text = " ".join(filter(None, [
        answers.q1, answers.q2, answers.q3, answers.q4,
        answers.q5, answers.q9, answers.q14, answers.q12,
    ]))
    user_emb = await embed_query(profile_text)

    yield f"data: {json.dumps({'type': 'status', 'text': 'Finding nearest programs via graph...'})}\n\n"
    nearest_programs = await loop.run_in_executor(None, find_programs_by_embedding, user_emb, 20)

    yield f"data: {json.dumps({'type': 'status', 'text': 'Running semantic course search...'})}\n\n"
    anchor_courses = await loop.run_in_executor(None, pgvector_search, user_emb, 50)

    yield f"data: {json.dumps({'type': 'status', 'text': 'Traversing knowledge graph...'})}\n\n"
    if nearest_programs:
        graph_context = await loop.run_in_executor(
            None, graph_guided_expansion, anchor_courses, nearest_programs, answers
        )
    else:
        graph_context = await loop.run_in_executor(None, _keyword_graph_search, answers)

    n_expanded = graph_context.get("expanded_program_count", 0)
    yield f"data: {json.dumps({'type': 'status', 'text': f'Graph expanded to {n_expanded} programs. Claude is building your pathway...'})}\n\n"

    prompt = build_json_prompt(answers, anchor_courses, graph_context)
    async for chunk in _run_claude_stream(prompt):
        yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


async def stream_chat(req: ChatRequest) -> AsyncGenerator[str, None]:
    prompt = f"""You are a personalized eCornell learning advisor. Answer concisely and specifically.

STUDENT PROFILE: {req.profile}

THEIR PATHWAY (excerpt):
{req.context}

FOLLOW-UP QUESTION: {req.question}

Answer directly. Be specific to their situation."""
    async for chunk in _run_claude_stream(prompt):
        yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

# ──────────────────────────────────────────────
# EMAIL BUILDERS
# ──────────────────────────────────────────────
def _smtp_send(msg, to_email: str):
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


def _build_ack_email(name: str, answers: OnboardingAnswers) -> str:
    qa_pairs = [
        ("Leadership direction", answers.q1),
        ("2-year vision", answers.q2),
        ("Biggest bottleneck", answers.q3),
        ("Who you lead / serve", answers.q4),
        ("AI / transformation challenges", answers.q5),
        ("Accountable for delivering", answers.q6),
        ("Compensation / revenue target", answers.q7),
        ("How you generate value", answers.q8),
        ("Strategic initiative (next 6 months)", answers.q9),
        ("Credentials pursuing", answers.q10),
        ("Target institution / program", answers.q11),
        ("Strengths and gaps", answers.q12),
        ("Hours/week for learning", answers.q13),
        ("What you want to be known for", answers.q14),
    ]
    q_rows = ""
    for label, answer in qa_pairs:
        if answer and answer.strip():
            q_rows += (
                f'<tr>'
                f'<td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;font-size:12px;color:#64748b;font-weight:600;vertical-align:top;width:200px;">{_esc(label)}</td>'
                f'<td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;font-size:13px;color:#1e293b;vertical-align:top;line-height:1.6;">{_esc(answer.strip())}</td>'
                f'</tr>'
            )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:32px 16px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 16px rgba(0,0,0,0.08);max-width:600px;">
  <tr><td style="background:linear-gradient(135deg,#B31B1B 0%,#8B1515 100%);padding:36px 32px;">
    <p style="margin:0 0 4px;color:rgba(255,255,255,0.7);font-size:12px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;">eCornell GraphRAG</p>
    <h1 style="margin:0;color:#fff;font-size:24px;font-weight:700;line-height:1.3;">Your pathway is being built, {_esc(name)}</h1>
    <p style="margin:12px 0 0;color:rgba(255,255,255,0.8);font-size:14px;line-height:1.6;">GraphRAG is searching 2,176 Cornell courses. Your personalized 6-phase learning pathway will arrive within 10 minutes.</p>
  </td></tr>
  <tr><td style="padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td width="33%" style="background:#B31B1B;padding:16px 8px;text-align:center;"><div style="color:#fff;font-size:22px;font-weight:700;">2,176</div><div style="color:rgba(255,255,255,0.75);font-size:11px;text-transform:uppercase;letter-spacing:0.8px;margin-top:2px;">Courses</div></td>
      <td width="34%" style="background:#9B1717;padding:16px 8px;text-align:center;"><div style="color:#fff;font-size:22px;font-weight:700;">6</div><div style="color:rgba(255,255,255,0.75);font-size:11px;text-transform:uppercase;letter-spacing:0.8px;margin-top:2px;">Phases</div></td>
      <td width="33%" style="background:#7B1313;padding:16px 8px;text-align:center;"><div style="color:#fff;font-size:22px;font-weight:700;">682</div><div style="color:rgba(255,255,255,0.75);font-size:11px;text-transform:uppercase;letter-spacing:0.8px;margin-top:2px;">Programs</div></td>
    </tr></table>
  </td></tr>
  <tr><td style="padding:32px;">
    <p style="margin:0 0 20px;font-size:15px;color:#334155;line-height:1.7;">Here's your profile that GraphRAG is working with:</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;border-collapse:collapse;">
      <tr><td colspan="2" style="background:#f8fafc;padding:12px 16px;border-bottom:1px solid #e2e8f0;"><p style="margin:0;font-size:11px;font-weight:700;color:#B31B1B;text-transform:uppercase;letter-spacing:1px;">Your Profile</p></td></tr>
      {q_rows}
    </table>
    <div style="margin-top:28px;padding:20px 24px;background:#fef2f2;border-radius:8px;border-left:4px solid #B31B1B;">
      <p style="margin:0;font-size:14px;color:#1e293b;line-height:1.7;font-style:italic;">"The pathway arriving in your inbox is not a course catalog. It's 6 strategic phases built specifically around where you are, what you're building, and who you want to become - with every course mapped to your clients, your initiatives, and your income targets."</p>
    </div>
  </td></tr>
  <tr><td style="background:#1a1a2e;padding:24px;text-align:center;">
    <p style="margin:0 0 4px;color:#fff;font-size:13px;font-weight:600;">eCornell GraphRAG - Personalized Learning Pathways</p>
    <p style="margin:0;color:rgba(255,255,255,0.4);font-size:11px;">2,176 courses - 682 programs - cornell.learnleadai.com</p>
  </td></tr>
</table>
</td></tr>
</table></body></html>"""


def _render_course_block(course: dict) -> str:
    title       = _esc(course.get("title", ""))
    program     = _esc(course.get("program", ""))
    instructor  = _esc(course.get("instructor", ""))
    why         = _esc(course.get("why", ""))
    deliverable = _esc(course.get("deliverable", ""))
    url         = course.get("url", "")
    safe_url    = url if (url and url.startswith("https://")) else ""
    title_html  = (
        f'<a href="{safe_url}" style="color:#B31B1B;font-size:14px;font-weight:700;text-decoration:none;">{title} &rarr;</a>'
        if safe_url else
        f'<span style="color:#1e293b;font-size:14px;font-weight:700;">{title}</span>'
    )
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:8px;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">'
        f'<tr><td style="padding:14px 16px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0">'
        f'<tr><td style="padding-bottom:4px;">{title_html}</td></tr>'
        f'<tr><td style="padding-bottom:8px;">{"<span style=\"font-size:11px;color:#64748b;\">" + instructor + "</span>" if instructor else ""}{"<span style=\"font-size:11px;color:#94a3b8;margin-left:6px;\">" + program + "</span>" if program else ""}</td></tr>'
        + (f'<tr><td style="padding-bottom:6px;"><p style="margin:0;font-size:12px;color:#334155;line-height:1.6;"><strong style="color:#1e293b;">Why this fits:</strong> {why}</p></td></tr>' if why else '')
        + (f'<tr><td><p style="margin:0;font-size:12px;color:#64748b;line-height:1.6;"><strong style="color:#475569;">Deliverable unlocked:</strong> {deliverable}</p></td></tr>' if deliverable else '')
        + f'</table></td></tr></table>'
    )


_PHASE_COLORS = [
    ("#B31B1B", "#fef2f2"),
    ("#2563eb", "#eff6ff"),
    ("#059669", "#ecfdf5"),
    ("#d97706", "#fffbeb"),
    ("#7c3aed", "#f5f3ff"),
    ("#0891b2", "#ecfeff"),
]


def _build_visual_pathway_email(name: str, data: dict) -> str:
    phases           = data.get("phases", [])
    narrative_now    = _esc(data.get("narrative_now", ""))
    narrative_future = _esc(data.get("narrative_future", ""))
    future_roles     = data.get("future_roles", [])
    total_courses    = sum(len(p.get("courses", [])) for p in phases)

    phase_blocks = ""
    for i, phase in enumerate(phases):
        accent, bg = _PHASE_COLORS[i % len(_PHASE_COLORS)]
        courses    = phase.get("courses", [])
        course_blocks = "".join(_render_course_block(c) for c in courses)
        phase_name = _esc(phase.get("name", ""))
        timeline   = _esc(phase.get("timeline", ""))
        reason     = _esc(phase.get("strategic_reason", ""))
        phase_blocks += (
            f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;border-radius:10px;overflow:hidden;border:1px solid #e2e8f0;">'
            f'<tr><td style="background:{bg};padding:16px 20px;border-bottom:3px solid {accent};">'
            f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td><p style="margin:0 0 2px;font-size:10px;font-weight:700;color:{accent};text-transform:uppercase;letter-spacing:1.2px;">Phase {phase.get("number", i+1)} - {timeline}</p>'
            f'<h3 style="margin:0;font-size:16px;font-weight:700;color:#1e293b;">{phase_name}</h3></td>'
            f'<td align="right" valign="top"><span style="background:{accent};color:#fff;font-size:11px;font-weight:600;padding:3px 9px;border-radius:20px;">{len(courses)} courses</span></td>'
            f'</tr>'
            + (f'<tr><td colspan="2" style="padding-top:8px;"><p style="margin:0;font-size:12px;color:#64748b;line-height:1.5;">{reason}</p></td></tr>' if reason else '')
            + f'</table></td></tr>'
            f'<tr><td style="padding:14px 16px;background:#fff;">{course_blocks}</td></tr>'
            f'</table>'
        )

    roles_html = ""
    if future_roles:
        role_items = "".join(
            f'<tr><td style="padding:5px 0;"><table cellpadding="0" cellspacing="0"><tr>'
            f'<td style="padding-right:8px;color:#B31B1B;font-size:14px;vertical-align:top;">+</td>'
            f'<td style="font-size:13px;color:#334155;line-height:1.5;">{_esc(r)}</td>'
            f'</tr></table></td></tr>'
            for r in future_roles
        )
        roles_html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px;background:#fef2f2;border-radius:10px;overflow:hidden;border:1px solid #fecaca;">'
            f'<tr><td style="padding:16px 20px;border-bottom:2px solid #B31B1B;"><p style="margin:0;font-size:11px;font-weight:700;color:#B31B1B;text-transform:uppercase;letter-spacing:1px;">Where This Takes You</p></td></tr>'
            f'<tr><td style="padding:14px 20px;"><table cellpadding="0" cellspacing="0">{role_items}</table></td></tr>'
            f'</table>'
        )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:28px 12px;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">
  <tr><td style="background:linear-gradient(135deg,#B31B1B 0%,#8B1515 100%);padding:36px 32px;border-radius:12px 12px 0 0;">
    <p style="margin:0 0 6px;color:rgba(255,255,255,0.65);font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;">eCornell GraphRAG - Personalized Pathway</p>
    <h1 style="margin:0 0 10px;color:#fff;font-size:24px;font-weight:700;line-height:1.3;">Your 6-Phase Learning Pathway, {_esc(name)}</h1>
    <table cellpadding="0" cellspacing="0"><tr>
      <td style="padding-right:20px;text-align:center;"><div style="color:#fff;font-size:20px;font-weight:800;">{len(phases)}</div><div style="color:rgba(255,255,255,0.65);font-size:10px;text-transform:uppercase;letter-spacing:0.8px;">Phases</div></td>
      <td style="padding-right:20px;text-align:center;"><div style="color:#fff;font-size:20px;font-weight:800;">{total_courses}</div><div style="color:rgba(255,255,255,0.65);font-size:10px;text-transform:uppercase;letter-spacing:0.8px;">Courses</div></td>
      <td style="text-align:center;"><div style="color:#fff;font-size:20px;font-weight:800;">2,176</div><div style="color:rgba(255,255,255,0.65);font-size:10px;text-transform:uppercase;letter-spacing:0.8px;">Searched</div></td>
    </tr></table>
  </td></tr>
  <tr><td style="background:#fff;padding:28px 32px 20px;">
    {"<p style=\"margin:0 0 12px;font-size:14px;color:#334155;line-height:1.75;\">" + narrative_now + "</p>" if narrative_now else ""}
    {"<p style=\"margin:0;font-size:14px;color:#334155;line-height:1.75;\">" + narrative_future + "</p>" if narrative_future else ""}
  </td></tr>
  <tr><td style="background:#fff;padding:0 32px;"><hr style="border:none;border-top:1px solid #e2e8f0;margin:0;"></td></tr>
  <tr><td style="background:#fff;padding:20px 32px 12px;"><p style="margin:0;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:1.2px;">Your Learning Roadmap</p></td></tr>
  <tr><td style="background:#fff;padding:0 32px 28px;">{phase_blocks}{roles_html}</td></tr>
  <tr><td style="background:#1a1a2e;padding:22px 32px;text-align:center;border-radius:0 0 12px 12px;">
    <p style="margin:0 0 3px;color:#fff;font-size:13px;font-weight:600;">eCornell GraphRAG - cornell.learnleadai.com</p>
    <p style="margin:0;color:rgba(255,255,255,0.35);font-size:11px;">2,176 courses - 682 programs - 226 instructors</p>
  </td></tr>
</table>
</td></tr>
</table></body></html>"""


def _pathway_data_to_plain(name: str, data: dict) -> str:
    lines = [f"Your eCornell 6-Phase Learning Pathway - {name}", "=" * 60, ""]
    if data.get("narrative_now"):
        lines += [data["narrative_now"], ""]
    if data.get("narrative_future"):
        lines += [data["narrative_future"], ""]
    for phase in data.get("phases", []):
        lines += [
            f"PHASE {phase.get('number', '')} - {phase.get('name', '').upper()}",
            f"Timeline: {phase.get('timeline', '')}",
            phase.get("strategic_reason", ""), "",
        ]
        for c in phase.get("courses", []):
            lines += [
                f"  - {c.get('title', '')} ({c.get('program', '')})",
                f"    Instructor: {c.get('instructor', '')}",
                f"    Link: {c.get('url', '')}",
                f"    Why: {c.get('why', '')}",
                f"    Deliverable: {c.get('deliverable', '')}", "",
            ]
    if data.get("future_roles"):
        lines += ["WHERE THIS TAKES YOU:", ""] + [f"  + {r}" for r in data["future_roles"]]
    lines += ["", "-" * 60, "eCornell GraphRAG - cornell.learnleadai.com"]
    return "\n".join(lines)


def pathway_to_html(text: str) -> str:
    lines = text.split("\n")
    html = []
    for line in lines:
        if line.startswith("## "):
            html.append(f'<h2 style="color:#B31B1B;font-size:18px;border-bottom:2px solid #B31B1B;padding-bottom:6px;margin:24px 0 10px;">{_esc(line[3:])}</h2>')
        elif line.startswith("### "):
            html.append(f'<h3 style="color:#1e293b;font-size:15px;margin:16px 0 6px;">{_esc(line[4:])}</h3>')
        elif re.match(r"^\s*[-•]\s", line):
            content = re.sub(r"^\s*[-•]\s", "", line)
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _esc(content))
            html.append(f'<li style="margin:4px 0;font-size:13px;color:#334155;">{content}</li>')
        elif line.strip() == "---":
            html.append('<hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0;">')
        elif line.strip():
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _esc(line))
            html.append(f'<p style="font-size:13px;color:#334155;line-height:1.7;margin:6px 0;">{content}</p>')
    body = "\n".join(html)
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:20px 10px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
  <tr><td style="background:linear-gradient(135deg,#B31B1B,#8B1515);padding:32px 28px;">
    <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">Your eCornell Learning Pathway</h1>
    <p style="margin:8px 0 0;color:rgba(255,255,255,0.75);font-size:13px;">Built by GraphRAG - 2,176 courses - Personalized for you</p>
  </td></tr>
  <tr><td style="padding:28px;">{body}</td></tr>
  <tr><td style="background:#1a1a2e;padding:20px;text-align:center;">
    <p style="margin:0;color:rgba(255,255,255,0.5);font-size:11px;">eCornell GraphRAG - cornell.learnleadai.com</p>
  </td></tr>
</table>
</td></tr></table></body></html>"""

# ──────────────────────────────────────────────
# BACKGROUND GENERATION
# ──────────────────────────────────────────────
async def _generate_and_send(name: str, email: str, answers: OnboardingAnswers, sub_id: str = None):
    loop = asyncio.get_event_loop()
    try:
        if sub_id:
            await loop.run_in_executor(None, _db_update_status, sub_id, "generating")

        # ── GraphRAG pipeline: single user embedding → graph expansion → prompt ──
        # Step 1: embed the user's full profile into a single vector
        profile_text = " ".join(filter(None, [
            answers.q1, answers.q2, answers.q3, answers.q4,
            answers.q5, answers.q9, answers.q14, answers.q12,
        ]))
        user_emb = await embed_query(profile_text)

        # Step 2: nearest programs by cosine similarity (replaces keyword domain matching)
        nearest_programs = await loop.run_in_executor(
            None, find_programs_by_embedding, user_emb, 20
        )

        # Step 3: semantic anchor courses — single query replaces 8 per-theme queries
        anchor_courses = await loop.run_in_executor(None, pgvector_search, user_emb, 50)

        # Step 4: graph-guided expansion — true GraphRAG pipeline
        #         fallback to keyword search if embeddings unavailable
        if nearest_programs:
            graph_context = await loop.run_in_executor(
                None, graph_guided_expansion, anchor_courses, nearest_programs, answers
            )
        else:
            graph_context = await loop.run_in_executor(
                None, _keyword_graph_search, answers
            )

        # Step 5: build enriched prompt with community summaries
        prompt = build_json_prompt(answers, anchor_courses, graph_context)

        cmd = [CLAUDE_BIN, "-p", "--output-format", "json", "--model", "claude-sonnet-4-6"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env={**os.environ, "HOME": CLAUDE_CLEAN_HOME},
        )
        try:
            raw_output, _ = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()),
                timeout=300,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError("Claude subprocess timed out after 5 minutes")

        outer       = json.loads(raw_output.decode().strip())
        result_text = outer.get("result", "")
        result_text = re.sub(r"^```(?:json)?\s*", "", result_text.strip())
        result_text = re.sub(r"\s*```$", "", result_text.strip())
        pathway_data = json.loads(result_text)

        if pathway_data:
            msg = MIMEMultipart("alternative")
            msg["From"]    = f"{FROM_NAME} <{FROM_EMAIL}>"
            msg["To"]      = _clean_email(email)
            msg["Subject"] = f"Your 6-Phase Learning Pathway - Built for {name.split()[0]}"
            msg.attach(MIMEText(_pathway_data_to_plain(name, pathway_data), "plain", "utf-8"))
            msg.attach(MIMEText(_build_visual_pathway_email(name, pathway_data), "html", "utf-8"))
            await loop.run_in_executor(None, _smtp_send, msg, email)
            logger.info(f"pathway sent: {name} <{email}> sub_id={sub_id}")
            if sub_id:
                await loop.run_in_executor(None, _db_update_status, sub_id, "sent")

    except Exception as e:
        logger.error(f"background task failed for {email}: {e}", exc_info=True)
        if sub_id:
            try:
                await loop.run_in_executor(None, _db_update_status, sub_id, "failed")
            except Exception:
                pass
        try:
            profile_summary = (
                f"PATHWAY GENERATION FAILED\nUser: {name} <{email}>\nSub ID: {sub_id}\nError: {e}\n\nProfile:\n"
                + "\n".join(f"Q{i}: {getattr(answers, f'q{i}', '')}" for i in range(1, 15))
            )
            fallback_msg = MIMEMultipart("alternative")
            fallback_msg["From"]    = f"{FROM_NAME} <{FROM_EMAIL}>"
            fallback_msg["To"]      = ADMIN_EMAIL
            fallback_msg["Subject"] = f"[ACTION REQUIRED] Pathway failed for {name} <{email}>"
            fallback_msg.attach(MIMEText(profile_summary, "plain", "utf-8"))
            await loop.run_in_executor(None, _smtp_send, fallback_msg, ADMIN_EMAIL)
        except Exception as fallback_err:
            logger.error(f"fallback email also failed: {fallback_err}")

# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────
@app.post("/api/analyze")
async def analyze(answers: OnboardingAnswers):
    return StreamingResponse(
        stream_pathway(answers),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/search")
async def search(req: SearchRequest):
    if not req.query.strip():
        return {"results": [], "graph_context": {}, "query": req.query}

    loop = asyncio.get_event_loop()

    # Embed the query once — used for both pgvector and program matching
    emb = await embed_query(req.query)

    # Parallel: pgvector anchor courses + program embedding search
    anchor_courses, nearest_programs = await asyncio.gather(
        loop.run_in_executor(None, pgvector_search, emb, req.limit),
        loop.run_in_executor(None, find_programs_by_embedding, emb, 15),
    )

    # Graph-guided expansion: walk the graph from the semantic anchors
    graph_ctx = await loop.run_in_executor(
        None, graph_guided_expansion, anchor_courses, nearest_programs
    )

    # Build a compact graph_context for the frontend
    communities_out = [
        {
            "summary":  c["summary"],
            "programs": c["programs"][:6],
        }
        for c in graph_ctx.get("matched_communities", [])
        if c.get("summary")
    ]

    related_programs = []
    for cl in graph_ctx.get("domain_clusters", []):
        for p in cl.get("programs", [])[:4]:
            name = p.get("program", "")
            if name and name not in related_programs:
                related_programs.append(name)

    return {
        "results":       anchor_courses,
        "graph_context": {
            "communities":      communities_out[:2],
            "related_programs": related_programs[:12],
            "bridges":          graph_ctx.get("cross_domain_bridges", [])[:5],
            "expanded_count":   graph_ctx.get("expanded_program_count", 0),
        },
        "query": req.query,
        "total": len(anchor_courses),
    }


@app.post("/api/send-pathway")
async def send_pathway(req: SendPathwayRequest):
    if not _valid_email(req.to_email):
        return {"ok": False, "error": "Invalid email address"}
    html_body = pathway_to_html(req.pathway_text)
    msg = MIMEMultipart("alternative")
    msg["From"]     = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"]       = _clean_email(req.to_email)
    msg["Subject"]  = req.subject
    msg["Reply-To"] = FROM_EMAIL
    msg.attach(MIMEText(req.pathway_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _smtp_send, msg, req.to_email)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/submit-profile")
@limiter.limit("5/hour")
async def submit_profile(request: Request, req: ProfileSubmission):
    clean_email = _clean_email(req.email)
    clean_name  = _clean_name(req.name)
    if not _valid_email(clean_email):
        return {"ok": False, "error": "Invalid email address"}
    if not clean_name:
        return {"ok": False, "error": "Name is required"}

    answers = OnboardingAnswers(
        q1=req.q1, q2=req.q2, q3=req.q3, q4=req.q4,
        q5=req.q5, q6=req.q6, q7=req.q7, q8=req.q8,
        q9=req.q9, q10=req.q10, q11=req.q11,
        q12=req.q12, q13=req.q13, q14=req.q14,
    )

    sub_id = None
    try:
        loop = asyncio.get_running_loop()
        sub_id = await loop.run_in_executor(None, _db_insert_submission, clean_name, clean_email, answers)
        logger.info(f"submission received: {clean_name} <{clean_email}> sub_id={sub_id}")
    except Exception as db_err:
        logger.error(f"DB insert failed: {db_err}")

    try:
        ack_html = _build_ack_email(clean_name, answers)
        msg = MIMEMultipart("alternative")
        msg["From"]    = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"]      = clean_email
        msg["Subject"] = f"Your Learning Pathway is Being Built, {clean_name.split()[0]}"
        msg.attach(MIMEText(ack_html, "html", "utf-8"))
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _smtp_send, msg, clean_email)
    except Exception as e:
        return {"ok": False, "error": f"Email failed: {e}"}

    asyncio.create_task(_generate_and_send(clean_name, clean_email, answers, sub_id))
    return {"ok": True}


@app.post("/api/retry")
async def retry_submission(req: RetryRequest):
    if req.admin_key != ADMIN_KEY:
        return {"ok": False, "error": "Unauthorized"}
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"{SUPA_URL}/rest/v1/cornell_submissions?id=eq.{req.sub_id}&select=name,email,answers",
                headers=_supa_headers(),
            )
            resp.raise_for_status()
            rows = resp.json()
        if not rows:
            return {"ok": False, "error": "Submission not found"}
        name, email, answers_dict = rows[0]["name"], rows[0]["email"], rows[0]["answers"]
        answers = OnboardingAnswers(**answers_dict)
        asyncio.create_task(_generate_and_send(name, email, answers, req.sub_id))
        logger.info(f"retry triggered: {name} <{email}> sub_id={req.sub_id}")
        return {"ok": True, "message": f"Retrying pathway for {name}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    return StreamingResponse(
        stream_chat(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/courses")
async def get_courses(q: str = "", program: str = "", limit: int = 50):
    limit   = min(max(limit, 1), 200)
    results = _COURSES_LITE
    if q:
        q_lower = q.lower()
        results = [
            c for c in results
            if q_lower in c.get("title", "").lower() or q_lower in c.get("program", "").lower()
        ]
    if program:
        results = [c for c in results if c.get("program", "") == program]
    return {"courses": results[:limit], "total": len(results)}


@app.get("/api/health")
async def health():
    return {"status": "ok", "courses": len(_COURSES_LITE)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3456, log_level="info")
