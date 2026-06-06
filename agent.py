import anthropic
import requests
import json
import os
import random
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, MimeType, Content

# ── CONFIG ──────────────────────────────────────────────────────────────────
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")
TAVILY_KEY    = os.environ.get("TAVILY_KEY")
SENDGRID_KEY  = os.environ.get("SENDGRID_KEY")
TO_EMAIL      = "liamtp45@gmail.com"
FROM_EMAIL    = "liamtp45@gmail.com"

# ── TOPIC POOL ───────────────────────────────────────────────────────────────
# The agent picks one topic per run and rotates through them.
# Add, remove, or edit topics freely.
TOPICS = [
    # --- Technology & Emerging ---
    {"title": "The EV Industry",             "category": "Technology",  "prompt": "The electric vehicle industry: full economics, key players (Tesla, BYD, legacy OEMs), battery technology, supply chain, charging infrastructure, government policy, competitive dynamics, and where the industry is heading over the next decade."},
    {"title": "Drone & UAV Industry",        "category": "Technology",  "prompt": "The drone and UAV industry: commercial, military, and consumer segments, economics, key players (DJI, Joby, Zipline, Anduril), regulation, delivery drones, defence applications, and future trajectory."},
    {"title": "Commercial Space Industry",   "category": "Technology",  "prompt": "The commercial space industry: launch, satellites, space tourism, in-orbit services, key players (SpaceX, Blue Origin, Rocket Lab, Planet Labs), economics, government contracts, and the long-term vision for human spaceflight."},
    {"title": "Artificial Intelligence & LLMs", "category": "Technology", "prompt": "The AI and large language model industry: the full economics, key players (Anthropic, OpenAI, Google DeepMind, Meta AI), infrastructure requirements, GPU supply chain, business model wars, regulation, and where AI is heading in 3-5 years."},
    {"title": "Semiconductor & Chip Industry", "category": "Technology", "prompt": "The global semiconductor industry: chip design vs fabrication, key players (TSMC, NVIDIA, Intel, ASML, Samsung), the geopolitics of chips, AI chip demand, supply chain fragility, and what the next wave of computing looks like."},
    {"title": "Biohacking & Human Augmentation", "category": "Health",  "prompt": "The biohacking and human augmentation space: nootropics, continuous glucose monitoring, genetic testing, longevity science, implantables, key figures (Bryan Johnson, Peter Attia), the science behind what actually works, and the future of human performance optimisation."},
    {"title": "Biomedicine & Gene Therapy",  "category": "Health",      "prompt": "Biomedicine and gene therapy: CRISPR, mRNA technology (beyond COVID vaccines), cell therapy, personalised medicine, key companies (Moderna, BioNTech, Vertex, Beam Therapeutics), the economics of drug development, and the most promising areas of the next decade."},

    # --- Industries & Companies ---
    {"title": "Private Equity Industry",     "category": "Finance",     "prompt": "The private equity industry: how it works, economics (fees, carry, fund structure), major players (Blackstone, KKR, Apollo, Carlyle), deal types (LBO, growth equity, venture), the controversy, returns vs public markets, and where PE is heading."},
    {"title": "Family Office Industry",      "category": "Finance",     "prompt": "The family office industry: single vs multi-family offices, AUM, how they invest differently from institutions, the role they play in private markets, key hubs (Hong Kong, Singapore, Zurich), and what working at one actually looks like."},
    {"title": "Hedge Fund Industry",         "category": "Finance",     "prompt": "The hedge fund industry: strategies (long/short, macro, quant, activist), economics, major players (Bridgewater, Citadel, Two Sigma, Man Group), the fee debate, performance vs index funds, and the evolution of the industry."},
    {"title": "Berkshire Hathaway",          "category": "Company",     "prompt": "Berkshire Hathaway deep dive: the full history, Buffett and Munger's investment philosophy, the insurance float model, major holdings and subsidiaries, competitive advantages, how the business actually makes money, and what happens post-Buffett."},
    {"title": "SpaceX",                      "category": "Company",     "prompt": "SpaceX deep dive: full history from founding to today, the Falcon 9 reusability breakthrough, Starlink economics and growth, Starship ambitions, revenue streams, competitive moat, and Elon Musk's long-term vision for Mars."},
    {"title": "NVIDIA",                      "category": "Company",     "prompt": "NVIDIA deep dive: history from gaming GPUs to AI infrastructure, the CUDA ecosystem moat, H100/B200 economics, data centre revenue, competitive threats (AMD, Intel, custom silicon from Google/Amazon/Apple), and whether the valuation is justified."},
    {"title": "SoftBank & Vision Fund",      "category": "Company",     "prompt": "SoftBank and the Vision Fund: Masayoshi Son's vision, the investment thesis, the hits (Alibaba) and disasters (WeWork), how the Vision Fund model works, current portfolio, and what SoftBank's role in the global tech ecosystem looks like today."},
    {"title": "Hong Kong as a Financial Hub","category": "Finance",     "prompt": "Hong Kong as a global financial centre: history, role in China's capital markets, the impact of 2019-2020 protests and national security law, competition from Singapore, family office migration, IPO market, and the outlook for the next decade."},
    {"title": "Singapore Financial Ecosystem","category": "Finance",    "prompt": "Singapore as a financial and wealth hub: MAS regulation, family office growth, fintech ecosystem, tax structure, competition with Hong Kong, key players and institutions, and why so much global capital is flowing there."},
    {"title": "Luxury Goods Industry",       "category": "Industry",    "prompt": "The luxury goods industry: economics of luxury (pricing power, brand moat, exclusivity), LVMH, Kering, Richemont as conglomerates, the China luxury boom and slowdown, resale markets, and what makes a truly durable luxury brand."},
    {"title": "Aviation Industry",           "category": "Industry",    "prompt": "The commercial aviation industry: full economics (why airlines are historically terrible businesses), Boeing vs Airbus duopoly, MRO (maintenance, repair, overhaul), sustainable aviation fuels, the pilot shortage, and whether aviation can ever be truly sustainable."},
    {"title": "Padel Tennis Industry",       "category": "Industry",    "prompt": "The global padel tennis industry: origins, growth trajectory, economics of building and operating courts, major players (World Padel Tour, Premier Padel), sponsorship and media deals, UK market specifically, and the investment opportunity in padel venues."},

    # --- Health, Fitness & Food ---
    {"title": "Longevity Science",           "category": "Health",      "prompt": "The science of longevity: the hallmarks of ageing, the most evidence-backed interventions (exercise, sleep, nutrition, rapamycin, metformin, NAD+ precursors), key researchers (David Sinclair, Peter Attia, Aubrey de Grey), and what someone in their 20s should actually be doing today."},
    {"title": "Ultra Endurance Physiology",  "category": "Fitness",     "prompt": "The physiology of ultra endurance sport: how the body fuels itself beyond marathon distance, fat adaptation, VO2 max vs lactate threshold vs economy, training methodologies (80/20, polarised), nutrition strategies, altitude training, and the latest research on recovery."},
    {"title": "Nutrition Science",           "category": "Health",      "prompt": "The current state of nutrition science: what the evidence actually shows about protein, carbohydrates, fats, intermittent fasting, time-restricted eating, the gut microbiome, ultra-processed foods, and what an optimal diet looks like based on the strongest available evidence."},
    {"title": "Sleep Science",               "category": "Health",      "prompt": "The science of sleep: what happens during different sleep stages, the role of sleep in memory, performance, and longevity, the research on sleep deprivation, evidence-based interventions for better sleep, and what elite performers do differently."},
    {"title": "Strength Training Science",   "category": "Fitness",     "prompt": "The science of strength and hypertrophy: mechanisms of muscle growth, optimal training variables (volume, intensity, frequency), protein synthesis, the role of sleep and nutrition, evidence-based programmes, and the latest research on concurrent training with endurance sport."},
    {"title": "Psychedelics & Mental Health","category": "Health",      "prompt": "The psychedelics renaissance: psilocybin, MDMA, ketamine, and LSD in clinical research, the science of how they work, FDA approval status, key companies (MAPS, Compass Pathways, MindMed), therapeutic applications, and where the field is heading."},

    # --- Macro & Geopolitics ---
    {"title": "China's Economic Model",      "category": "Macro",       "prompt": "China's economic model: how it actually works, the role of state-owned enterprises, the property crisis, debt levels, demographics, the Belt and Road Initiative, decoupling from the West, and the outlook for China's economy over the next decade."},
    {"title": "The Future of Money",         "category": "Macro",       "prompt": "The future of money: central bank digital currencies (CBDCs), stablecoins, the role of crypto, de-dollarisation trends, the Bank for International Settlements, how payment systems are evolving, and what a post-dollar world might actually look like."},
    {"title": "Climate Tech & Green Energy", "category": "Technology",  "prompt": "The climate technology landscape: solar, wind, battery storage, green hydrogen, carbon capture, nuclear (including small modular reactors), the economics of each, key companies, government policy, and which technologies are actually going to move the needle."},
]

