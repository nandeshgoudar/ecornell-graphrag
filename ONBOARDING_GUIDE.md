# eCornell GraphRAG — Personalized Learning Pathway Guide
### For Cornell Classmates | Built by Nandesh Goudar

---

## What Is This?

This is a **semantic search system** built on top of all 2,176 eCornell courses.

Instead of browsing a catalog, you answer a series of questions about where you're going — career goals, clients, business, income targets — and the system finds the courses from across every program that are most relevant to *your specific situation*. It then generates a personalized **6-phase learning pathway**, a **PDF report** with course links and use cases, and emails it to you.

**Powered by:**
- A knowledge graph of 2,176 courses × 682 programs × 226 instructors (`graph.json`)
- OpenAI `text-embedding-3-large` — converts every course into a 1,536-dimension vector
- Supabase pgvector — stores and searches embeddings by cosine similarity
- Claude — interprets your answers and builds the pathway
- Brevo SMTP — delivers your report to your inbox

---

## The Complete Workflow (What We Built, Step by Step)

```
Step 1  Scrape eCornell catalog        →  graph.json (courses + programs + instructors)
Step 2  Flatten graph for embedding    →  courses_for_embedding.json (2,176 text records)
Step 3  Embed with OpenAI              →  courses_embedded.jsonl (run: embed_courses.py)
Step 4  Insert into Supabase pgvector  →  ecornell_embeddings table (run: insert_embeddings.py)
Step 5  Semantic search                →  search_courses.py "your query here"
Step 6  Build 6-phase learning plan    →  Claude analyzes your answers + search results
Step 7  Generate PDF report            →  generate_report.py → learning_pathway_report.pdf
Step 8  Send personalized email        →  send_email.py → your inbox with PDF attached
```

---

## Part 1 — The Onboarding Questions

These are the exact questions we asked Nandesh. Answer them honestly and specifically — the more detail you give, the better the course matching.

---

### Section A: Career Vision

**Q1. What is the career or business direction you are actively building toward?**

*Be specific — not "I want to be successful" but what role, what industry, what kind of work.*

Example: *"I'm building a productivity consulting practice targeting SME business owners. I want to be the go-to person at the intersection of AI adoption and human performance."*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

**Q2. What does your professional life look like in 2 years? In 5 years?**

*Think in terms of: who you're working with, what you're being paid to do, what credential or title you hold, what you're known for.*

Example: *"In 2 years — running AI workshops for 3-4 corporate clients per quarter at $4,000/workshop. In 5 years — Director of Learning Strategy at a scale-up, or running a $500K/year training company."*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

**Q3. What is your single biggest professional bottleneck right now?**

*What's the one thing that, if solved, would unlock the most growth?*

Example: *"I have clients but I can't articulate what makes my methodology different from any other coach. I need intellectual credibility — not just results."*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

### Section B: Current Work & Clients

**Q4. Who are your current clients or employers? What do they pay you for?**

*Name the types of clients (or companies). What problem do you solve for them?*

Example: *"Three clients: (1) executive coach building a nervous system recovery program, (2) compliance advisory firm doing cold outreach via LinkedIn, (3) my own workshops for real estate agents and clinic owners."*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

**Q5. What tools, platforms, or methods are central to your work right now?**

*This helps map which courses will have the most immediate practical application.*

Example: *"GoHighLevel for client CRM, ScoreApp for lead qualification, Clay + Expandi for LinkedIn outreach, Claude + GPT-4 for content generation."*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

**Q6. What is a typical deliverable you give to a client?**

*A report? A workshop? A system? A strategy document? Code?*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

### Section C: Revenue & Business Model

**Q7. What are your current and target income levels?**

*Be honest — the pathway is calibrated to help you get there.*

Example: *"Currently $4,000–6,000/month. Target: $25,000/month within 18 months, with $225,000 annual target across workshops, retainers, and digital products."*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

**Q8. How do you (or do you want to) make money? What's the revenue model?**

*Freelance? Salary? Workshops? SaaS? Consulting retainer? Course sales?*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

**Q9. What new product, service, or offer are you trying to build in the next 6 months?**

*This tells the system which courses to prioritize for immediate ROI.*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

### Section D: Academic & Credential Goals

**Q10. What academic credentials or certifications are you pursuing or considering?**

*Cornell certificates? Graduate school? MBA? Professional designations (PMP, CFA, etc.)?*

Example: *"I don't have a traditional bachelor's degree. I want a pathway into a Canadian graduate program — ideally an Executive MBA or graduate certificate in AI/business within 2 years."*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

**Q11. Is there a specific university, country, or program type you are targeting?**

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

