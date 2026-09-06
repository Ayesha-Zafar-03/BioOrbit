import streamlit as st
import pandas as pd
import requests
import hashlib
import json
import os

from utils.ai_summarizer import summarize_text

ADS_API_KEY = st.secrets.get("NASA_ADS_API_KEY", "")

st.set_page_config(
    page_title="BioOrbit",
    page_icon="🧬",
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

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .stApp {
        background: #0a0e17;
        color: #e0e0e0;
    }

    [data-testid="stHeader"] { background: transparent; }

    [data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #1a1f2e; }

    .stTextInput > div > div > input {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 12px 16px;
        color: #f9fafb;
        font-size: 15px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59,130,246,0.15);
    }

    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.2s;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37,99,235,0.3);
    }

    .hero-section {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
        position: relative;
    }
    .hero-section h1 {
        font-size: 2.8rem;
        font-weight: 700;
        color: #f9fafb;
        margin-bottom: 0.3rem;
        letter-spacing: -1px;
    }
    .hero-section .accent { color: #3b82f6; }
    .hero-section .tagline {
        color: #6b7280;
        font-size: 1.05rem;
        font-weight: 400;
        margin-top: 0.3rem;
    }

    .stat-bar {
        display: flex;
        justify-content: center;
        gap: 2.5rem;
        margin: 1.2rem 0 0.5rem;
        padding: 0.8rem 0;
    }
    .stat-item {
        text-align: center;
    }
    .stat-item .num {
        font-size: 1.3rem;
        font-weight: 700;
        color: #3b82f6;
    }
    .stat-item .label {
        font-size: 0.75rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 2px;
    }

    .search-container {
        max-width: 680px;
        margin: 0 auto 1.5rem;
    }

    .paper-card {
        background: #111827;
        border: 1px solid #1a1f2e;
        border-radius: 12px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 0.8rem;
        transition: border-color 0.2s;
    }
    .paper-card:hover { border-color: #2563eb44; }

    .paper-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #f9fafb;
        margin: 0 0 0.5rem;
        line-height: 1.4;
    }
    .paper-meta {
        font-size: 0.82rem;
        color: #6b7280;
        margin-bottom: 0.6rem;
    }
    .paper-meta span { margin-right: 1.2rem; }
    .paper-meta .year-badge {
        background: #1e293b;
        color: #94a3b8;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .view-link {
        display: inline-block;
        background: transparent;
        color: #3b82f6;
        border: 1px solid #2563eb44;
        padding: 5px 14px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.82rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    .view-link:hover {
        background: #2563eb22;
        border-color: #3b82f6;
    }

    .summary-block {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-left: 3px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-top: 0.8rem;
        font-size: 0.9rem;
        line-height: 1.65;
        color: #d1d5db;
    }
    .summary-block .sum-head {
        font-size: 0.78rem;
        font-weight: 600;
        color: #3b82f6;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }

    .results-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.6rem 0;
        margin-bottom: 1rem;
        border-bottom: 1px solid #1a1f2e;
    }
    .results-header .count {
        font-size: 0.9rem;
        color: #9ca3af;
    }
    .results-header .count b { color: #f9fafb; }

    .footer-bar {
        text-align: center;
        padding: 2rem 0 1rem;
        border-top: 1px solid #1a1f2e;
        margin-top: 2rem;
    }
    .footer-bar p {
        color: #4b5563;
        font-size: 0.8rem;
    }

    [data-testid="stSpinner"] { color: #3b82f6; }
    .stAlert > div { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

if not ADS_API_KEY:
    st.error("NASA ADS API key is missing. Add it to Streamlit Secrets as `NASA_ADS_API_KEY`.")
    st.stop()

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

st.markdown("""
<div class="hero-section">
    <h1>Bio<span class="accent">Orbit</span></h1>
    <p class="tagline">Search and explore NASA Space Biology research — powered by AI</p>
</div>
""", unsafe_allow_html=True)

col_l, col_search, col_r = st.columns([1, 3, 1])
with col_search:
    query = st.text_input("", placeholder="Search topics — microgravity, radiation, stem cells...", label_visibility="collapsed")

with col_l:
    rows = st.select_slider("", options=[5, 10, 15, 20, 25, 30], value=10, label_visibility="collapsed")
with col_r:
    page = st.number_input("", min_value=1, step=1, value=1, label_visibility="collapsed")

start = (page - 1) * rows

if query:
    with st.spinner("Searching NASA ADS..."):
        df, total, error = fetch_ads(query, rows, start)

    if error:
        st.error(f"Could not reach NASA ADS. {error}")
        st.stop()

    total_pages = max(1, -(-total // rows))

    st.markdown(f"""
    <div class="stat-bar">
        <div class="stat-item">
            <div class="num">{total:,}</div>
            <div class="label">Papers Found</div>
        </div>
        <div class="stat-item">
            <div class="num">{page}/{total_pages}</div>
            <div class="label">Page</div>
        </div>
        <div class="stat-item">
            <div class="num">{len(df)}</div>
            <div class="label">Showing</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if len(df) == 0:
        st.info("No results found. Try different keywords.")
    else:
        for i, row in df.iterrows():
            article_id = hashlib.md5(row.title.encode()).hexdigest()
            authors_display = row.authors if len(row.authors) < 60 else row.authors[:57] + "..."
            link_html = f"<a class='view-link' target='_blank' href='{row.link}'>View paper</a>" if row.link else ""

            st.markdown(f"""
            <div class="paper-card">
                <p class="paper-title">{row.title}</p>
                <div class="paper-meta">
                    <span>{authors_display}</span>
                    <span class="year-badge">{row.year}</span>
                </div>
                {link_html}
            </div>
            """, unsafe_allow_html=True)

            btn_label = "Generate summary"
            if st.button(btn_label, key=f"s{i}", help="Summarize this paper with AI"):
                if article_id not in st.session_state.summaries:
                    with st.spinner("Summarizing..."):
                        raw = summarize_text(row.abstract)
                        bullets = raw.split(". ")
                        bullets = [f"• {b.strip().rstrip('.')}" for b in bullets if b.strip()][:4]
                        st.session_state.summaries[article_id] = "<br>".join(bullets)
                        with open(CACHE_FILE, "w") as f:
                            json.dump(st.session_state.summaries, f)

                st.markdown(f"""
                <div class="summary-block">
                    <div class="sum-head">AI Summary</div>
                    {st.session_state.summaries[article_id]}
                </div>
                """, unsafe_allow_html=True)

            st.write("")

st.markdown("""
<div class="footer-bar">
    <p>BioOrbit &middot; NASA ADS + HuggingFace &middot; Ayesha Zafar</p>
</div>
""", unsafe_allow_html=True)