# ── WEB SEARCH ───────────────────────────────────────────────────────────────
def search_web(query: str, max_results: int = 8) -> list[dict]:
    """Search the web using Tavily and return results."""
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_KEY,
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,
            },
            timeout=30
        )
        data = resp.json()
        results = data.get("results", [])
        answer  = data.get("answer", "")
        return {"results": results, "answer": answer}
    except Exception as e:
        print(f"Search error: {e}")
        return {"results": [], "answer": ""}

def fetch_url(url: str) -> str:
    """Fetch the text content of a URL using Tavily extract."""
    try:
        resp = requests.post(
            "https://api.tavily.com/extract",
            json={"api_key": TAVILY_KEY, "urls": [url]},
            timeout=20
        )
        data = resp.json()
        results = data.get("results", [])
        if results:
            return results[0].get("raw_content", "")[:4000]
        return ""
    except Exception as e:
        return ""

# ── AGENT ─────────────────────────────────────────────────────────────────────
def run_research_agent(topic: dict) -> str:
    """
    Agentic research loop:
    1. Plan searches
    2. Execute searches iteratively
    3. Synthesise into full report
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    print(f"\n🔍 Researching: {topic['title']}")

    # Step 1: Generate targeted search queries
    print("  → Planning searches...")
    plan_response = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=800,
        system="You are a research planning assistant. Generate precise web search queries to thoroughly research a topic. Return ONLY a JSON array of 6-8 search query strings, nothing else.",
        messages=[{
            "role": "user",
            "content": f"Generate 6-8 targeted search queries to research this topic thoroughly:\n\n{topic['prompt']}\n\nFocus on: current data, key players, economics, recent developments, expert analysis. Return only a JSON array."
        }]
    )
    
    try:
        queries = json.loads(plan_response.content[0].text)
    except:
        # Fallback queries if parsing fails
        queries = [
            f"{topic['title']} industry overview 2024 2025",
            f"{topic['title']} key players market leaders",
            f"{topic['title']} economics business model revenue",
            f"{topic['title']} competitive landscape analysis",
            f"{topic['title']} latest developments news",
            f"{topic['title']} future outlook predictions",
        ]

    # Step 2: Execute searches and collect research material
    print(f"  → Running {len(queries)} searches...")
    all_research = []
    seen_urls = set()

    for i, query in enumerate(queries):
        print(f"     [{i+1}/{len(queries)}] {query[:60]}...")
        search_data = search_web(query)
        
        if search_data["answer"]:
            all_research.append(f"[Search Answer for '{query}']\n{search_data['answer']}\n")
        
        for result in search_data["results"][:4]:
            url   = result.get("url", "")
            title = result.get("title", "")
            content = result.get("content", "")
            
            if url not in seen_urls and content:
                seen_urls.add(url)
                all_research.append(
                    f"[Source: {title}]\n[URL: {url}]\n{content}\n"
                )

    research_text = "\n---\n".join(all_research)
    print(f"  → Collected {len(all_research)} sources")

    # Step 3: Write the full deep dive report
    print("  → Writing report...")
    today = datetime.now().strftime("%B %d, %Y")
    
    report_response = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=4000,
        system=f"""You are writing a deep dive research report for Liam, a 22-year-old aerospace engineering graduate from Newcastle, UK. He is ambitious, intellectually curious, and working toward a career in high finance in Hong Kong/Singapore before building a conglomerate. He runs ultra trails competitively and has wide-ranging interests in technology, business, health, and science.

