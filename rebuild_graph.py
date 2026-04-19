"""
rebuild_graph.py — Rebuilds graph.json with a richer knowledge graph.

Idempotent: strips old domain nodes and domain-derived edges before
re-computing, so it can be run multiple times safely.
TOPIC_OVERLAP edges (added by add_topic_overlap.py) are preserved.

Adds:
  - 18 domain hub nodes (expanded from original 15)
  - BELONGS_TO_DOMAIN links (program → domain)
  - SHARES_INSTRUCTOR links (program ↔ program, when they share an instructor)
  - SAME_DOMAIN links (program ↔ program, same domain AND shared instructor)

New domains vs original:
  - domain:sales     — Sales & Revenue (split out from domain:marketing)
  - domain:wine      — Wine & Viticulture
  - domain:cannabis  — Cannabis & Hemp
  - domain:creative  — Creative Arts & Film
"""

import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

BASE = Path(__file__).parent

# ── Domain definitions ──────────────────────────────────────────────────────
# Must match DOMAIN_MAP in index.html exactly (same order, same keys).
# First match wins — order matters.
DOMAINS = [
    {
        "id": "domain:ai_tech", "name": "AI & Technology",
        "keys": ["ai ","artificial intelligence","machine learning","cybersecurity","cyber",
                 "digital transformation","technology","data science","algorithm","automation",
                 "robotics","blockchain","cloud","5g","deepfake","telemedicine","fintech"],
    },
    {
        "id": "domain:marketing", "name": "Marketing & Sales",
        "keys": ["marketing","brand","advertising","content","seo","social media","digital media",
                 "campaign","consumer","market research","public relations","pr ","copywriting",
                 "fashion","targeting","segmentation","customer journey","positioning","pricing strategy"],
    },
    {
        "id": "domain:sales", "name": "Sales & Revenue",
        "keys": ["sales","revenue","business development","negotiation","crm","account management",
                 "pipeline","cold calling","key account","winning with"],
    },
    {
        "id": "domain:leadership", "name": "Leadership & Strategy",
        "keys": ["leadership","executive","strategic","strategy","organizational","influence",
                 "decision","coaching","mentoring","change management","culture","vision",
                 "public sector","systems thinking","systemic","vuca","adaptive","leading",
                 "courage","humility","credibility","authority","accountability",
                 "ancient rome","happiness as a leader"],
    },
    {
        "id": "domain:finance", "name": "Finance & Accounting",
        "keys": ["finance","financial","accounting","investment","portfolio","budget","cash flow",
                 "valuation","equity","capital","tax","audit","balance sheet","p&l","economic",
                 "economics","monopoly","equilibrium","scarcity","mergers","synergies","securities",
                 "fintech trends","time value of money","stock","fiduciary"],
    },
    {
        "id": "domain:hr", "name": "HR & People",
        "keys": ["human resources","hr ","hiring","recruitment","dei","diversity","inclusion",
                 "talent","compensation","workforce","employee","performance management","people",
                 "behavioral science","emotion","emotional intelligence","mediation","counseling",
                 "bias","eliciting","onboarding","labor relations","engagement","family relationships"],
    },
    {
        "id": "domain:healthcare", "name": "Healthcare",
        "keys": ["healthcare","health ","medical","clinical","nursing","patient","pharma",
                 "public health","hospital","wellness","obesity","nutrition","cancer","immunity",
                 "medicinal plant","senior living","metabolic","cardiovascular","digestive",
                 "skin health","atherosclerosis","endocannabinoid","food allergy","plant-based",
                 "herbal","botanical medicine","bones","reproductive"],
    },
    {
        "id": "domain:legal", "name": "Legal & Compliance",
        "keys": ["law","legal","compliance","regulatory","regulation","antitrust","contract",
                 "intellectual property","privacy","ethics","governance","trade secret","trademark",
                 "patent","securities registration","jury","litigation","international agreement",
                 "rule system","policing","rule design","violations"],
    },
    {
        "id": "domain:esg", "name": "Sustainability & ESG",
        "keys": ["sustainability","climate","esg","environmental","green","carbon","energy",
                 "renewable","social impact","nonprofit","csr","preservation","historic preservation",
                 "agriculture","horticulture","plant selection","soil","insects","weeds",
                 "outdoor cultivation","site assessment","planting plan","sustainable","human rights"],
    },
    {
        "id": "domain:ops", "name": "Project Management",
        "keys": ["project management","agile","scrum","operations","supply chain","process",
                 "logistics","quality","lean","six sigma","program management","project risk",
                 "project pitch","monitoring project","project team","project outcomes","scope",
                 "organizing project","resource planning"],
    },
    {
        "id": "domain:startup", "name": "Entrepreneurship",
        "keys": ["entrepreneur","startup","venture","innovation","product design",
                 "product engineering","product prototype","business model","ideation","incubator",
                 "beverage","beer","brewing","craft","hops","yeast","fermentation","water profile",
                 "commercialization","pitching","feasibility","emerging market",
                 "value proposition","distribution channel"],
    },
    {
        "id": "domain:comms", "name": "Communication",
        "keys": ["communication","writing","presentation","public speaking","conflict","feedback",
                 "listening","negotiating","storytell","podcast","op-ed","narrative",
                 "persuasive speaking","media support","dialogue","subtext","voice and point",
                 "slide deck","slides for impact","convincing case"],
    },
    {
        "id": "domain:data", "name": "Data & Analytics",
        "keys": ["data ","analytics","statistics","quantitative","visualization","bi ",
                 "business intelligence","tableau","excel","python","sql","statistical",
                 "regression","hypothesis testing","sampling","forecasting","probability",
                 "queueing","multivariable","distributions","econometric",
                 "market response modeling","interpreting data"],
    },
    {
        "id": "domain:realestate", "name": "Real Estate",
        "keys": ["real estate","property","construction","facility","senior facilit"],
    },
    {
        "id": "domain:education", "name": "Education",
        "keys": ["education","teaching","learning","curriculum","academic","university","training"],
    },
    # ── New domains ──────────────────────────────────────────────────────────
    {
        "id": "domain:wine", "name": "Wine & Viticulture",
        "keys": ["wine","vineyard","viticulture","grape varietals","winery","oenology",
                 "sommelier","wine production","evaluating wine","wine essentials","wine ingredient"],
    },
    {
        "id": "domain:cannabis", "name": "Cannabis & Hemp",
        "keys": ["cannabis","hemp","cannabinoid","endocannabinoid system","marijuana","cbd",
                 "hemp biology","hemp genetics","hemp breeding","hemp propagation","hemp cultivation",
                 "hemp market","cannabis legislation","cannabis production"],
    },
    {
        "id": "domain:creative", "name": "Creative Arts & Film",
        "keys": ["photography","cinematography","film","camera","lighting","scene","screenplay",
                 "image and action","world-building","character development","creative writing",
                 "dialogue","voice and point of view","creative arts","visual storytelling",
                 "style and expression","professional photography"],
    },
    # ── Catch-all (must remain last) ─────────────────────────────────────────
    {
        "id": "domain:other", "name": "Other",
        "keys": [],
    },
]

