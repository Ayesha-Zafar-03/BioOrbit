import streamlit as st
import pandas as pd
import requests
import hashlib
import json
import os
import time

from utils.ai_summarizer import summarize_text

ADS_API_KEY = st.secrets.get("NASA_ADS_API_KEY", "")

st.set_page_config(
    page_title="BioOrbit — NASA Space Biology Explorer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

CACHE_FILE = "summary_cache.json"

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cached_summaries = json.load(f)
else:
    cached_summaries = {}

if "summaries" not in st.session_state:
    st.session_state.summaries = cached_summaries
if "total_searches" not in st.session_state:
    st.session_state.total_searches = 0
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "page" not in st.session_state:
    st.session_state.page = 1
if "active_nav" not in st.session_state:
    st.session_state.active_nav = "Dashboard"

# ─────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .stApp {
        background: #f0f2f8;
        color: #1a1a2e;
    }

    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { display: none; }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background: #0f1629;
        padding: 1.2rem 0.8rem;
    }
    [data-testid="stSidebar"] * { color: #c7c9d3 !important; }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 0.2rem 0.4rem 1.2rem;
        border-bottom: 1px solid #1c2440;
        margin-bottom: 1rem;
    }
    .sidebar-brand .logo-icon {
        width: 36px; height: 36px;
        background: linear-gradient(135deg, #6366f1, #818cf8);
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.2rem; color: white;
    }
    .sidebar-brand .brand-text h2 {
        font-size: 1.1rem; font-weight: 700; color: #f1f5f9;
        margin: 0; letter-spacing: -0.3px;
    }
    .sidebar-brand .brand-text p {
        font-size: 0.68rem; color: #6b7280;
        margin: 0; line-height: 1.3;
    }

    .nav-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        border-radius: 10px;
        margin-bottom: 4px;
        cursor: pointer;
        font-size: 0.88rem;
        font-weight: 500;
        color: #94a3b8;
        transition: all 0.2s;
        text-decoration: none;
    }
    .nav-item:hover { background: #1a2340; color: #e2e8f0; }
    .nav-item.active {
        background: linear-gradient(135deg, #4f46e5, #6366f1);
        color: #ffffff;
        box-shadow: 0 4px 12px rgba(79,70,229,0.3);
    }
    .nav-item .nav-icon { font-size: 1rem; width: 20px; text-align: center; }

    .sidebar-footer {
        position: absolute;
        bottom: 1.5rem;
        left: 0.8rem; right: 0.8rem;
        border-top: 1px solid #1c2440;
        padding-top: 1rem;
    }
    .sidebar-footer img { height: 40px; margin-bottom: 8px; }
    .sidebar-footer p {
        font-size: 0.72rem; color: #6b7280;
        margin: 2px 0; line-height: 1.4;
    }
    .sidebar-footer .tagline {
        font-size: 0.7rem;
        color: #4b5563;
        font-style: italic;
        margin-top: 6px;
    }

    /* ── WELCOME SECTION ── */
    .welcome-section {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .welcome-section::before {
        content: '';
        position: absolute;
        top: -50%; right: -10%;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(99,102,241,0.15), transparent 70%);
        pointer-events: none;
    }
    .welcome-section h1 {
        font-size: 2rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0 0 0.3rem;
    }
    .welcome-section h1 .accent { color: #818cf8; }
    .welcome-section .desc {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
        max-width: 520px;
    }

    .search-row {
        display: flex;
        gap: 0;
        max-width: 600px;
    }
    .search-row .stTextInput { flex: 1; }
    .search-row .stTextInput > div > div > input {
        background: #ffffff;
        border: 2px solid #e2e8f0;
        border-right: none;
        border-radius: 10px 0 0 10px;
        padding: 12px 16px;
        color: #1a1a2e;
        font-size: 14px;
    }
    .search-row .stTextInput > div > div > input:focus {
        border-color: #6366f1;
    }
    .search-btn {
        background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
        color: white !important;
        border: none !important;
        border-radius: 0 10px 10px 0 !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        height: 100% !important;
        white-space: nowrap !important;
    }
    .search-btn:hover {
        background: linear-gradient(135deg, #6366f1, #818cf8) !important;
        box-shadow: 0 4px 12px rgba(99,102,241,0.3) !important;
    }

    .popular-label {
        font-size: 0.78rem;
        color: #6b7280;
        margin-top: 0.8rem;
    }
    .popular-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 0.4rem; }
    .chip {
        display: inline-block;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        color: #cbd5e1;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }
    .chip:hover { background: rgba(99,102,241,0.2); border-color: #6366f1; color: #e2e8f0; }

    /* ── STAT CARDS (hero right) ── */
    .hero-stats {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .hero-stat-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 14px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-stat-card .icon-circle {
        width: 38px; height: 38px;
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem;
        flex-shrink: 0;
    }
    .hero-stat-card .icon-circle.blue { background: #3b82f620; color: #60a5fa; }
    .hero-stat-card .icon-circle.green { background: #10b98120; color: #34d399; }
    .hero-stat-card .icon-circle.purple { background: #8b5cf620; color: #a78bfa; }
    .hero-stat-card .stat-text .val {
        font-size: 1.1rem; font-weight: 700; color: #f1f5f9;
    }
    .hero-stat-card .stat-text .lbl {
        font-size: 0.72rem; color: #6b7280;
    }

    /* ── FEATURE CARDS ── */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .feature-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1.4rem;
        transition: all 0.2s;
    }
    .feature-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
        transform: translateY(-2px);
    }
    .feature-card .num-icon {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 0.8rem;
    }
    .feature-card .num {
        width: 32px; height: 32px;
        background: #eef2ff;
        color: #4f46e5;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem; font-weight: 700;
    }
    .feature-card .fi {
        font-size: 1.2rem;
        color: #6366f1;
    }
    .feature-card h3 {
        font-size: 1rem;
        font-weight: 700;
        color: #111827;
        margin: 0 0 0.4rem;
    }
    .feature-card p {
        font-size: 0.82rem;
        color: #6b7280;
        line-height: 1.55;
        margin: 0;
    }

    /* ── PAPER CARDS ── */
    .papers-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .papers-header h2 {
        font-size: 1.2rem;
        font-weight: 700;
        color: #111827;
        margin: 0;
    }
    .papers-header .showing {
        font-size: 0.82rem;
        color: #6b7280;
    }
    .papers-header .showing b { color: #4f46e5; }

    .paper-item {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.7rem;
        transition: all 0.2s;
    }
    .paper-item:hover {
        border-color: #c7d2fe;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }
    .paper-item-top {
        display: flex;
        align-items: flex-start;
        gap: 14px;
    }
    .paper-doc-icon {
        width: 36px; height: 36px;
        background: #eef2ff;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem; color: #6366f1;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .paper-content { flex: 1; }
    .paper-content h4 {
        font-size: 0.95rem;
        font-weight: 600;
        color: #111827;
        margin: 0 0 0.3rem;
        line-height: 1.4;
    }
    .paper-content .meta {
        font-size: 0.8rem;
        color: #6b7280;
        margin-bottom: 0.5rem;
    }
    .paper-tags { display: flex; gap: 6px; flex-wrap: wrap; }
    .paper-tag {
        background: #f0f4ff;
        color: #4f46e5;
        padding: 3px 10px;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 500;
    }
    .paper-actions {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 8px;
    }
    .nasa-link {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        color: #4f46e5;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 500;
        text-decoration: none;
        transition: all 0.2s;
        white-space: nowrap;
    }
    .nasa-link:hover { background: #eef2ff; border-color: #c7d2fe; }
    .expand-btn {
        background: none; border: none;
        color: #94a3b8; font-size: 1.2rem;
        cursor: pointer; padding: 4px;
        transition: color 0.2s;
    }
    .expand-btn:hover { color: #4f46e5; }

    /* ── QUICK STATS ── */
    .quick-stats {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1.3rem;
    }
    .quick-stats h3 {
        font-size: 1rem;
        font-weight: 700;
        color: #111827;
        margin: 0 0 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .stat-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #f3f4f6;
    }
    .stat-row:last-child { border-bottom: none; }
    .stat-row .left {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.85rem;
        color: #6b7280;
    }
    .stat-row .left .s-icon {
        width: 32px; height: 32px;
        background: #f3f4f6;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem;
    }
    .stat-row .right {
        font-size: 0.95rem;
        font-weight: 700;
        color: #111827;
    }

    /* ── ABOUT PAGE ── */
    .about-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .about-card h3 {
        font-size: 1.05rem;
        font-weight: 700;
        color: #111827;
        margin: 0 0 0.5rem;
    }
    .about-card p {
        color: #6b7280;
        font-size: 0.88rem;
        line-height: 1.6;
        margin: 0;
    }
    .tech-pill {
        display: inline-block;
        background: #eef2ff;
        color: #4f46e5;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 500;
        margin: 3px;
    }

    /* ── SUMMARY ── */
    .summary-block {
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-left: 3px solid #6366f1;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-top: 0.6rem;
        font-size: 0.88rem;
        line-height: 1.7;
        color: #374151;
    }
    .summary-block .sum-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: #6366f1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.4rem;
    }

    /* ── MISC ── */
    .stTabs [data-baseweb="tab-list"] { gap: 0; }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        color: #94a3b8;
        font-weight: 500;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        color: #4f46e5 !important;
        border-bottom: 2px solid #4f46e5 !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #4f46e5, #6366f1);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
        font-size: 13px;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #6366f1, #818cf8);
        box-shadow: 0 4px 12px rgba(99,102,241,0.25);
    }

    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        color: #111827 !important;
    }

    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #f0f2f8; }
    ::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }

    .stAlert > div { border-radius: 8px; }
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
        "fl": "title,abstract,author,year,doi,keyword",
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
        keywords = d.get("keyword", [])[:3]
        if not keywords:
            keywords = d.get("category", [])[:3]
        rows_data.append({
            "title": d.get("title", [""])[0],
            "abstract": d.get("abstract", ""),
            "year": d.get("year", ""),
            "authors": ", ".join(d.get("author", [])[:3]),
            "keywords": keywords,
            "link": f"https://ui.adsabs.harvard.edu/abs/{d.get('doi',[None])[0]}" if d.get("doi") else ""
        })
    return pd.DataFrame(rows_data), total, ""

# ─────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="logo-icon">🔬</div>
        <div class="brand-text">
            <h2>BioOrbit</h2>
            <p>NASA Space Biology<br>Research Explorer</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("🏠", "Dashboard"),
        ("🔍", "Search"),
        ("📑", "Saved Summaries"),
        ("ℹ️", "About"),
    ]
    for icon, label in nav_items:
        active = "active" if st.session_state.active_nav == label else ""
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.active_nav = label
            st.rerun()

    st.markdown("""
    <div class="sidebar-footer">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/2449px-NASA_logo.svg.png" alt="NASA" />
        <p><strong style="color:#e2e8f0;">Powered by NASA ADS<br>+ HuggingFace</strong></p>
        <p class="tagline">Making space biology<br>research accessible<br>and actionable through AI.</p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# NAV: DASHBOARD
# ─────────────────────────────────────────────────
if st.session_state.active_nav == "Dashboard":
    if not ADS_API_KEY:
        st.error("NASA ADS API key missing. Add `NASA_ADS_API_KEY` to Streamlit Secrets.")
        st.stop()

    total_cached = len(st.session_state.summaries)

    st.markdown(f"""
    <div class="welcome-section">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div style="flex:1;">
                <h1>Welcome to <span class="accent">BioOrbit</span></h1>
                <p class="desc">Search, explore, and understand NASA-funded research on how spaceflight affects living organisms.</p>
                <div class="popular-label">Popular searches:</div>
                <div class="popular-chips">
                    <span class="chip" onclick="window.location.reload()">microgravity</span>
                    <span class="chip">radiation biology</span>
                    <span class="chip">space plants</span>
                    <span class="chip">human health</span>
                    <span class="chip">astrobiology</span>
                </div>
            </div>
            <div class="hero-stats">
                <div class="hero-stat-card">
                    <div class="icon-circle blue">📄</div>
                    <div class="stat-text">
                        <div class="val">15M+</div>
                        <div class="lbl">Papers in NASA ADS</div>
                    </div>
                </div>
                <div class="hero-stat-card">
                    <div class="icon-circle green">⚡</div>
                    <div class="stat-text">
                        <div class="val">Real-time</div>
                        <div class="lbl">NASA ADS API</div>
                    </div>
                </div>
                <div class="hero-stat-card">
                    <div class="icon-circle purple">🤖</div>
                    <div class="stat-text">
                        <div class="val">AI Summaries</div>
                        <div class="lbl">Powered by HuggingFace (BART-large-CNN)</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="features-grid">
        <div class="feature-card">
            <div class="num-icon">
                <div class="num">1</div>
                <div class="fi">🔍</div>
            </div>
            <h3>Search</h3>
            <p>Type a topic and we query NASA's Astrophysics Data System (ADS) API, which indexes 15M+ peer-reviewed papers.</p>
        </div>
        <div class="feature-card">
            <div class="num-icon">
                <div class="num">2</div>
                <div class="fi">📋</div>
            </div>
            <h3>Explore</h3>
            <p>View paper titles, authors, year, and direct links to the full record on NASA ADS. Expand abstracts inline.</p>
        </div>
        <div class="feature-card">
            <div class="num-icon">
                <div class="num">3</div>
                <div class="fi">✨</div>
            </div>
            <h3>Summarize</h3>
            <p>Click "Generate AI Summary" and we use HuggingFace's BART-large-CNN model to create a concise 4-bullet summary.</p>
        </div>
        <div class="feature-card">
            <div class="num-icon">
                <div class="num">4</div>
                <div class="fi">⚡</div>
            </div>
            <h3>Cache</h3>
            <p>Summaries are saved locally so they load instantly on repeat views.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="papers-header">
        <h2>Recent Research Results</h2>
        <span class="showing">Showing <b>{st.session_state.get('last_total', 0)}</b> results for "<b>{st.session_state.get('last_query', '—')}</b>"</span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("last_results") is not None and len(st.session_state.last_results) > 0:
        df = st.session_state.last_results
        for i, row in df.iterrows():
            article_id = hashlib.md5(row.title.encode()).hexdigest()
            tags_html = "".join([f'<span class="paper-tag">{k}</span>' for k in row.get("keywords", []) if k])
            link_html = f'<a class="nasa-link" target="_blank" href="{row.link}">View on NASA ADS ↗</a>' if row.link else ""

            st.markdown(f"""
            <div class="paper-item">
                <div class="paper-item-top">
                    <div class="paper-doc-icon">📄</div>
                    <div class="paper-content">
                        <h4>{row.title}</h4>
                        <div class="meta">{row.authors} · {row.year}</div>
                        <div class="paper-tags">{tags_html}</div>
                    </div>
                    <div class="paper-actions">
                        {link_html}
                        <span class="expand-btn">⌄</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Read Abstract & Summarize"):
                st.write(row.abstract if row.abstract else "Abstract not available.")
                if st.button("✨ Generate AI Summary", key=f"ds_sum_{i}"):
                    if article_id not in st.session_state.summaries:
                        with st.spinner("Generating..."):
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
    else:
        st.info("Use the Search page to find papers, and results will appear here.")

# ─────────────────────────────────────────────────
# NAV: SEARCH
# ─────────────────────────────────────────────────
elif st.session_state.active_nav == "Search":
    if not ADS_API_KEY:
        st.error("NASA ADS API key missing. Add `NASA_ADS_API_KEY` to Streamlit Secrets.")
        st.stop()

    st.markdown("""
    <div style="margin-bottom:1.2rem;">
        <h2 style="font-size:1.3rem; font-weight:700; color:#111827; margin:0 0 0.2rem;">Search NASA Research</h2>
        <p style="font-size:0.85rem; color:#6b7280; margin:0;">Find papers on space biology, microgravity, radiation, and more.</p>
    </div>
    """, unsafe_allow_html=True)

    col_search, col_btn = st.columns([5, 1])
    with col_search:
        query = st.text_input("", placeholder="Try searching for a topic (e.g. microgravity, radiation biology, plant science...)", label_visibility="collapsed")
    with col_btn:
        st.write("")
        search_clicked = st.button("Search", use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        rows = st.selectbox("Results per page", [5, 10, 15, 20, 25, 30], index=1)
    with col2:
        page = st.number_input("Page", min_value=1, step=1, value=1)

    start = (page - 1) * rows

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

        st.session_state.last_query = query
        st.session_state.last_total = total
        st.session_state.last_results = df

        st.markdown(f"""
        <div class="papers-header">
            <h2>Research Results</h2>
            <span class="showing">Showing <b>{len(df)}</b> of <b>{total:,}</b> results for "<b>{query}</b>" · Page {page}/{total_pages}</span>
        </div>
        """, unsafe_allow_html=True)

        if len(df) == 0:
            st.info("No results found. Try different keywords.")
        else:
            for i, row in df.iterrows():
                article_id = hashlib.md5(row.title.encode()).hexdigest()
                tags_html = "".join([f'<span class="paper-tag">{k}</span>' for k in row.get("keywords", []) if k])
                link_html = f'<a class="nasa-link" target="_blank" href="{row.link}">View on NASA ADS ↗</a>' if row.link else ""

                st.markdown(f"""
                <div class="paper-item">
                    <div class="paper-item-top">
                        <div class="paper-doc-icon">📄</div>
                        <div class="paper-content">
                            <h4>{row.title}</h4>
                            <div class="meta">{row.authors} · {row.year}</div>
                            <div class="paper-tags">{tags_html}</div>
                        </div>
                        <div class="paper-actions">
                            {link_html}
                            <span class="expand-btn">⌄</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("Read Abstract & Summarize"):
                    st.write(row.abstract if row.abstract else "Abstract not available.")
                    if st.button("✨ Generate AI Summary", key=f"sr_sum_{i}"):
                        if article_id not in st.session_state.summaries:
                            with st.spinner("Generating..."):
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

            if total_pages > 1:
                st.write("")
                pg_cols = st.columns([1, 2, 1])
                with pg_cols[0]:
                    if page > 1:
                        if st.button("← Previous"):
                            st.session_state.page = page - 1
                            st.rerun()
                with pg_cols[2]:
                    if page < total_pages:
                        if st.button("Next →"):
                            st.session_state.page = page + 1
                            st.rerun()

# ─────────────────────────────────────────────────
# NAV: SAVED SUMMARIES
# ─────────────────────────────────────────────────
elif st.session_state.active_nav == "Saved Summaries":
    st.markdown("""
    <div style="margin-bottom:1.2rem;">
        <h2 style="font-size:1.3rem; font-weight:700; color:#111827; margin:0 0 0.2rem;">Saved Summaries</h2>
        <p style="font-size:0.85rem; color:#6b7280; margin:0;">Your cached AI-generated paper summaries.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.summaries:
        for aid, summary in st.session_state.summaries.items():
            st.markdown(f"""
            <div class="paper-item">
                <div class="paper-content">
                    <div class="meta" style="font-size:0.75rem; color:#94a3b8; margin-bottom:0.3rem;">ID: {aid[:12]}...</div>
                    <div class="summary-block" style="margin-top:0;">
                        <div class="sum-label">✦ Cached Summary</div>
                        {summary}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        if st.button("Clear All Summaries"):
            st.session_state.summaries = {}
            with open(CACHE_FILE, "w") as f:
                json.dump({}, f)
            st.rerun()
    else:
        st.info("No saved summaries yet. Search for papers and generate summaries to see them here.")

# ─────────────────────────────────────────────────
# NAV: ABOUT
# ─────────────────────────────────────────────────
elif st.session_state.active_nav == "About":
    st.markdown("""
    <div style="margin-bottom:1.2rem;">
        <h2 style="font-size:1.3rem; font-weight:700; color:#111827; margin:0 0 0.2rem;">About BioOrbit</h2>
        <p style="font-size:0.85rem; color:#6b7280; margin:0;">The story behind the project.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="about-card">
        <h3>What is BioOrbit?</h3>
        <p>BioOrbit is an AI-powered research explorer built for the <strong style="color:#4f46e5;">NASA Space Apps Challenge</strong>.
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
        📜 <a href="https://www.linkedin.com/in/ayesha-zafar03/details/certifications/1766219867831/single-media-viewer/?profileId=ACoAAEZ2YVsBLGhwcNHEkxQm5iYEemAyoYlrWoE" target="_blank" style="color:#4f46e5; text-decoration:none;">View Certificate on LinkedIn</a></p>
    </div>
    <div class="about-card">
        <h3>Credits</h3>
        <p>Created by <strong style="color:#111827;">Ayesha Zafar</strong> —
        <a href="https://github.com/Ayesha-Zafar-03" target="_blank" style="color:#4f46e5; text-decoration:none;">GitHub</a> ·
        <a href="https://www.linkedin.com/in/ayesha-zafar03/" target="_blank" style="color:#4f46e5; text-decoration:none;">LinkedIn</a></p>
    </div>
    """, unsafe_allow_html=True)