### Section E: Personal Context

**Q12. What is your background — what do you already know well?**

*This prevents recommending introductory courses in areas you've already mastered.*

Example: *"Strong in sales, cold outreach automation, AI tools, client management. Weak in formal data science, financial modeling, academic research methods."*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

**Q13. How many hours per week can you realistically dedicate to learning?**

*This calibrates the timeline and phase pacing.*

Example: *"5–8 hours per week. More during slow client weeks. I prefer 20–30 minute course modules I can do on commutes."*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

**Q14. What is one thing you want to be known for — your "intellectual brand"?**

*The thing you want people to associate with your name professionally.*

Example: *"The AI productivity leader who uses behavioral science, not just productivity hacks. Someone with actual credentials, not just content."*

Your answer:
```
[WRITE YOUR ANSWER HERE]
```

---

## Part 2 — How to Run The System

### Prerequisites

```bash
pip install openai reportlab edge-tts
```

You also need:
- SSH access to the Hetzner server (ask Nandesh)
- A Brevo account (free tier works) or swap in your own SMTP
- OpenAI API key (for embedding your queries)

---

### Step 1: Search for Courses Matching Your Goals

Once you've answered the questions above, run semantic searches against the embedded catalog:

```bash
# From the project root
python search_courses.py "behavioral science for executive coaching"
python search_courses.py "AI adoption change management for consultants"
python search_courses.py "data analytics for marketing strategy"
python search_courses.py "sustainable business for ESG advisory"
```

Each search returns the top 10 most semantically similar courses with similarity scores.

**Tip:** Run 6–10 searches targeting different aspects of your career goals. Collect the course titles that appear most relevant.

---

### Step 2: Feed Your Answers + Search Results to Claude

Copy your answers from Part 1 and paste them into Claude with this prompt:

---

#### THE MASTER PROMPT — Paste This Into Claude

```
I've answered a career onboarding questionnaire and I want you to build me a personalized 6-phase eCornell learning pathway.

Here are my answers:

**Career Vision:**
[Paste Q1–Q3 answers]

**Current Work & Clients:**
[Paste Q4–Q6 answers]

**Revenue & Business Model:**
[Paste Q7–Q9 answers]

**Academic Goals:**
[Paste Q10–Q11 answers]

**Personal Context:**
[Paste Q12–Q14 answers]

Here are the top course search results from the eCornell GraphRAG system:
[Paste your search results]

Based on all of the above, please:

1. Identify the 6 strategic dimensions most relevant to where I'm going
2. Assign 4–6 courses per phase from the search results (or suggest additional semantic queries I should run)
3. For each course, explain:
   - Why it's relevant to MY specific situation (not generic)
   - Which client or project it maps to directly
   - What new workflow, deliverable, or offer it enables
   - A LinkedIn content angle it unlocks
4. Write a 2-paragraph career narrative: where I am now, and who I become after 6 months of this
5. Identify which future roles or credentials this pathway positions me for
```

---

### Step 3: Generate Your PDF Report

Edit `generate_report.py` with your personalized data (course list, phase names, your name) and run:

```bash
python generate_report.py
# Output: learning_pathway_report.pdf
```

---

### Step 4: Send Yourself the Email

Edit `send_email.py` — change `TO_EMAIL` to your address and `FROM_NAME` to your name:

```python
FROM_NAME = "eCornell Personalized Learning"
TO_EMAIL = "your@email.com"
```

Then run:

```bash
python send_email.py
# You'll receive the email with PDF in your inbox
```

---

## Part 3 — Example Search Queries by Career Type

Use these as starting points for your semantic searches:

### If you're in Consulting / Advisory:
```
python search_courses.py "strategic leadership for consultants"
python search_courses.py "client communication and influence"
python search_courses.py "organizational change management"
python search_courses.py "business analytics for advisory services"
```

### If you're in Tech / Product:
```
python search_courses.py "product strategy and innovation"
python search_courses.py "AI product management"
python search_courses.py "data science for product decisions"
python search_courses.py "user behavior and UX research"
```

### If you're in Marketing / Growth:
```
python search_courses.py "digital marketing strategy"
python search_courses.py "behavioral pricing and conversion"
python search_courses.py "content marketing and brand building"
python search_courses.py "marketing analytics and attribution"
```

### If you're in Finance / Investment:
```
python search_courses.py "financial modeling and valuation"
python search_courses.py "investment analysis and portfolio management"
python search_courses.py "ESG investing and sustainable finance"
python search_courses.py "risk management and governance"
```

### If you're building a startup:
```
python search_courses.py "entrepreneurship and venture strategy"
python search_courses.py "go to market strategy for startups"
python search_courses.py "fundraising and investor relations"
python search_courses.py "lean product development"
```