Write in a style that is:
- Intellectually rigorous but readable — like a brilliant friend who happens to be an expert
- Direct and confident — no hedging unnecessarily  
- Rich with specific numbers, names, and examples
- Structured with clear headers
- Includes "so what" takeaways — why this matters, what Liam should know or do

Format the report in clean HTML for email. Use these HTML elements:
- <h1> for the main title
- <h2> for section headers
- <h3> for sub-sections
- <p> for paragraphs
- <ul><li> for bullet lists
- <strong> for key terms/numbers
- <blockquote> for standout insights
- A <div class="takeaway"> section at the end with key takeaways

Do NOT use markdown. Use only HTML tags. Today's date: {today}.""",
        messages=[{
            "role": "user",
            "content": f"""Write a full deep dive research report on: {topic['title']}

Research brief: {topic['prompt']}

Here is the research material gathered from the web:

{research_text[:12000]}

Write a comprehensive 5-10 page report covering all the key dimensions of this topic. Be thorough, specific, and genuinely insightful. Include real numbers, real company names, real people where possible."""
        }]
    )

    report_html = report_response.content[0].text
    print(f"  → Report written ({len(report_html)} chars)")
    return report_html

# ── EMAIL ─────────────────────────────────────────────────────────────────────
def send_report(topic: dict, report_html: str):
    """Send the research report via SendGrid."""
    today = datetime.now().strftime("%B %d, %Y")
    category_emoji = {
        "Technology": "⚡",
        "Finance":    "💰",
        "Company":    "🏢",
        "Industry":   "🏭",
        "Health":     "🧬",
        "Fitness":    "🏃",
        "Macro":      "🌍",
    }.get(topic["category"], "📊")

    subject = f"{category_emoji} Deep Dive: {topic['title']} — {today}"

    full_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; margin: 0; padding: 20px; color: #1a1a1a; }}
  .container {{ max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  .header {{ background: linear-gradient(135deg, #0a0a0f 0%, #1a1040 100%); padding: 32px 40px; }}
  .header-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(255,255,255,0.5); margin-bottom: 8px; }}
  .header h1 {{ color: #ffffff; font-size: 26px; font-weight: 700; margin: 0 0 8px; line-height: 1.3; }}
  .header-meta {{ font-size: 13px; color: rgba(255,255,255,0.5); }}
  .badge {{ display: inline-block; background: rgba(124,106,247,0.3); color: #a89df9; border: 1px solid rgba(124,106,247,0.4); padding: 3px 10px; border-radius: 99px; font-size: 11px; font-weight: 600; margin-right: 8px; }}
  .body {{ padding: 40px; }}
  .body h1 {{ font-size: 24px; font-weight: 700; color: #0a0a0f; margin: 32px 0 12px; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; }}
  .body h2 {{ font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 28px 0 10px; }}
  .body h3 {{ font-size: 16px; font-weight: 600; color: #2d2d4e; margin: 20px 0 8px; }}
  .body p {{ font-size: 15px; line-height: 1.75; color: #333; margin: 0 0 16px; }}
  .body ul {{ padding-left: 20px; margin: 0 0 16px; }}
  .body li {{ font-size: 15px; line-height: 1.7; color: #333; margin-bottom: 6px; }}
  .body strong {{ color: #0a0a0f; font-weight: 600; }}
  blockquote {{ border-left: 3px solid #7c6af7; margin: 24px 0; padding: 12px 20px; background: #f8f7ff; border-radius: 0 8px 8px 0; font-size: 15px; color: #2d2d4e; font-style: italic; }}
  .takeaway {{ background: linear-gradient(135deg, #f0eeff 0%, #e8f5e0 100%); border-radius: 10px; padding: 24px; margin: 32px 0 0; }}
  .takeaway h2 {{ color: #1a1a2e; margin-top: 0; font-size: 17px; }}
  .takeaway li {{ color: #2d2d4e; font-weight: 500; }}
  .footer {{ background: #f5f5f5; padding: 24px 40px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #e8e8e8; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-label">Research Intelligence</div>
    <h1>{topic['title']}</h1>
    <div class="header-meta">
      <span class="badge">{topic['category']}</span>
      {today} · Autonomous Deep Dive
    </div>
  </div>
  <div class="body">
    {report_html}
  </div>
  <div class="footer">
    Liam's Research Agent · Powered by Claude & Tavily · <a href="#" style="color:#7c6af7;">Manage topics</a>
  </div>
</div>
</body>
</html>"""

    try:
        sg = SendGridAPIClient(SENDGRID_KEY)
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAIL,
            subject=subject,
            html_content=full_html
        )
        response = sg.send(message)
        print(f"  → Email sent! Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"  → Email error: {e}")
        return False

# ── TOPIC ROTATION ────────────────────────────────────────────────────────────
def get_next_topic() -> dict:
    """
    Pick the next topic. Uses a rotation file to track which topics
    have been covered recently and avoid repeats.
    """
    rotation_file = "topic_rotation.json"
    
    try:
        with open(rotation_file, "r") as f:
            state = json.load(f)
    except:
        state = {"completed": [], "index": 0}

    completed = state.get("completed", [])
    remaining = [t for t in TOPICS if t["title"] not in completed]

    if not remaining:
        # Full cycle complete — reset and start again
        remaining = TOPICS
        completed = []
        print("  → Full topic cycle complete, restarting rotation")

    # Pick next topic
    topic = remaining[0]
    completed.append(topic["title"])

    # Save state
    with open(rotation_file, "w") as f:
        json.dump({"completed": completed, "index": len(completed)}, f, indent=2)

    return topic

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  LIAM'S RESEARCH AGENT")
    print(f"  {datetime.now().strftime('%A, %B %d %Y at %H:%M')}")
    print(f"{'='*60}")

    # Pick topic
    topic = get_next_topic()
    print(f"\n📚 Topic: {topic['title']} [{topic['category']}]")

    # Run research
    report_html = run_research_agent(topic)

    # Send email
    print(f"\n📧 Sending to {TO_EMAIL}...")
    success = send_report(topic, report_html)

    if success:
        print(f"\n✅ Done! Report on '{topic['title']}' sent successfully.")
    else:
        print(f"\n❌ Research complete but email failed.")

    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
