"""Generate the eCornell Learning Pathway PDF report."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

import os

OUTPUT = os.environ.get("REPORT_OUTPUT", "learning_pathway_report.pdf")

# Colors
CORNELL_RED = colors.HexColor("#B31B1B")
DARK_BG = colors.HexColor("#1a1a2e")
ACCENT_BLUE = colors.HexColor("#4f8cf7")
ACCENT_GREEN = colors.HexColor("#34d399")
ACCENT_ORANGE = colors.HexColor("#f59e42")
LIGHT_GRAY = colors.HexColor("#f5f5f5")
MEDIUM_GRAY = colors.HexColor("#666666")
WHITE = colors.white

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle', parent=styles['Title'],
    fontSize=28, leading=34, textColor=CORNELL_RED,
    spaceAfter=6, alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)
subtitle_style = ParagraphStyle(
    'CustomSubtitle', parent=styles['Normal'],
    fontSize=14, leading=18, textColor=MEDIUM_GRAY,
    spaceAfter=20, alignment=TA_CENTER,
    fontName='Helvetica'
)
heading1_style = ParagraphStyle(
    'Heading1Custom', parent=styles['Heading1'],
    fontSize=20, leading=24, textColor=CORNELL_RED,
    spaceBefore=24, spaceAfter=12,
    fontName='Helvetica-Bold',
    borderWidth=0, borderPadding=0,
    borderColor=CORNELL_RED,
)
heading2_style = ParagraphStyle(
    'Heading2Custom', parent=styles['Heading2'],
    fontSize=15, leading=19, textColor=ACCENT_BLUE,
    spaceBefore=16, spaceAfter=8,
    fontName='Helvetica-Bold'
)
heading3_style = ParagraphStyle(
    'Heading3Custom', parent=styles['Heading3'],
    fontSize=12, leading=15, textColor=ACCENT_ORANGE,
    spaceBefore=10, spaceAfter=6,
    fontName='Helvetica-Bold'
)
body_style = ParagraphStyle(
    'BodyCustom', parent=styles['Normal'],
    fontSize=10, leading=14, textColor=colors.black,
    spaceAfter=8, alignment=TA_JUSTIFY,
    fontName='Helvetica'
)
body_bold = ParagraphStyle(
    'BodyBold', parent=body_style,
    fontName='Helvetica-Bold'
)
link_style = ParagraphStyle(
    'LinkStyle', parent=body_style,
    fontSize=9, textColor=ACCENT_BLUE,
)
quote_style = ParagraphStyle(
    'QuoteStyle', parent=body_style,
    fontSize=11, leading=15, textColor=CORNELL_RED,
    fontName='Helvetica-Oblique',
    leftIndent=20, rightIndent=20,
    spaceBefore=12, spaceAfter=12,
    alignment=TA_CENTER,
)
linkedin_style = ParagraphStyle(
    'LinkedInStyle', parent=body_style,
    fontSize=10, leading=13, textColor=ACCENT_BLUE,
    fontName='Helvetica-Oblique',
    leftIndent=15, borderWidth=2,
    borderColor=ACCENT_BLUE, borderPadding=8,
)
small_style = ParagraphStyle(
    'SmallStyle', parent=body_style,
    fontSize=8, leading=10, textColor=MEDIUM_GRAY,
)

COURSES = {
    "phase1": [
        {
            "title": "Explore the Psychology of Daily Decision Making",
            "program": "Introduction to Behavioral Science",
            "instructor": "Manoj Thomas",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=JCB651OD3",
            "why": "This is the intellectual bedrock of everything you'll build. Understanding how humans make decisions — the shortcuts, the irrationalities, the emotional triggers — is what separates a productivity guru from a productivity influencer. When you teach people how to be more productive, you're really teaching them to make better decisions faster. This course gives you the science to back every claim.",
            "assignments": "Map your own daily decision fatigue points over one week. Identify the 3 biggest productivity killers and trace them to specific cognitive patterns from the course.",
            "applications": "Build a 'Decision Audit' framework for your consulting clients. Create a productivity assessment tool based on behavioral patterns. Use this in your gamified mind-map product as the scoring engine.",
            "linkedin": "\"I just learned why you can't focus after lunch — and it has nothing to do with food coma. Here's what Cornell's behavioral science research says about decision fatigue (and the 3-minute fix that actually works).\"",
            "leadership": "You'll speak with scientific authority on productivity. When a CEO asks 'why can't my team execute?' you'll diagnose the behavioral root cause, not just prescribe another Kanban board."
        },
        {
            "title": "Evaluate Cognitive Biases and Apply Remedies",
            "program": "Leveraging Problem-Solver Profiles",
            "instructor": "Cheryl Strauss Einhorn",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=JCB441OD2",
            "why": "Bias is the invisible tax on productivity. Every time a team makes a slow decision, it's usually because cognitive biases are creating friction — confirmation bias makes people research longer than needed, anchoring bias makes them fixate on wrong priorities. This course teaches you to see what others can't.",
            "assignments": "Audit a real team meeting for bias patterns. Document 5 specific instances where bias slowed decisions or created unnecessary work. Propose remedies.",
            "applications": "Develop a 'Bias-Free Meeting Protocol' that teams can adopt. This becomes a signature framework for your LinkedIn brand. Integrate bias detection prompts into your AI marketing tools.",
            "linkedin": "\"Your team isn't slow because they're lazy. They're slow because of anchoring bias. Here's the one-page protocol I use to cut meeting time by 40% — backed by Cornell research.\"",
            "leadership": "You become the person who can walk into any organization and immediately see the invisible productivity drains that nobody else notices. That's a superpower."
        },
        {
            "title": "Explore the Best Research Methods to Predict Consumer Behavior",
            "program": "Introduction to Behavioral Science",
            "instructor": "Manoj Thomas",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=JCB651OD1",
            "why": "This bridges psychology into marketing. If you're going to be the AI marketing leader, you need to understand HOW to measure and predict what people will do — not just theorize about it. This is the data layer under your behavioral science knowledge.",
            "assignments": "Design a research study for one of your Antigravity clients. Define hypotheses about their customer behavior and propose methods to test them.",
            "applications": "Build automated consumer behavior prediction models into your AI marketing stack. Use these methods to validate your gamified product's engagement mechanics before building them.",
            "linkedin": "\"Stop guessing what your customers want. Here are 3 research methods from Cornell's behavioral science program that predict buying behavior with 80%+ accuracy.\"",
            "leadership": "You'll have the methodological rigor to back your marketing recommendations with data, not just intuition. This separates consultants from thought leaders."
        },
        {
            "title": "Guide Your Customers' Emotions",
            "program": "Using Behavioral Science to Influence Customer Behavior Online",
            "instructor": "Manoj Thomas",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=JCB653OD3",
            "why": "This is where psychology meets digital marketing directly. Every funnel, every landing page, every email sequence is an emotional journey. This course teaches you to architect those journeys intentionally — the same skill you need for your gamified marketing product.",
            "assignments": "Redesign one of your existing client funnels using emotional journey mapping. Before/after analysis with predicted conversion improvements.",
            "applications": "Create an 'Emotional Journey Blueprint' template for your consulting practice. Integrate emotional state detection into your AI marketing tools.",
            "linkedin": "\"Your funnel isn't broken. Your customer's emotional journey is. Here's how I redesigned a client's landing page using behavioral science — and increased conversions 3x.\"",
            "leadership": "You understand the human layer that most AI marketers completely ignore. AI can optimize, but only a leader who understands emotions can architect the right experience to optimize."
        },
        {
            "title": "Recognizing Predictably Irrational Decision-Making",
            "program": "Psychology in Business Ethics",
            "instructor": "Bradley Wendel",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LAW533OD1",
            "why": "Ethics is your differentiation. In an AI marketing world where everyone is optimizing for clicks, you'll be the leader who optimizes for sustainable engagement. Understanding irrational behavior through an ethical lens makes your productivity advice trustworthy.",
            "assignments": "Write a case study on an AI marketing practice that exploits irrational behavior vs. one that helps users overcome it. Present both sides.",
            "applications": "Build ethical guardrails into your gamified product. Create a 'Responsible Persuasion' framework that becomes part of your brand.",
            "linkedin": "\"There's a fine line between helping people be more productive and manipulating them. Here's the ethical framework I use — from Cornell's psychology + law program.\"",
            "leadership": "Ethical authority is the highest form of thought leadership. When AI marketing scandals inevitably hit the news, you'll be the voice people turn to."
        },
    ],
    "phase2": [
        {
            "title": "Assess the Cultural Challenges Around AI Adoption",
            "program": "Shaping Internal AI Policies",
            "instructor": "Frank Pasquale",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LAW625OD2",
            "why": "90% of AI adoption failures are cultural, not technical. You're building AI marketing tools — if your clients can't adopt them, it doesn't matter how good the tech is. This course teaches you to diagnose and solve the human side of AI transformation.",
            "assignments": "Conduct an AI readiness assessment for one organization. Map their cultural barriers on a 2x2 matrix of resistance vs. capability.",
            "applications": "Create an 'AI Adoption Readiness Score' tool that you offer as a free assessment on LinkedIn. It generates leads and positions you as the expert.",
            "linkedin": "\"I've seen $500K AI projects fail in 6 months. The problem was never the technology. Here are the 4 cultural signals that predict AI adoption failure — from Cornell's AI policy program.\"",
            "leadership": "You become the bridge between technical AI capability and organizational reality. That's exactly the role a CTO/productivity leader needs to fill."
        },
        {
            "title": "Increase Business Adaptability Using AI",
            "program": "Using Generative AI to Transform Business Processes",
            "instructor": "Karan Girotra",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=CTECH473OD4",
            "why": "This is the practical application course — how to actually redesign business processes with generative AI. Your gamified marketing platform is fundamentally about process transformation. This gives you the frameworks to design it right.",
            "assignments": "Map 3 business processes in marketing (content creation, lead scoring, campaign optimization) and redesign each with AI integration. Estimate time savings.",
            "applications": "Build the process redesign directly into your product roadmap. Each workflow in your gamified system should reflect these transformation patterns.",
            "linkedin": "\"I just redesigned my content creation workflow using principles from Cornell's Generative AI program. What used to take 4 hours now takes 25 minutes. Here's the exact process.\"",
            "leadership": "You won't just talk about AI productivity — you'll have Cornell-backed frameworks for implementing it. That's the difference between a thought leader and a real leader."
        },
        {
            "title": "Consider What It Means to Be a 'Change Agent'",
            "program": "Leading Organizational Change",
            "instructor": "Samuel Bacharach",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LSM591OD1",
            "why": "If you want people to change how they work (productivity), you need to understand change itself. Samuel Bacharach is one of the leading organizational change scholars — his frameworks are battle-tested in real organizations.",
            "assignments": "Write your 'Change Agent Manifesto' — your personal philosophy on driving productivity change. Test it with 3 people and iterate.",
            "applications": "Embed change management principles into your onboarding flows. When users adopt your gamified product, they're going through organizational change — design for it.",
            "linkedin": "\"Being the 'productivity guy' isn't about tools. It's about being a change agent. Here's what Cornell's organizational change program taught me about why most productivity advice fails.\"",
            "leadership": "Change agents are leaders by definition. This course gives you the identity framework and the credibility to claim that role."
        },
        {
            "title": "Develop Your Agenda for Change",
            "program": "Leading Organizational Change",
            "instructor": "Samuel Bacharach",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LSM591OD2",
            "why": "Following the change agent course, this gets tactical. HOW do you actually drive change? What's the playbook? This gives you a repeatable framework you can teach others — which is exactly what your LinkedIn content needs.",
            "assignments": "Create a 90-day change agenda for implementing AI-driven productivity in a mid-size company. Include stakeholder mapping, quick wins, and resistance management.",
            "applications": "Template this into a consulting deliverable. Offer '90-Day AI Productivity Transformation' as a service.",
            "linkedin": "\"Forget new year's resolutions. Here's what a real 'agenda for change' looks like — the framework Cornell teaches for organizational transformation. I adapted it for personal productivity.\"",
            "leadership": "You'll have a structured methodology, not just opinions. Leaders who can say 'here's the playbook' command instant credibility."
        },
        {
            "title": "Propose Organizational Strategies to Address AI-Related Uncertainty",
            "program": "Building Organizational Resilience for AI",
            "instructor": "Frank Pasquale",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LAW626OD3",
            "why": "AI uncertainty is THE conversation right now. Everyone is anxious about AI replacing jobs, changing workflows, creating risks. This course equips you to be the calm, strategic voice in the room — which is exactly the productivity leader brand you want.",
            "assignments": "Write a 'State of AI Uncertainty' report for your industry. Include strategic recommendations. Share it as a LinkedIn document.",
            "applications": "Build uncertainty management features into your product. Help teams track and manage AI-related risks alongside their marketing actions.",
            "linkedin": "\"Everyone's afraid AI will take their job. Here's what Cornell's AI resilience program says you should actually be worried about — and the 3 strategies that work.\"",
            "leadership": "In times of uncertainty, people follow the person who has a framework for navigating it. That's you."
        },
    ],
    "phase3": [
        {
            "title": "Enact Your Leadership Strategy",
            "program": "Becoming a Strategic Leader",
            "instructor": "Kate Walsh",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LSM598OD3",
            "why": "This is where you go from 'productivity advisor' to 'strategic leader.' The course forces you to articulate and execute your own leadership strategy — not just advise others. Kate Walsh's framework connects personal strategy to organizational impact.",
            "assignments": "Write your personal leadership strategy document. Define your 3-year vision for the AI productivity space, your unique positioning, and your execution plan.",
            "applications": "Use this as the foundation for your LinkedIn bio, your consulting pitch deck, and your product's mission statement. Everything should align.",
            "linkedin": "\"I spent a week building my leadership strategy with Cornell's methodology. The biggest insight? Strategy isn't a plan — it's a set of choices about what NOT to do. Here's what I'm saying no to.\"",
            "leadership": "A leader without a strategy is just a busy person. This course ensures your productivity brand is strategically positioned, not just active."
        },
        {
            "title": "Optimize Follow-through",
            "program": "Leading with Credibility",
            "instructor": "Tony Simons",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LSM586OD2",
            "why": "The productivity guy MUST be the follow-through guy. Credibility comes from doing what you say you'll do. Tony Simons literally wrote the book on behavioral integrity — this is the science of walking your talk.",
            "assignments": "Audit your own follow-through rate for one month. Track every commitment you make and whether you delivered. Calculate your 'Integrity Score.'",
            "applications": "Build a follow-through tracking feature into your gamified product. Make accountability visible and rewarding.",
            "linkedin": "\"I tracked every commitment I made for 30 days. My follow-through rate was 67%. Here's how I used Cornell's credibility research to get it to 94% — and why it changed everything.\"",
            "leadership": "This is the most powerful leadership lesson: credibility is measurable, and the gap between words and actions is the #1 predictor of team productivity."
        },
        {
            "title": "Examine the Interconnectedness of Culture and Productivity",
            "program": "Culture and Productivity",
            "instructor": "Donna Haeger",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LSM722OD1",
            "why": "This is literally your thesis course. Culture determines productivity more than any tool, process, or AI system. Donna Haeger's research connects organizational culture to measurable productivity outcomes — the exact evidence base your brand needs.",
            "assignments": "Develop a 'Culture-Productivity Index' — a scoring model that predicts team output based on cultural factors. Test it with 2-3 real teams.",
            "applications": "This becomes a signature consulting offering. The 'Culture-Productivity Index' is your Intellectual Property — something you can trademark and scale.",
            "linkedin": "\"Productivity tools are a $100B industry. But Cornell research shows culture explains 4x more variance in output than tools. Here's the framework I use to diagnose culture-productivity fit.\"",
            "leadership": "You'll own the narrative that most productivity advice ignores the biggest lever. That's a contrarian, defensible position for thought leadership."
        },
        {
            "title": "Build Capacity and Learning Systems",
            "program": "Designing Organizations for Systems Thinking",
            "instructor": "Laura Cabrera, Derek Cabrera",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=CIPA525OD2",
            "why": "Systems thinking is how you scale productivity beyond individual tips. Your gamified mind-map product IS a system. The Cabreras' DSRP framework (Distinctions, Systems, Relationships, Perspectives) maps directly to how knowledge graphs work — which is what you've already built.",
            "assignments": "Model your AI marketing product as a system using DSRP. Identify the feedback loops, the bottlenecks, and the leverage points.",
            "applications": "Use systems thinking to design the node-relationship structure of your 3D mind-map. Each action in the game should create ripple effects through the system — that's engagement through systems design.",
            "linkedin": "\"I used Cornell's systems thinking framework to redesign my marketing workflow. The result: 60% fewer tasks, 2x the output. Here's how thinking in systems beats thinking in to-do lists.\"",
            "leadership": "Systems thinkers are rare. Most people optimize locally; you'll optimize globally. That's what makes a CTO, not just a manager."
        },
        {
            "title": "Analyze an Organization in Terms of a Transformation Process",
            "program": "Fundamentals of Organizational Design",
            "instructor": "M. Diane Burton, Pedro Perez",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=ILR551OD2",
            "why": "If you're advising organizations on AI adoption and productivity, you need to understand organizational design as a discipline. This course from ILR (Industrial & Labor Relations) gives you the structural lens — how orgs transform, not just how individuals change.",
            "assignments": "Take a company you admire and reverse-engineer its transformation journey. Identify the design choices that enabled (or blocked) their productivity.",
            "applications": "Create organizational transformation templates for your consulting practice. Map these to your product's enterprise features.",
            "linkedin": "\"Netflix, Spotify, and Tesla all redesigned their organizations for speed. Cornell's ILR school teaches the framework they (probably) used. Here's the 4-step transformation process.\"",
            "leadership": "Organizational design is executive-level work. This positions you for C-suite conversations, not just team-lead productivity tips."
        },
    ],
    "phase4": [
        {
            "title": "A Tour of the Digital Marketing Landscape",
            "program": "Understanding the Digital Marketing Landscape and the Customer Funnel",
            "instructor": "Clarence Lee",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LSM515OD1",
            "why": "Before you revolutionize marketing with AI, understand the full landscape. This gives you the map of all the channels, tools, and funnels that your gamified product will need to connect to. You can't gamify what you don't fully understand.",
            "assignments": "Map your own digital marketing funnel end-to-end. Identify every touchpoint, conversion rate, and drop-off. This becomes your product's first use case.",
            "applications": "Use this map as the foundation for your gamified product's workflow templates. Each node in your 3D mind-map represents a funnel stage.",
            "linkedin": "\"I mapped my entire marketing funnel using Cornell's framework. The biggest surprise? 70% of my 'marketing effort' was focused on 10% of the customer journey. Here's how I rebalanced.\"",
            "leadership": "Full-funnel thinking is what separates marketing leaders from marketing managers. You'll see the whole picture."
        },
        {
            "title": "Develop a Brand-Generated Social Content Strategy",
            "program": "Creating Effective Content Marketing",
            "instructor": "Stephanie Cartin, Rob Kwortnik",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=SHA743OD2",
            "why": "This is directly applicable to your LinkedIn strategy. Every Cornell course you take becomes content. This course teaches you to systematize content creation — which is exactly the productivity angle you want.",
            "assignments": "Create a 90-day content calendar based on your learning pathway. Each course = 3-5 LinkedIn posts. Map them to content pillars.",
            "applications": "Build a content engine that auto-suggests LinkedIn posts based on your course completions. Integrate this into your product.",
            "linkedin": "\"Cornell taught me content strategy. So I turned their course into a content strategy for LinkedIn. Meta? Yes. Effective? Here are the numbers after 30 days.\"",
            "leadership": "Content-led leadership is the modern version of thought leadership. You're not just consuming knowledge — you're distributing it."
        },
        {
            "title": "Draft a Brand Narrative Script",
            "program": "Principles of Digital Storytelling",
            "instructor": "Christopher Byrne",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=CALS211OD2",
            "why": "Your 'productivity guy' brand needs a narrative, not just tips. This course teaches the structure of compelling brand stories — the hero's journey, the tension, the transformation. Your story: 'I was drowning in tools and tasks until I discovered systems thinking and behavioral science.'",
            "assignments": "Write your brand narrative script. 3 versions: 30-second elevator pitch, 2-minute LinkedIn About, 10-minute keynote opening.",
            "applications": "Use narrative frameworks in your product's onboarding experience. Every user should feel like they're starting a journey, not just signing up for a tool.",
            "linkedin": "\"Every productivity guru tells you what to do. Almost none tell you a story that makes you WANT to do it. Here's the storytelling framework from Cornell's digital storytelling program that changes everything.\"",
            "leadership": "Leaders who tell stories move people. Leaders who share spreadsheets manage people. Choose."
        },
        {
            "title": "Examine Economic and Behavioral Pricing",
            "program": "Applied Marketing Strategy and Decision-Making Tools",
            "instructor": "Doug Stayman",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LSM522OD4",
            "why": "You're building a product. You need to price it. This course combines economics and behavioral science for pricing — perfectly aligned with your Phase 1 foundation. Price your consulting, your product, and your courses using science, not guesswork.",
            "assignments": "Design 3 pricing tiers for your gamified marketing product. Use behavioral pricing principles (anchoring, decoy effect, bundling) to optimize conversions.",
            "applications": "Build pricing psychology into your clients' offerings. This becomes a high-value consulting skill.",
            "linkedin": "\"I used Cornell's behavioral pricing research to reprice a client's service. Same offering. 40% higher revenue. Here's the psychology behind the three changes we made.\"",
            "leadership": "Leaders who understand pricing understand value creation. This is a business-critical skill that most marketers lack."
        },
        {
            "title": "Marketing KPIs and Other Analytics",
            "program": "Marketing",
            "instructor": "Andrea Ippolito",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=JCB505OD5",
            "why": "You can't improve what you can't measure. This course gives you the measurement framework for everything — your LinkedIn content performance, your product metrics, your client results. The productivity leader needs to be data-literate.",
            "assignments": "Build a personal marketing KPI dashboard. Track your LinkedIn engagement, website traffic, and pipeline metrics weekly.",
            "applications": "Integrate KPI tracking into your gamified product. Users should see their marketing metrics as game scores — with levels, achievements, and progress bars.",
            "linkedin": "\"I track 7 marketing KPIs weekly — here's my dashboard and what each number actually means for revenue. Cornell's marketing analytics framework simplified everything.\"",
            "leadership": "Data-driven leaders make better decisions. This closes the loop between action and impact."
        },
    ],
    "phase5": [
        {
            "title": "Assess Your Organization's Approach to Sustainability",
            "program": "Sustainable Business Foundations",
            "instructor": "Mark Milstein",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LSM711OD1",
            "why": "Sustainability is the unexpected differentiator in your brand. While every other productivity influencer talks about output, you'll talk about SUSTAINABLE output — for people, organizations, and the planet. Mark Milstein's work connects business strategy to sustainability in a way that resonates with executives.",
            "assignments": "Audit your own business practices for sustainability. Where are you creating waste — in time, energy, resources? Apply the same productivity lens to environmental impact.",
            "applications": "Add a 'sustainability score' to your gamified product. Teams don't just track productivity — they track whether their productivity is sustainable long-term.",
            "linkedin": "\"Hustle culture is the opposite of productivity. Here's what Cornell's sustainability program taught me about why burnout is the world's most expensive inefficiency.\"",
            "leadership": "Leaders who connect productivity to sustainability attract the next generation of talent and clients. This is future-proof positioning."
        },
        {
            "title": "Identify Relevant Sustainability Issues",
            "program": "Analyzing Sustainability in Organizations",
            "instructor": "Glen Dowell",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LSM712OD1",
            "why": "This gives you the analytical framework to identify WHICH sustainability issues matter for which organizations. Not every company needs to worry about carbon — but every company has sustainability blindspots that affect productivity.",
            "assignments": "Map the sustainability issues relevant to 3 different industries. Identify the intersection between sustainability risk and productivity impact.",
            "applications": "Build industry-specific sustainability assessments into your consulting practice.",
            "linkedin": "\"Most companies focus on the wrong sustainability issues. Cornell taught me a materiality framework that identifies the 20% of issues that drive 80% of impact.\"",
            "leadership": "Industry-specific expertise is more valuable than generic advice. This course gives you the tool to specialize."
        },
        {
            "title": "Incorporate Climate Change Language Into Your Organization",
            "program": "Introduction to Climate Change Science",
            "instructor": "Michael Hoffmann, Danielle Eiseman",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=CALS101OD3",
            "why": "Communication is everything. If you want to lead conversations about sustainable productivity, you need to speak the language of climate science accurately. This ensures you don't get dismissed as 'greenwashing' — you'll have the scientific credibility.",
            "assignments": "Rewrite one of your existing blog posts or LinkedIn posts to incorporate climate language authentically. Before/after comparison.",
            "applications": "Create content templates that naturally weave sustainability messaging into productivity content.",
            "linkedin": "\"I used to think sustainability and productivity were different conversations. Cornell's climate science program showed me they're the same conversation — just at different timescales.\"",
            "leadership": "Leaders who can bridge business and science languages are rare and incredibly valuable."
        },
        {
            "title": "Identify and Categorize Sustainability Risks",
            "program": "Corporate Sustainability Risk Management",
            "instructor": "John Tobin",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=CIPA562OD1",
            "why": "Risk management is an executive-level skill. This course teaches you to categorize and prioritize sustainability risks — which maps directly to productivity risk management. Every productivity blocker is a risk that needs to be categorized and addressed.",
            "assignments": "Create a 'Productivity Risk Register' for your own business. Categorize risks by likelihood and impact. Map mitigation strategies.",
            "applications": "Build risk assessment into your product's planning features. Teams should see productivity risks before they become crises.",
            "linkedin": "\"The best productivity system isn't a to-do list. It's a risk register. Here's how I adapted Cornell's corporate risk management framework for daily execution.\"",
            "leadership": "Risk-aware leaders prevent problems. That's higher-leverage than solving problems after they occur."
        },
    ],
    "phase6": [
        {
            "title": "Use Google Trends to Do Portfolio and Competitor Analysis",
            "program": "Behavioral Science for Innovation",
            "instructor": "Manoj Thomas",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=JCB654OD2",
            "why": "Data science starts with knowing where to find signal in noise. Google Trends is an underused superpower for market intelligence. This course connects Manoj Thomas's behavioral science expertise to practical data analysis — perfect bridge to AI marketing.",
            "assignments": "Analyze your niche (AI productivity) using Google Trends. Identify seasonal patterns, rising subtopics, and competitor content gaps. Use findings to plan your next month of LinkedIn content.",
            "applications": "Integrate trend analysis into your gamified product's recommendation engine. Suggest marketing actions based on trending topics.",
            "linkedin": "\"I used Google Trends + behavioral science to find 5 untapped content topics in my niche. One post went viral 3 days later. Here's the exact method from Cornell's innovation program.\"",
            "leadership": "Leaders who spot trends early move first. This is the analytical skill that feeds your content machine."
        },
        {
            "title": "Present a Path Forward",
            "program": "Product Analytics and Iteration",
            "instructor": "Keith Cowing",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=CTECH105OD3",
            "why": "You're building a product. This course teaches you to use analytics to iterate — essential for your gamified mind-map. Keith Cowing's product management expertise helps you make data-driven decisions about what to build next.",
            "assignments": "Define the core metrics for your gamified product. What does success look like? Build an analytics spec before you build the product.",
            "applications": "Create a product analytics dashboard. Use it to prioritize features based on user behavior data.",
            "linkedin": "\"Most products fail because founders build what they think users want. Cornell's product analytics course taught me to build what data says users NEED. Here's my framework.\"",
            "leadership": "Product leaders who are analytics-literate build better products. Period."
        },
        {
            "title": "Communicate About Data Effectively",
            "program": "Communicating Quantitative Data",
            "instructor": "Craig R. Snow",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=LSM717OD1",
            "why": "All the data science in the world is useless if you can't communicate it. This is the skill that makes your LinkedIn posts about productivity data actually engaging. Craig Snow's communication expertise ensures your data storytelling hits.",
            "assignments": "Take one of your data analyses and present it in 3 formats: a LinkedIn carousel, a one-page executive summary, and a verbal 2-minute pitch.",
            "applications": "Design your gamified product's reporting features to follow data communication best practices. Users should understand their metrics at a glance.",
            "linkedin": "\"I showed the same data to 3 groups in 3 different ways. One format got blank stares. One got nods. One got investment offers. Here's what Cornell taught me about data communication.\"",
            "leadership": "Leaders who communicate data clearly get buy-in. Leaders who dump spreadsheets get ignored."
        },
        {
            "title": "Hold Bots Accountable",
            "program": "Accountability in the Fourth Industrial Revolution",
            "instructor": "Robert Bloomfield",
            "url": "https://ondemand.ecornell.com/viewLessonPage.do?lessonCode=JCB686OD2",
            "why": "You're building AI marketing tools. Who's accountable when the AI makes a mistake? This course from Robert Bloomfield addresses the most important question in AI — accountability. It's essential for building trust in your product and your brand.",
            "assignments": "Write an 'AI Accountability Framework' for your gamified product. Define who's responsible when the AI recommends a bad action.",
            "applications": "Build accountability features into your product. Every AI suggestion should show reasoning and allow human override. This becomes a selling point.",
            "linkedin": "\"Your AI marketing tool just sent the wrong message to 10,000 people. Whose fault is it? Cornell's accountability research has a framework for this — and every AI company needs it.\"",
            "leadership": "The leader who addresses AI accountability head-on wins trust. Everyone else is avoiding the hardest question."
        },
    ],
}


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch
    )
    story = []

    # === COVER PAGE ===
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("eCornell Learning Pathway", title_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="60%", thickness=2, color=CORNELL_RED, spaceAfter=12))
    story.append(Paragraph("Personalized for Nandesh Goudar", subtitle_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "The AI Productivity Leader:<br/>Psychology, Marketing, Sustainability &amp; Gamification",
        ParagraphStyle('BigSub', parent=subtitle_style, fontSize=16, leading=22, textColor=CORNELL_RED)
    ))
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph(
        '"Productivity isn\'t about doing more things.<br/>It\'s about doing the right things, sustainably,<br/>with systems that scale."',
        quote_style
    ))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        "Prepared by the Office of the Dean<br/>eCornell Personalized Learning<br/>April 2026",
        ParagraphStyle('Footer', parent=small_style, alignment=TA_CENTER, fontSize=10, leading=14)
    ))
    story.append(PageBreak())

    # === WELCOME LETTER ===
    story.append(Paragraph("Welcome to Your Learning Journey", heading1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=CORNELL_RED, spaceAfter=16))
    story.append(Paragraph("Dear Nandesh,", body_bold))
    story.append(Paragraph(
        "Welcome to your personalized eCornell learning pathway. This isn't a generic curriculum — it's been architected specifically around your unique vision: becoming the industry leader at the intersection of AI, productivity, behavioral science, and sustainable marketing.",
        body_style
    ))
    story.append(Paragraph(
        "Your vision is ambitious and interconnected. You want to understand human psychology to improve productivity. You want to apply behavioral science to AI marketing. You want to build a gamified 3D mind-map that turns marketing actions into a game. And you want to do all of this while caring for the planet. Most people see these as separate tracks. We see them as one coherent strategy.",
        body_style
    ))
    story.append(Paragraph(
        "This pathway contains <b>29 courses</b> across <b>6 strategic phases</b>, carefully sequenced so each phase builds on the previous one. By the end, you won't just have certificates — you'll have a fully formed intellectual framework, a library of LinkedIn content, a consulting methodology, and the product design foundations for your gamified marketing platform.",
        body_style
    ))
    story.append(Paragraph(
        "Each course in this pathway includes detailed guidance on assignments, real-world applications, LinkedIn content opportunities, and how it develops your leadership. Treat this as your operating manual for the next 6 months.",
        body_style
    ))
    story.append(Paragraph(
        "The future belongs to leaders who can connect disciplines that others see as separate. You're already doing that. Let's make it systematic.",
        body_style
    ))
    story.append(Spacer(1, 16))
    story.append(Paragraph("Warm regards,<br/><b>The Office of Personalized Learning</b><br/>eCornell", body_style))
    story.append(PageBreak())

    # === EXECUTIVE SUMMARY ===
    story.append(Paragraph("Executive Summary", heading1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=CORNELL_RED, spaceAfter=16))

    summary_data = [
        ["Metric", "Value"],
        ["Total Courses", "29"],
        ["Learning Phases", "6"],
        ["Estimated Duration", "6 months"],
        ["LinkedIn Content Pieces", "90+ (3-5 per course)"],
        ["Programs Covered", "25"],
        ["Instructors", "20+"],
        ["Core Competencies", "Psychology, AI, Leadership,\nMarketing, Sustainability, Data Science"],
    ]
    summary_table = Table(summary_data, colWidths=[2.5*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), CORNELL_RED),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # Timeline
    story.append(Paragraph("Recommended Timeline", heading2_style))
    timeline_data = [
        ["Month", "Phase", "Focus"],
        ["1-2", "Phase 1: Psychology + Behavioral Science", "Build the intellectual foundation"],
        ["2-3", "Phase 2: AI + Change Management", "Understand AI adoption deeply"],
        ["3-4", "Phase 3: Strategic Leadership + Productivity", "Position as a strategic leader"],
        ["4-5", "Phase 4: Marketing + Content Strategy", "Turn learning into LinkedIn content"],
        ["5", "Phase 5: Environmental Sciences + Sustainability", "Add the differentiator"],
        ["5-6", "Phase 6: Data Science for AI Marketing", "Technical credibility for your product"],
    ]
    tl_table = Table(timeline_data, colWidths=[0.6*inch, 2.8*inch, 3.1*inch])
    tl_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tl_table)
    story.append(PageBreak())

    # === PHASE DETAILS ===
    phases = [
        ("Phase 1: Psychology + Behavioral Science", "The Intellectual Foundation", "phase1",
         "Everything you build — your brand, your product, your content — rests on understanding how humans think, decide, and act. This phase gives you the scientific foundation that makes every subsequent course more powerful. When you talk about productivity on LinkedIn, you won't be sharing tips — you'll be sharing science."),
        ("Phase 2: AI Adoption + Change Management", "The Transformation Engine", "phase2",
         "AI is the tool. Change management is the skill. This phase teaches you how organizations actually adopt new technology, what blocks them, and how to lead them through uncertainty. As someone building AI marketing tools, this is your competitive moat — you understand not just what AI can do, but how to make organizations actually use it."),
        ("Phase 3: Strategic Leadership + Productivity", "The Personal Brand Core", "phase3",
         "This is where you become 'the productivity guy.' Not with tips and hacks, but with strategic frameworks backed by Cornell research on leadership, credibility, culture, and systems thinking. This phase builds the executive-level credibility that separates you from every other productivity influencer on LinkedIn."),
        ("Phase 4: Marketing + Content Strategy", "The Content Machine", "phase4",
         "Every course you've taken becomes content. This phase teaches you how to systematize content creation, build a brand narrative, understand digital funnels, price your offerings, and measure results. Your Cornell journey itself becomes your most powerful marketing asset."),
        ("Phase 5: Environmental Sciences + Sustainability", "The Unexpected Differentiator", "phase5",
         "While every productivity influencer talks about output, you'll talk about SUSTAINABLE output — for people, organizations, and the planet. This unexpected positioning makes you memorable, attracts values-aligned clients, and connects productivity to the biggest challenge of our time. This is the phase that makes people say, 'I've never thought of it that way.'"),
        ("Phase 6: Data Science for AI Marketing", "The Technical Credibility", "phase6",
         "You're building a gamified AI marketing product. This phase gives you the analytical and data communication skills to make data-driven decisions, iterate based on evidence, and communicate insights compellingly. It also addresses AI accountability — the ethical foundation your product needs."),
    ]

    for phase_title, phase_subtitle, phase_key, phase_intro in phases:
        story.append(Paragraph(phase_title, heading1_style))
        story.append(Paragraph(phase_subtitle, ParagraphStyle('PhaseSubtitle', parent=subtitle_style, alignment=TA_LEFT, fontSize=12, textColor=ACCENT_ORANGE)))
        story.append(HRFlowable(width="100%", thickness=1, color=CORNELL_RED, spaceAfter=12))
        story.append(Paragraph(phase_intro, body_style))
        story.append(Spacer(1, 8))

        for idx, course in enumerate(COURSES[phase_key], 1):
            # Course header
            story.append(Paragraph(f"Course {idx}: {course['title']}", heading2_style))

            # Meta info table
            meta_data = [
                ["Program", course['program']],
                ["Instructor", course['instructor']],
                ["Course Link", course['url']],
            ]
            meta_table = Table(meta_data, colWidths=[1.2*inch, 5.3*inch])
            meta_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (0, -1), MEDIUM_GRAY),
                ('TEXTCOLOR', (1, 2), (1, 2), ACCENT_BLUE),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 8))

            # Why this course
            story.append(Paragraph("Why This Course Matters", heading3_style))
            story.append(Paragraph(course['why'], body_style))

            # Assignments
            story.append(Paragraph("Suggested Assignments", heading3_style))
            story.append(Paragraph(course['assignments'], body_style))

            # Applications
            story.append(Paragraph("Real-World Applications", heading3_style))
            story.append(Paragraph(course['applications'], body_style))

            # LinkedIn
            story.append(Paragraph("LinkedIn Content Idea", heading3_style))
            story.append(Paragraph(course['linkedin'], linkedin_style))

            # Leadership
            story.append(Paragraph("How This Develops Your Leadership", heading3_style))
            story.append(Paragraph(course['leadership'], body_style))

            story.append(Spacer(1, 12))
            if idx < len(COURSES[phase_key]):
                story.append(HRFlowable(width="40%", thickness=0.5, color=colors.lightgrey, spaceAfter=8))

        story.append(PageBreak())

    # === CONTENT STRATEGY ===
    story.append(Paragraph("Your LinkedIn Content Strategy", heading1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=CORNELL_RED, spaceAfter=16))
    story.append(Paragraph(
        "Every course in this pathway is designed to produce LinkedIn content. Here's how to systematize it:",
        body_style
    ))

    story.append(Paragraph("Content Formula: 1 Course = 5 Posts", heading2_style))
    content_types = [
        ["Post Type", "Format", "Example Hook"],
        ["The Insight", "Text post (< 300 words)", "\"Cornell just taught me something about [topic]\nthat changes how I think about productivity...\""],
        ["The Framework", "Carousel (8-10 slides)", "\"The [X] Framework: How Cornell research\nexplains why your team isn't productive\""],
        ["The Story", "Long-form (600+ words)", "\"I failed at [X] for 3 years. Then I learned\n[concept] from Cornell's [program]. Here's what changed.\""],
        ["The Hot Take", "Short text + poll", "\"Unpopular opinion from Cornell research:\n[contrarian claim]. Agree or disagree?\""],
        ["The How-To", "Document/PDF carousel", "\"Step-by-step: How I applied [concept]\nto get [specific result]. (Free template in comments)\""],
    ]
    ct_table = Table(content_types, colWidths=[1.2*inch, 1.5*inch, 3.8*inch])
    ct_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(ct_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Content Pillars", heading2_style))
    pillars = [
        "1. <b>Productivity Science</b> — Behavioral science meets execution. Posts about cognitive biases, decision fatigue, follow-through, culture.",
        "2. <b>AI Transformation</b> — Practical AI adoption stories. What works, what fails, and why culture matters more than technology.",
        "3. <b>Sustainable Performance</b> — The intersection of productivity and sustainability. Anti-hustle culture. Long-term thinking.",
        "4. <b>Learning in Public</b> — Share your Cornell journey in real-time. Lessons learned, frameworks discovered, mistakes made.",
        "5. <b>Product Building</b> — Behind-the-scenes of building your gamified marketing product. Technical decisions, design choices, user feedback.",
    ]
    for p in pillars:
        story.append(Paragraph(p, body_style))

    story.append(PageBreak())

    # === GAMIFIED PRODUCT VISION ===
    story.append(Paragraph("The Gamified Marketing Mind-Map", heading1_style))
    story.append(Paragraph("How Your Cornell Learning Feeds Your Product", ParagraphStyle('PhaseSubtitle', parent=subtitle_style, alignment=TA_LEFT, fontSize=12, textColor=ACCENT_ORANGE)))
    story.append(HRFlowable(width="100%", thickness=1, color=CORNELL_RED, spaceAfter=16))
    story.append(Paragraph(
        "Your vision for a 3D rendering mind-map that gamifies marketing actions draws from multiple disciplines in this pathway. Here's how each phase feeds into the product:",
        body_style
    ))

    product_map = [
        ["Phase", "Product Contribution"],
        ["Phase 1: Behavioral Science", "Reward loop design, nudge architecture,\nfriction reduction in user workflows"],
        ["Phase 2: Change Management", "User onboarding as organizational change,\nadoption mechanics, resistance handling"],
        ["Phase 3: Systems Thinking", "Node-relationship architecture, feedback loops,\nripple effects between marketing actions"],
        ["Phase 4: Content Strategy", "Template library, content suggestion engine,\nperformance scoring system"],
        ["Phase 5: Sustainability", "Sustainability scoring, burnout prevention\nmetrics, long-term health tracking"],
        ["Phase 6: Data Science", "Analytics engine, trend detection,\nAI recommendation accountability"],
    ]
    pm_table = Table(product_map, colWidths=[2.2*inch, 4.3*inch])
    pm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(pm_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph(
        '"The best productivity tool isn\'t a tool at all.<br/>It\'s a game that makes doing the right thing feel inevitable."',
        quote_style
    ))

    story.append(PageBreak())

    # === CLOSING ===
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("Your Next Steps", heading1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=CORNELL_RED, spaceAfter=16))

    steps = [
        "<b>Week 1:</b> Start Phase 1, Course 1 — Explore the Psychology of Daily Decision Making. Block 2 hours on your calendar.",
        "<b>Week 1:</b> Write your first 'Learning in Public' LinkedIn post: announce your Cornell journey and what you're building toward.",
        "<b>Every course completion:</b> Write 3-5 LinkedIn posts using the content formula above. Publish on a Mon-Wed-Fri schedule.",
        "<b>Monthly:</b> Review your pathway progress. Adjust the timeline if needed. The sequence matters more than the speed.",
        "<b>Month 3 checkpoint:</b> You should have completed Phases 1-2 and published 30+ LinkedIn posts. Assess engagement and refine your content pillars.",
        "<b>Month 6:</b> All phases complete. Begin building the gamified product with your full intellectual framework in place.",
    ]
    for s in steps:
        story.append(Paragraph(f"  {s}", body_style))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "This pathway was generated by your personal AI learning advisor,<br/>"
        "powered by eCornell GraphRAG — a semantic knowledge graph of 2,176 courses,<br/>"
        "682 programs, and 226 instructors, embedded with text-embedding-3-large<br/>"
        "and stored in Supabase pgvector for intelligent retrieval.",
        ParagraphStyle('Footer2', parent=small_style, alignment=TA_CENTER, fontSize=8)
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>cornell.learnleadai.com</b>",
        ParagraphStyle('Footer3', parent=small_style, alignment=TA_CENTER, fontSize=10, textColor=CORNELL_RED)
    ))

    doc.build(story)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