### If you're in Healthcare / Biotech:
```
python search_courses.py "healthcare leadership and operations"
python search_courses.py "clinical decision making and evidence based practice"
python search_courses.py "health informatics and digital health"
```

---

## Part 4 — What Your Output Looks Like

When the system is done, you get three things:

### 1. A 6-Phase Learning Pathway
Each phase is a strategic cluster of 4–6 courses that builds on the previous. Named for what it gives you — not the department it comes from. Example from Nandesh's plan:

| Phase | Timeline | Focus | Strategic Purpose |
|-------|----------|-------|-------------------|
| 1 | Month 1–2 | Psychology & Behavioral Science | Intellectual foundation — understand *why* people behave the way they do |
| 2 | Month 2–3 | AI Adoption & Change Management | Competitive moat — lead organizations through the AI shift |
| 3 | Month 3–4 | Strategic Leadership & Productivity | Become the leader, not the practitioner |
| 4 | Month 4–5 | Marketing & Content Strategy | Monetize everything you know via content and offers |
| 5 | Month 5 | Sustainability & ESG | Differentiator nobody else has |
| 6 | Month 5–6 | Data Science for Decision Making | Technical credibility, analytical authority |

### 2. A PDF Report
- Every course with a direct link
- Why each course was chosen for you specifically
- Client/employer application for each course
- LinkedIn post ideas from each course
- Suggested assignments and real-world applications
- Career narrative: where you are vs. where this takes you

### 3. An Email in Your Inbox
Beautiful Cornell-branded HTML email with PDF attached. Share it with anyone who asks "what are you studying and why."

---

## Part 5 — How the GraphRAG Actually Works

### The Knowledge Graph
```
graph.json contains:
  - Nodes: courses, programs, instructors
  - Edges: course → belongs_to → program
           course → taught_by → instructor
  - 2,176 courses across every eCornell subject area
```

### The Embedding Pipeline
```
courses_for_embedding.json
  Each record: { id, title, program, instructor, role, text }
  text = "Course: [title]. Program: [program]. Instructor: [name], [role]."

embed_courses.py
  → OpenAI text-embedding-3-large (1536 dimensions)
  → Saves to courses_embedded.jsonl

insert_embeddings.py
  → Reads JSONL
  → Inserts into Supabase table: ecornell_embeddings
  → Column: embedding vector(1536)
```

### The Search
```
search_courses.py "your query"
  1. Embeds your query with the same model (text-embedding-3-large)
  2. Runs pgvector cosine similarity: 1 - (embedding <=> query_vector)
  3. Returns top 10 courses sorted by similarity score
  4. Score of 0.6+ = highly relevant | 0.4–0.6 = relevant | below 0.4 = loose match
```

---

## Quick Reference: Files in This Project

| File | What it does |
|------|-------------|
| `graph.json` | Knowledge graph: 2,176 courses × programs × instructors |
| `courses_for_embedding.json` | Flattened text records ready for embedding |
| `embed_courses.py` | Calls OpenAI to embed all courses → JSONL |
| `courses_embedded.jsonl` | Output: courses with their 1536-dim vectors |
| `insert_embeddings.py` | Inserts JSONL into Supabase pgvector table |
| `search_courses.py` | Semantic search — run this to find relevant courses |
| `generate_report.py` | Builds the PDF learning pathway report |
| `send_email.py` | Sends email with PDF via Brevo SMTP |
| `comprehensive_career_email.py` | Extended version: client use cases + podcast audio |

---

## FAQ

**Do I need to re-run the embedding pipeline?**
No. The courses are already embedded and stored in Supabase. Just run `search_courses.py`.

**What if I want different courses than what comes up?**
Run more searches with different queries. Try synonyms, specific skills, or industry terms. The more angles you search from, the richer your course pool.

**Can I use this for a different learning platform?**
Yes — swap out the course data in `graph.json` and re-run `embed_courses.py`. The pipeline is platform-agnostic.

**How accurate is the matching?**
Very accurate for semantic meaning. A search for "negotiation" finds courses on persuasion, influence, deal-making, and conflict resolution — not just courses with "negotiation" in the title.

**What if I don't have a clear career direction yet?**
That's fine. Answer what you do know and be explicit about your uncertainty. Claude will ask follow-up questions and suggest exploratory options rather than a rigid pathway.

---

*Built by Nandesh Goudar | Antigravity Dev Team | Cornell eCornell GraphRAG v1.0*
*Infrastructure: Supabase pgvector on Hetzner | cornell.learnleadai.com*
