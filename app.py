import streamlit as st
import pandas as pd
import requests
import hashlib
import json
import os

from utils.ai_summarizer import summarize_text

ADS_API_KEY = st.secrets.get("NASA_ADS_API_KEY", "")

st.set_page_config(
    page_title="BioOrbit — NASA Space Biology Explorer",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CACHE_FILE = "summary_cache.json"

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cached_summaries = json.load(f)
else:
    cached_summaries = {}

if "summaries" not in st.session_state:
    st.session_state.summaries = cached_summaries

if "search_history" not in st.session_state:
    st.session_state.search_history = []

if "total_searches" not in st.session_state:
    st.session_state.total_searches = 0

# ─────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .stApp {
        background: #030712;
        color: #e5e7eb;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { display: none; }
    [data-testid="stSidebarNav"] { display: none; }

    /* Starfield background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background:
            radial-gradient(1px 1px at 10% 20%, rgba(255,255,255,0.4), transparent),
            radial-gradient(1px 1px at 30% 60%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1.5px 1.5px at 50% 10%, rgba(255,255,255,0.5), transparent),
            radial-gradient(1px 1px at 70% 80%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1px 1px at 90% 40%, rgba(255,255,255,0.4), transparent),
            radial-gradient(1.5px 1.5px at 15% 85%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1px 1px at 45% 45%, rgba(255,255,255,0.2), transparent),
            radial-gradient(1px 1px at 80% 15%, rgba(255,255,255,0.35), transparent),
            radial-gradient(1px 1px at 25% 35%, rgba(255,255,255,0.25), transparent),
            radial-gradient(1.5px 1.5px at 60% 70%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1px 1px at 5% 50%, rgba(255,255,255,0.2), transparent),
            radial-gradient(1px 1px at 95% 90%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1px 1px at 40% 95%, rgba(255,255,255,0.15), transparent),
            radial-gradient(1.5px 1.5px at 75% 30%, rgba(255,255,255,0.25), transparent),
            radial-gradient(1px 1px at 55% 55%, rgba(255,255,255,0.2), transparent);
        z-index: -1;
        pointer-events: none;
    }

    /* Nebula glow */
    .stApp::after {
        content: '';
        position: fixed;
        top: -30%; left: -20%;
        width: 140%; height: 140%;
        background:
            radial-gradient(ellipse at 20% 50%, rgba(37,99,235,0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 20%, rgba(139,92,246,0.04) 0%, transparent 50%),
            radial-gradient(ellipse at 60% 80%, rgba(6,182,212,0.03) 0%, transparent 50%);
        z-index: -1;
        pointer-events: none;
        animation: drift 30s ease-in-out infinite alternate;
    }
    @keyframes drift {
        0% { transform: translate(0, 0) rotate(0deg); }
        100% { transform: translate(2%, -1%) rotate(1deg); }
    }

    /* Hero */
    .hero {
        text-align: center;
        padding: 1.8rem 1rem 0.8rem;
    }
    .hero-brand {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin-bottom: 0.4rem;
    }
    .hero-brand img { height: 52px; }
    .hero h1 {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3rem;
        font-weight: 800;
        color: #f9fafb;
        letter-spacing: -2px;
        margin: 0;
    }
    .hero h1 .or { color: #3b82f6; }
    .hero .sub {
        color: #6b7280;
        font-size: 1.05rem;
        font-weight: 400;
        margin-top: 0.2rem;
    }
    .hero .hackathon-badge {
        display: inline-block;
        margin-top: 0.8rem;
        padding: 5px 14px;
        border: 1px solid #f59e0b44;
        background: linear-gradient(135deg, #f59e0b11, #f59e0b08);
        border-radius: 20px;
        font-size: 0.78rem;
        color: #f59e0b;
        font-weight: 500;
        letter-spacing: 0.3px;
    }

    /* Metrics row */
    .metrics-row {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin: 1.2rem auto;
        max-width: 700px;
    }
    .metric-box {
        flex: 1;
        text-align: center;
        padding: 0.9rem 0.6rem;
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        min-width: 120px;
    }
    .metric-box .val {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #f9fafb;
    }
    .metric-box .lbl {
        font-size: 0.7rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 2px;
    }
    .metric-box .val.blue { color: #3b82f6; }
    .metric-box .val.purple { color: #a78bfa; }
    .metric-box .val.cyan { color: #06b6d4; }
    .metric-box .val.green { color: #34d399; }

    /* Trending chips */
    .trending-section { text-align: center; margin: 1.5rem 0 0.5rem; }
    .trending-label {
        font-size: 0.75rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.6rem;
    }

    /* Tabs override */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        color: #9ca3af;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: #1e3a5f !important;
        border-color: #3b82f6 !important;
        color: #f9fafb !important;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 14px 18px;
        color: #f9fafb;
        font-size: 15px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.12);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 22px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.25s;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(37,99,235,0.25);
    }

    /* Paper cards */
    .paper-card {
        background: linear-gradient(135deg, #0f172a, #111827);
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 0.8rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s;
    }
    .paper-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 3px; height: 100%;
        background: linear-gradient(180deg, #3b82f6, #8b5cf6);
        border-radius: 14px 0 0 14px;
    }
    .paper-card:hover {
        border-color: #3b82f633;
        transform: translateY(-1px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .paper-num {
        position: absolute;
        top: 1rem; right: 1.2rem;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #1f2937;
        line-height: 1;
    }
    .paper-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #f9fafb;
        margin: 0 0 0.5rem;
        line-height: 1.45;
        padding-right: 2.5rem;
    }
    .paper-meta {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        flex-wrap: wrap;
        font-size: 0.8rem;
        color: #6b7280;
        margin-bottom: 0.7rem;
    }
    .paper-meta .badge {
        background: #1e293b;
        color: #94a3b8;
        padding: 3px 10px;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 500;
    }
    .paper-meta .dot {
        width: 3px; height: 3px;
        background: #4b5563;
        border-radius: 50%;
        display: inline-block;
    }
    .view-link {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        color: #3b82f6;
        border: 1px solid #2563eb33;
        padding: 5px 14px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.8rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    .view-link:hover {
        background: #2563eb15;
        border-color: #3b82f6;
    }

    /* Summary */
    .summary-block {
        background: #0c1322;
        border: 1px solid #1e293b;
        border-left: 3px solid #3b82f6;
        border-radius: 10px;
        padding: 1rem 1.3rem;
        margin-top: 0.8rem;
        font-size: 0.88rem;
        line-height: 1.7;
        color: #d1d5db;
    }
    .summary-block .sum-label {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        color: #3b82f6;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-bottom: 0.5rem;
    }

    /* Results bar */
    .results-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.7rem 1rem;
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .results-bar .left { font-size: 0.85rem; color: #9ca3af; }
    .results-bar .left b { color: #f9fafb; }
    .results-bar .right { font-size: 0.78rem; color: #6b7280; }

    /* About page */
    .about-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .about-card h3 {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem;
        color: #f9fafb;
        margin: 0 0 0.6rem;
    }
    .about-card p {
        color: #9ca3af;
        font-size: 0.9rem;
        line-height: 1.6;
        margin: 0;
    }
    .tech-pill {
        display: inline-block;
        background: #1e293b;
        color: #94a3b8;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 500;
        margin: 3px;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2.5rem 0 1.5rem;
        margin-top: 2rem;
        border-top: 1px solid #111827;
    }
    .footer p {
        color: #374151;
        font-size: 0.78rem;
    }
    .footer a {
        color: #4b5563;
        text-decoration: none;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #030712; }
    ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 3px; }

    /* Spinner */
    [data-testid="stSpinner"] { color: #3b82f6; }
    .stAlert > div { border-radius: 8px; }
    .stExpander { background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# NASA ADS FETCH
# ─────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_ads(query, rows, start):
    url = "https://api.adsabs.harvard.edu/v1/search/query"
    headers = {"Authorization": f"Bearer {ADS_API_KEY}"}
    clean_query = ' '.join(query.split())
    query_str = f'title:"{clean_query}" OR abstract:"{clean_query}"'
    params = {
        "q": query_str,
        "fl": "title,abstract,author,year,doi",
        "rows": rows,
        "start": start
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
        r.raise_for_status()
    except requests.RequestException as e:
        return pd.DataFrame(), 0, str(e)
    data = r.json().get("response", {})
    total = data.get("numFound", 0)
    rows_data = []
    for d in data.get("docs", []):
        rows_data.append({
            "title": d.get("title", [""])[0],
            "abstract": d.get("abstract", ""),
            "year": d.get("year", ""),
            "authors": ", ".join(d.get("author", [])[:3]),
            "link": f"https://ui.adsabs.harvard.edu/abs/{d.get('doi',[None])[0]}" if d.get("doi") else ""
        })
    return pd.DataFrame(rows_data), total, ""

# ─────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-brand">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/2449px-NASA_logo.svg.png" alt="NASA" />
    </div>
    <h1>Bio<span class="or">Orbit</span></h1>
    <p class="sub">AI-Powered Explorer for NASA Space Biology Research</p>
    <div class="hackathon-badge">🏆 NASA Space Apps Challenge 2025 — Hackathon Project</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────────
total_cached = len(st.session_state.summaries)
total_searches = st.session_state.total_searches

st.markdown(f"""
<div class="metrics-row">
    <div class="metric-box">
        <div class="val blue">{total_searches}</div>
        <div class="lbl">Searches</div>
    </div>
    <div class="metric-box">
        <div class="val purple">{total_cached}</div>
        <div class="lbl">Summaries</div>
    </div>
    <div class="metric-box">
        <div class="val cyan">2</div>
        <div class="lbl">AI Models</div>
    </div>
    <div class="metric-box">
        <div class="val green">1</div>
        <div class="lbl">NASA API</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# TRENDING TOPICS
# ─────────────────────────────────────────────────
trending = [
    "Microgravity", "Radiation Biology", "Plant Growth in Space",
    "Stem Cells", "Bone Density Loss", "Mars Adaptation",
    "ISS Experiments", "Astromaterials", "Genomics in Space",
    "Tissue Engineering"
]

st.markdown('<div class="trending-section"><div class="trending-label">Quick Search</div></div>', unsafe_allow_html=True)
chip_cols = st.columns(10)
for idx, topic in enumerate(trending):
    with chip_cols[idx]:
        if st.button(topic, key=f"chip_{idx}", use_container_width=True):
            st.session_state["query_input"] = topic
            st.rerun()

# ─────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────
tab_search, tab_about, tab_how = st.tabs(["🔍 Search", "🧬 About", "⚙️ How it Works"])

# ─────────────────────────────────────────────────
# TAB: SEARCH
# ─────────────────────────────────────────────────
with tab_search:
    if not ADS_API_KEY:
        st.error("NASA ADS API key missing. Add `NASA_ADS_API_KEY` to Streamlit Secrets.")
        st.stop()

    col_search, col_btn = st.columns([5, 1])
    with col_search:
        search_val = st.text_input(
            "",
            value=st.session_state.get("query_input", ""),
            placeholder="Search — microgravity, radiation, stem cells, Mars...",
            label_visibility="collapsed",
            key="main_search"
        )
    with col_btn:
        st.write("")
        search_clicked = st.button("Search", use_container_width=True)

    col_rows, col_page = st.columns(2)
    with col_rows:
        rows = st.select_slider("Results per page", options=[5, 10, 15, 20, 25, 30], value=10)
    with col_page:
        page = st.number_input("Page", min_value=1, step=1, value=1)

    start = (page - 1) * rows
    query = search_val

    if query:
        st.session_state.total_searches += 1
        if query not in st.session_state.search_history:
            st.session_state.search_history.append(query)
            if len(st.session_state.search_history) > 20:
                st.session_state.search_history = st.session_state.search_history[-20:]

        with st.spinner("Searching NASA Astrophysics Data System..."):
            df, total, error = fetch_ads(query, rows, start)

        if error:
            st.error(f"Could not reach NASA ADS — {error}")
            st.stop()

        total_pages = max(1, -(-total // rows))

        st.markdown(f"""
        <div class="results-bar">
            <div class="left"><b>{total:,}</b> papers found for "<b>{query}</b>"</div>
            <div class="right">Page {page} of {total_pages} &middot; {len(df)} shown</div>
        </div>
        """, unsafe_allow_html=True)

        if len(df) == 0:
            st.info("No results. Try different keywords.")
        else:
            for i, row in df.iterrows():
                article_id = hashlib.md5(row.title.encode()).hexdigest()
                authors_short = row.authors if len(row.authors) < 55 else row.authors[:52] + "..."
                link_html = f"<a class='view-link' target='_blank' href='{row.link}'>↗ NASA ADS</a>" if row.link else ""

                abstract_preview = row.abstract[:200] + "..." if len(row.abstract) > 200 else row.abstract

                st.markdown(f"""
                <div class="paper-card">
                    <div class="paper-num">{i+1}</div>
                    <p class="paper-title">{row.title}</p>
                    <div class="paper-meta">
                        <span class="badge">{row.year}</span>
                        <span class="dot"></span>
                        <span>{authors_short}</span>
                    </div>
                    {link_html}
                </div>
                """, unsafe_allow_html=True)

                with st.expander("Read Abstract"):
                    st.write(row.abstract if row.abstract else "Abstract not available.")

                if st.button("✨ Generate AI Summary", key=f"sum_{i}", use_container_width=False):
                    if article_id not in st.session_state.summaries:
                        with st.spinner("Generating summary..."):
                            raw = summarize_text(row.abstract)
                            bullets = raw.split(". ")
                            bullets = [f"• {b.strip().rstrip('.')}" for b in bullets if b.strip()][:4]
                            st.session_state.summaries[article_id] = "<br>".join(bullets)
                            with open(CACHE_FILE, "w") as f:
                                json.dump(st.session_state.summaries, f)

                    st.markdown(f"""
                    <div class="summary-block">
                        <div class="sum-label">✦ AI-Generated Summary</div>
                        {st.session_state.summaries[article_id]}
                    </div>
                    """, unsafe_allow_html=True)

                st.write("")

            if total_pages > 1:
                st.write("")
                pg_cols = st.columns([1, 2, 1])
                with pg_cols[0]:
                    if page > 1:
                        if st.button("← Previous"):
                            st.session_state["page"] = page - 1
                            st.rerun()
                with pg_cols[2]:
                    if page < total_pages:
                        if st.button("Next →"):
                            st.session_state["page"] = page + 1
                            st.rerun()

# ─────────────────────────────────────────────────
# TAB: ABOUT
# ─────────────────────────────────────────────────
with tab_about:
    st.markdown("""
    <div class="about-card">
        <h3>What is BioOrbit?</h3>
        <p>BioOrbit is an AI-powered research explorer built for the <strong style="color:#f59e0b;">NASA Space Apps Challenge</strong>.
        It connects to NASA's Astrophysics Data System (ADS) to fetch real peer-reviewed papers on space biology,
        then uses HuggingFace's BART-large-CNN model to generate concise, human-readable summaries.
        The goal: make complex space biology research accessible to everyone — students, researchers, and curious minds.</p>
    </div>
    <div class="about-card">
        <h3>Why It Matters</h3>
        <p>NASA funds thousands of studies on how spaceflight affects living organisms — from plant growth on the ISS
        to radiation effects on human DNA. But these papers are buried behind academic jargon and paywalls.
        BioOrbit surfaces this research and distills it into actionable insights in seconds.</p>
    </div>
    <div class="about-card">
        <h3>Built With</h3>
        <p>
            <span class="tech-pill">Python</span>
            <span class="tech-pill">Streamlit</span>
            <span class="tech-pill">HuggingFace Transformers</span>
            <span class="tech-pill">NASA ADS API</span>
            <span class="tech-pill">BART-large-CNN</span>
            <span class="tech-pill">Pandas</span>
            <span class="tech-pill">JSON Caching</span>
            <span class="tech-pill">Custom CSS</span>
        </p>
    </div>
    <div class="about-card">
        <h3>Achievements</h3>
        <p>🏆 Recognized at the NASA Space Apps Challenge for innovative use of AI in space biology research.<br>
        📜 <a href="https://www.linkedin.com/in/ayesha-zafar03/details/certifications/1766219867831/single-media-viewer/?profileId=ACoAAEZ2YVsBLGhwcNHEkxQm5iYEemAyoYlrWoE" target="_blank" style="color:#3b82f6; text-decoration:none;">View Certificate on LinkedIn</a></p>
    </div>
    <div class="about-card">
        <h3>Credits</h3>
        <p>Created by <strong style="color:#f9fafb;">Ayesha Zafar</strong> —
        <a href="https://github.com/Ayesha-Zafar-03" target="_blank" style="color:#3b82f6; text-decoration:none;">GitHub</a> &middot;
        <a href="https://www.linkedin.com/in/ayesha-zafar03/" target="_blank" style="color:#3b82f6; text-decoration:none;">LinkedIn</a></p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# TAB: HOW IT WORKS
# ─────────────────────────────────────────────────
with tab_how:
    st.markdown("""
    <div class="about-card">
        <h3>1 — Search</h3>
        <p>Type a topic (e.g. "microgravity", "radiation biology") and BioOrbit queries NASA's ADS database,
        which indexes over 15 million astrophysics papers. Results are filtered to title and abstract matches.</p>
    </div>
    <div class="about-card">
        <h3>2 — Explore</h3>
        <p>Browse paper cards showing title, authors, year, and a direct link to the full record on NASA ADS.
        Expand any card to read the full abstract.</p>
    </div>
    <div class="about-card">
        <h3>3 — Summarize</h3>
        <p>Click "Generate AI Summary" on any paper. The abstract is sent to HuggingFace's BART-large-CNN model,
        which produces a 4-bullet-point summary. Summaries are cached locally so they load instantly on repeat views.</p>
    </div>
    <div class="about-card">
        <h3>Architecture</h3>
        <p>
            <span class="tech-pill">Frontend: Streamlit</span>
            <span class="tech-pill">Backend: Python</span>
            <span class="tech-pill">Data: NASA ADS REST API</span>
            <span class="tech-pill">AI: HuggingFace Inference API</span>
            <span class="tech-pill">Cache: JSON + st.cache</span>
            <span class="tech-pill">Deploy: Streamlit Cloud</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    <p>BioOrbit &middot; Built for NASA Space Apps Challenge &middot; Ayesha Zafar</p>
    <p style="margin-top:4px;">Powered by NASA ADS + HuggingFace 🤗</p>
</div>
""", unsafe_allow_html=True)