DOMAIN_IDS = {d["id"] for d in DOMAINS}

# Relations that are rebuilt every run (strip before re-adding)
REBUILT_RELATIONS = {"BELONGS_TO_DOMAIN", "SHARES_INSTRUCTOR", "SAME_DOMAIN"}


def match_domain(name: str) -> str:
    """Return domain id for program name (first keyword match wins)."""
    lower = name.lower()
    for domain in DOMAINS:
        for key in domain["keys"]:
            if key in lower:
                return domain["id"]
    return "domain:other"


def main():
    graph_path = BASE / "graph.json"

    with open(graph_path, encoding="utf-8") as f:
        graph = json.load(f)

    all_nodes = graph["nodes"]
    all_links = graph["links"]

    print(f"Loaded graph: {len(all_nodes)} nodes, {len(all_links)} links")

    # ── Strip old domain nodes and rebuilt-relation edges (idempotent) ────────
    core_nodes = [n for n in all_nodes if n.get("type") != "domain"]
    core_links = [l for l in all_links if l.get("relation") not in REBUILT_RELATIONS]

    programs    = [n for n in core_nodes if n.get("type") == "program"]
    courses     = [n for n in core_nodes if n.get("type") == "course"]
    instructors = [n for n in core_nodes if n.get("type") == "instructor"]

    print(f"  Core nodes — Programs: {len(programs)}, Courses: {len(courses)}, "
          f"Instructors: {len(instructors)}")
    print(f"  Preserved links: {len(core_links)}")

    # ── Build domain nodes ────────────────────────────────────────────────────
    domain_nodes = [{"id": d["id"], "name": d["name"], "type": "domain"} for d in DOMAINS]

    # ── BELONGS_TO_DOMAIN links (program → domain) ───────────────────────────
    program_domain: dict[str, str] = {}
    belongs_to_domain_links: list[dict] = []

    for prog in programs:
        pid   = prog["id"]
        pname = prog.get("name", "")
        did   = match_domain(pname)
        program_domain[pid] = did
        belongs_to_domain_links.append({
            "source":   pid,
            "target":   did,
            "relation": "BELONGS_TO_DOMAIN",
        })

    # ── Build instructor → programs map ──────────────────────────────────────
    course_program:     dict[str, str] = {}
    course_instructor:  dict[str, str] = {}

    for link in core_links:
        rel = link.get("relation")
        src = link.get("source")
        tgt = link.get("target")
        if rel == "BELONGS_TO":
            course_program[src] = tgt
        elif rel == "TAUGHT_BY":
            course_instructor[src] = tgt

    instructor_programs: dict[str, set] = defaultdict(set)
    for cid, iid in course_instructor.items():
        pid = course_program.get(cid)
        if pid:
            instructor_programs[iid].add(pid)

    # ── SHARES_INSTRUCTOR links ───────────────────────────────────────────────
    shares_instructor_links: list[dict] = []
    seen_pairs: set[tuple] = set()

    for iid, prog_set in instructor_programs.items():
        if len(prog_set) < 2:
            continue
        for p1, p2 in combinations(sorted(prog_set), 2):
            pair = (p1, p2)
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                shares_instructor_links.append({
                    "source":     p1,
                    "target":     p2,
                    "relation":   "SHARES_INSTRUCTOR",
                    "instructor": iid,
                })

    # ── SAME_DOMAIN links (same domain AND shared instructor) ─────────────────
    same_domain_links:   list[dict] = []
    seen_domain_pairs:   set[tuple] = set()

    for link in shares_instructor_links:
        p1, p2 = link["source"], link["target"]
        if program_domain.get(p1) == program_domain.get(p2):
            pair = (p1, p2)
            if pair not in seen_domain_pairs:
                seen_domain_pairs.add(pair)
                same_domain_links.append({
                    "source":   p1,
                    "target":   p2,
                    "relation": "SAME_DOMAIN",
                    "domain":   program_domain[p1],
                })

    # ── Assemble ──────────────────────────────────────────────────────────────
    new_nodes = core_nodes + domain_nodes
    new_links = (
        core_links
        + belongs_to_domain_links
        + shares_instructor_links
        + same_domain_links
    )

    graph["nodes"] = new_nodes
    graph["links"] = new_links

    with open(str(graph_path), "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, separators=(",", ":"))

    # ── Stats ─────────────────────────────────────────────────────────────────
    from collections import Counter
    rel_counts = Counter(l["relation"] for l in new_links)

    domain_prog_counts: dict[str, int] = defaultdict(int)
    for did in program_domain.values():
        domain_prog_counts[did] += 1

    other_count    = domain_prog_counts.get("domain:other", 0)
    all_prog_ids   = {p["id"] for p in programs}
    si_touched     = {l["source"] for l in shares_instructor_links} | \
                     {l["target"] for l in shares_instructor_links}
    isolated_count = len(all_prog_ids - si_touched)

    print(f"\n=== New graph.json stats ===")
    print(f"Total nodes : {len(new_nodes)}")
    print(f"  domain    : {len(domain_nodes)}")
    print(f"  program   : {len(programs)}")
    print(f"  course    : {len(courses)}")
    print(f"  instructor: {len(instructors)}")
    print(f"\nTotal links : {len(new_links)}")
    for rel, cnt in sorted(rel_counts.items()):
        print(f"  {rel:<25} {cnt}")

    print(f"\nDomain distribution:")
    for d in DOMAINS:
        cnt = domain_prog_counts.get(d["id"], 0)
        print(f"  {d['name']:<30} {cnt} programs")

    print(f"\nPrograms landing in 'Other' domain : {other_count}")
    print(f"Programs with NO instructor-sharing : {isolated_count}  (out of {len(programs)})")
    print(f"\nWrote {graph_path}")


if __name__ == "__main__":
    main()
