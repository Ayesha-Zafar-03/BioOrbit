import streamlit as st
import pandas as pd
import requests
import hashlib
import json
import os
import base64
from pathlib import Path

from utils.ai_summarizer import summarize_text


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="BioOrbit — NASA Space Biology Explorer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

ADS_API_KEY = st.secrets.get("NASA_ADS_API_KEY", "")
CACHE_FILE = "summary_cache.json"
BASE_DIR = Path(__file__).resolve().parent
EARTH_IMAGE = BASE_DIR / "assets" / "eathbackgroug.jpg"
NASA_LOGO = BASE_DIR / "assets" / "logonasa.png"


# ============================================================
# HELPERS
# ============================================================

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


earth_b64 = image_to_base64(EARTH_IMAGE) if EARTH_IMAGE.exists() else ""
nasa_b64  = image_to_base64(NASA_LOGO)  if NASA_LOGO.exists()  else ""

# mime type for nasa logo
nasa_mime = "image/png"
earth_mime = "image/jpeg"


# ============================================================
# SESSION STATE
# ============================================================

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r") as f:
            cached_summaries = json.load(f)
    except Exception:
        cached_summaries = {}
else:
    cached_summaries = {}

defaults = {
    "summaries":       cached_summaries,
    "total_searches":  0,
    "search_history":  [],
    "active_nav":      "Dashboard",
    "last_results":    None,
    "last_query":      "",
    "last_total":      0,
    "search_query":    "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# CSS
# ============================================================

hero_bg = (
    f"url('data:{earth_mime};base64,{earth_b64}')"
    if earth_b64 else "none"
)

st.markdown(
    f"""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

*, *::before, *::after {{
    font-family: 'Inter', sans-serif;
    box-sizing: border-box;
}}

/* ── app background ── */
.stApp {{
    background: #f0f2f8 !important;
    color: #172554;
}}

/* hide streamlit chrome */
#MainMenu, footer, header {{visibility: hidden;}}
.stDeployButton {{display:none;}}
[data-testid="stToolbar"] {{display:none;}}

/* ── remove default padding ── */
.block-container {{
    padding-top: 0 !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 100% !important;
}}

/* ============================================================
   SIDEBAR
   ============================================================ */

[data-testid="stSidebar"] {{
    background: #060f23 !important;
    min-width: 260px !important;
    max-width: 260px !important;
}}

[data-testid="stSidebar"] > div:first-child {{
    padding: 0 !important;
}}

/* sidebar inner wrapper */
[data-testid="stSidebarContent"] {{
    padding: 22px 16px !important;
    display: flex;
    flex-direction: column;
    height: 100vh;
}}

/* ── brand ── */
.sb-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 22px;
    margin-bottom: 20px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}}

.sb-logo {{
    width: 46px;
    height: 46px;
    border: 2.5px solid #6d5ce8;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    flex-shrink: 0;
    color: #a78bfa;
    font-size: 19px;
}}

.sb-logo::after {{
    content: "";
    position: absolute;
    width: 62px;
    height: 20px;
    border: 2px solid #6d5ce8;
    border-radius: 50%;
    transform: rotate(-28deg);
    pointer-events: none;
}}

.sb-title {{
    color: #ffffff;
    font-size: 22px;
    font-weight: 800;
    line-height: 1;
}}

.sb-subtitle {{
    color: #8899b4;
    font-size: 11px;
    line-height: 1.4;
    margin-top: 4px;
}}

/* ── nav buttons ── */
[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    border: none !important;
    color: #94a3b8 !important;
    text-align: left !important;
    border-radius: 9px !important;
    padding: 11px 14px !important;
    margin-bottom: 3px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    width: 100% !important;
    transition: background 0.15s, color 0.15s;
}}

[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(99,102,241,0.15) !important;
    color: #ffffff !important;
}}

/* active nav item */
.nav-active [data-testid="stSidebar"] .stButton > button,
.nav-active .stButton > button {{
    background: linear-gradient(90deg, #4f46e5, #5b54e8) !important;
    color: #ffffff !important;
}}

/* ── bottom section ── */
.sb-bottom {{
    margin-top: auto;
    padding-top: 18px;
    border-top: 1px solid rgba(255,255,255,0.07);
}}

.sb-nasa-img {{
    width: 60px;
    height: auto;
    margin-bottom: 10px;
}}

.sb-powered {{
    font-size: 11px;
    color: #94a3b8;
    line-height: 1.5;
}}

.sb-tagline {{
    font-size: 10.5px;
    color: #506076;
    line-height: 1.55;
    margin-top: 10px;
}}

/* ============================================================
   HERO
   ============================================================ */

.hero-wrap {{
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 20px;
    position: relative;
    min-height: 300px;

    background:
        linear-gradient(
            90deg,
            rgba(4,11,28,0.97) 0%,
            rgba(4,11,28,0.90) 36%,
            rgba(4,11,28,0.35) 65%,
            transparent 100%
        ),
        {hero_bg};
    background-size: cover;
    background-position: center right;
}}

/* fallback gradient when no image */
.hero-wrap-nogfx {{
    background:
        radial-gradient(circle at 75% 50%, rgba(99,102,241,0.35), transparent 35%),
        linear-gradient(120deg, #060f23 0%, #0c1c3d 55%, #101b44 100%);
}}

.hero-inner {{
    display: flex;
    align-items: flex-start;
    gap: 24px;
    padding: 36px 36px 30px;
    position: relative;
    z-index: 2;
}}

.hero-left {{
    flex: 1;
    min-width: 0;
}}

.hero-title {{
    color: #ffffff;
    font-size: 38px;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -1px;
    margin: 0 0 10px;
}}

.hero-title span {{
    color: #8b7cf6;
}}

.hero-desc {{
    color: #c4cfe3;
    font-size: 14.5px;
    line-height: 1.65;
    max-width: 520px;
    margin-bottom: 22px;
}}

/* search bar */
.hero-search-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    max-width: 680px;
    background: rgba(255,255,255,0.97);
    border-radius: 10px;
    padding: 6px 6px 6px 14px;
    margin-bottom: 16px;
}}

.hero-search-icon {{
    color: #94a3b8;
    font-size: 15px;
}}

.hero-search-input {{
    flex: 1;
    border: none;
    outline: none;
    background: transparent;
    font-size: 13.5px;
    color: #172554;
}}

.hero-search-btn {{
    background: linear-gradient(135deg, #5046d9, #7c6ff0);
    color: white;
    border: none;
    border-radius: 7px;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    white-space: nowrap;
}}

/* chips */
.popular-row {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 7px;
}}

.popular-label {{
    color: #8899b4;
    font-size: 12px;
    white-space: nowrap;
}}

.chip {{
    display: inline-block;
    padding: 5px 13px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.2);
    background: rgba(255,255,255,0.07);
    color: #c4cfe3;
    font-size: 11.5px;
    cursor: default;
}}

/* ── hero stat panel ── */
.stat-panel {{
    background: rgba(4,13,35,0.82);
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: 13px;
    padding: 6px 16px;
    min-width: 215px;
    flex-shrink: 0;
}}

.stat-row {{
    display: flex;
    align-items: center;
    gap: 13px;
    padding: 13px 0;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}}

.stat-row:last-child {{
    border-bottom: none;
}}

.stat-icon-box {{
    width: 38px;
    height: 38px;
    border-radius: 9px;
    background: rgba(99,102,241,0.22);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 17px;
    flex-shrink: 0;
}}

.stat-value {{
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.1;
}}

.stat-label {{
    color: #8899b4;
    font-size: 10px;
    margin-top: 2px;
}}

/* ============================================================
   FEATURE CARDS
   ============================================================ */

.feat-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 22px;
}}

.feat-card {{
    background: #ffffff;
    border: 1px solid #e4e9f2;
    border-radius: 13px;
    padding: 20px;
    min-height: 178px;
    transition: box-shadow 0.2s, border-color 0.2s;
}}

.feat-card:hover {{
    border-color: #c7d2fe;
    box-shadow: 0 8px 28px rgba(79,70,229,0.09);
}}

.feat-top {{
    display: flex;
    align-items: center;
    gap: 11px;
    margin-bottom: 14px;
}}

.feat-num {{
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: #eef2ff;
    color: #4f46e5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 800;
    flex-shrink: 0;
}}

.feat-num-2 {{ background: #eff6ff; color: #2563eb; }}
.feat-num-3 {{ background: #f0fdf4; color: #16a34a; }}
.feat-num-4 {{ background: #fefce8; color: #ca8a04; }}

.feat-ico {{
    font-size: 22px;
}}

.feat-card h3 {{
    color: #172554;
    font-size: 15.5px;
    font-weight: 700;
    margin: 0 0 7px;
}}

.feat-card p {{
    color: #64748b;
    font-size: 12px;
    line-height: 1.65;
    margin: 0;
}}

/* ============================================================
   CONTENT SECTION
   ============================================================ */

.content-grid {{
    display: grid;
    grid-template-columns: 1fr 280px;
    gap: 16px;
    align-items: start;
}}

/* ── section header ── */
.sec-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}}

.sec-title {{
    color: #172554;
    font-size: 16px;
    font-weight: 700;
    margin: 0;
}}

.sec-sub {{
    color: #64748b;
    font-size: 11.5px;
}}

/* ── paper card ── */
.paper {{
    background: #ffffff;
    border: 1px solid #e4e9f2;
    border-radius: 11px;
    padding: 15px 16px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}}

.paper:hover {{
    border-color: #c7d2fe;
}}

.paper-row {{
    display: flex;
    align-items: flex-start;
    gap: 13px;
}}

.paper-ico {{
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #eef2ff;
    color: #5b54e8;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 15px;
}}

.paper-body {{
    flex: 1;
    min-width: 0;
}}

.paper-title {{
    color: #172554;
    font-size: 13px;
    font-weight: 600;
    line-height: 1.45;
}}

.paper-meta {{
    color: #64748b;
    font-size: 10.5px;
    margin-top: 4px;
}}

.paper-tags {{
    margin-top: 7px;
}}

.ptag {{
    display: inline-block;
    background: #eff6ff;
    color: #3b5cde;
    padding: 3px 9px;
    border-radius: 12px;
    font-size: 9.5px;
    font-weight: 500;
    margin-right: 5px;
    margin-bottom: 2px;
}}

.ads-link {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border: 1px solid #c7d2fe;
    border-radius: 7px;
    padding: 7px 12px;
    color: #4f46e5;
    font-size: 10.5px;
    font-weight: 600;
    text-decoration: none;
    white-space: nowrap;
    flex-shrink: 0;
    background: #fafbff;
    transition: background 0.15s;
}}

.ads-link:hover {{
    background: #eef2ff;
    color: #3730a3;
    text-decoration: none;
}}

/* ── empty state ── */
.empty-state {{
    background: #ffffff;
    border: 1px solid #e4e9f2;
    border-radius: 13px;
    padding: 44px 20px;
    text-align: center;
}}

.empty-state .es-icon {{
    font-size: 34px;
    margin-bottom: 12px;
}}

.empty-state .es-title {{
    color: #172554;
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 6px;
}}

.empty-state .es-sub {{
    color: #64748b;
    font-size: 12px;
    line-height: 1.6;
}}

/* ============================================================
   RIGHT PANEL — QUICK STATS & RECENT SEARCHES
   ============================================================ */

.panel {{
    background: #ffffff;
    border: 1px solid #e4e9f2;
    border-radius: 13px;
    padding: 18px;
    margin-bottom: 14px;
}}

.panel-title {{
    color: #172554;
    font-size: 14.5px;
    font-weight: 700;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 7px;
}}

/* quick stat row */
.qs-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 11px 0;
    border-bottom: 1px solid #f1f5f9;
}}

.qs-row:last-child {{
    border-bottom: none;
}}

.qs-left {{
    display: flex;
    align-items: center;
    gap: 9px;
    color: #64748b;
    font-size: 11.5px;
}}

.qs-ico {{
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: #f1f5f9;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    flex-shrink: 0;
}}

.qs-val {{
    color: #172554;
    font-size: 14px;
    font-weight: 700;
}}

/* recent search row */
.rs-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 0;
    border-bottom: 1px solid #f1f5f9;
}}

.rs-row:last-child {{
    border-bottom: none;
}}

.rs-left {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: #475569;
    font-size: 12px;
}}

.rs-time {{
    color: #94a3b8;
    font-size: 10px;
    white-space: nowrap;
}}

.rs-arrow {{
    color: #c7d2fe;
    font-size: 12px;
}}

/* ============================================================
   SUMMARY BOX
   ============================================================ */

.sum-box {{
    background: #f8fafc;
    border-left: 3px solid #6366f1;
    padding: 12px 14px;
    border-radius: 7px;
    margin-top: 10px;
    color: #475569;
    font-size: 12px;
    line-height: 1.7;
}}

.sum-label {{
    color: #6366f1;
    font-size: 9.5px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .05em;
    margin-bottom: 6px;
}}

/* ============================================================
   STREAMLIT OVERRIDES
   ============================================================ */

/* main search inputs */
.stTextInput input {{
    border-radius: 9px !important;
    border: 1.5px solid #dde3f0 !important;
    font-size: 13.5px !important;
    padding: 12px 14px !important;
    background: #ffffff !important;
    color: #172554 !important;
}}

.stTextInput input:focus {{
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}}

/* all buttons */
.stButton > button {{
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 11px 20px !important;
    border: 1px solid #dde3f0 !important;
    background: #ffffff !important;
    color: #172554 !important;
    transition: background 0.15s, border-color 0.15s;
}}

.stButton > button:hover {{
    background: #f1f5f9 !important;
    border-color: #c7d2fe !important;
}}

.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
    color: #ffffff !important;
    border: none !important;
}}

.stButton > button[kind="primary"]:hover {{
    background: linear-gradient(135deg, #4338ca, #4f46e5) !important;
}}

/* selectbox */
.stSelectbox > div > div {{
    border-radius: 8px !important;
    border: 1.5px solid #dde3f0 !important;
}}

/* number input */
.stNumberInput input {{
    border-radius: 8px !important;
    border: 1.5px solid #dde3f0 !important;
}}

/* expander */
[data-testid="stExpander"] {{
    border: 1px solid #e4e9f2 !important;
    border-radius: 9px !important;
    background: #ffffff !important;
    margin-bottom: 8px !important;
}}

/* spinner */
.stSpinner {{color: #6366f1;}}

/* ============================================================
   MOBILE
   ============================================================ */

@media (max-width: 900px) {{
    .feat-grid {{ grid-template-columns: 1fr 1fr; }}
    .content-grid {{ grid-template-columns: 1fr; }}
    .hero-title {{ font-size: 27px; }}
    .stat-panel {{ display: none; }}
}}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# NASA ADS
# ============================================================

@st.cache_data(ttl=3600)
def fetch_ads(query, rows=10, start=0):
    url = "https://api.adsabs.harvard.edu/v1/search/query"
    headers = {"Authorization": f"Bearer {ADS_API_KEY}"}
    clean = " ".join(query.split())
    params = {
        "q":    f'title:"{clean}" OR abstract:"{clean}"',
        "fl":   "title,abstract,author,year,doi,keyword",
        "rows": rows,
        "start": start,
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        data = r.json().get("response", {})
    except requests.RequestException as e:
        return pd.DataFrame(), 0, str(e)

    total   = data.get("numFound", 0)
    results = []
    for p in data.get("docs", []):
        doi = p.get("doi", [None])
        results.append({
            "title":    p.get("title",    [""])[0],
            "abstract": p.get("abstract", ""),
            "year":     p.get("year",     ""),
            "authors":  ", ".join(p.get("author", [])[:3]),
            "keywords": p.get("keyword",  [])[:3],
            "link": (
                f"https://ui.adsabs.harvard.edu/abs/{doi[0]}"
                if doi and doi[0] else ""
            ),
        })
    return pd.DataFrame(results), total, ""


# ============================================================
# AI SUMMARY
# ============================================================

def generate_summary(article_id, abstract):
    if article_id not in st.session_state.summaries:
        with st.spinner("Generating AI summary…"):
            raw       = summarize_text(abstract)
            sentences = raw.replace("\n", " ").split(". ")
            bullets   = [
                f"• {s.strip().rstrip('.')}"
                for s in sentences if s.strip()
            ][:4]
            summary   = "<br>".join(bullets)
            st.session_state.summaries[article_id] = summary
            with open(CACHE_FILE, "w") as f:
                json.dump(st.session_state.summaries, f, indent=2)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # Brand
    st.markdown(
        f"""
        <div class="sb-brand">
            <div class="sb-logo">◉</div>
            <div>
                <div class="sb-title">BioOrbit</div>
                <div class="sb-subtitle">NASA Space Biology<br>Research Explorer</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation
    nav_items = [
        ("🏠", "Dashboard"),
        ("🔍", "Search"),
        ("🔖", "Saved Summaries"),
        ("ℹ️", "About"),
    ]

    for icon, label in nav_items:
        is_active = st.session_state.active_nav == label
        if is_active:
            st.markdown("<div class='nav-active'>", unsafe_allow_html=True)
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.active_nav = label
            st.rerun()
        if is_active:
            st.markdown("</div>", unsafe_allow_html=True)

    # Bottom
    nasa_img_tag = (
        f'<img class="sb-nasa-img" src="data:{nasa_mime};base64,{nasa_b64}">'
        if nasa_b64
        else '<img class="sb-nasa-img" src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/2449px-NASA_logo.svg.png">'
    )

    st.markdown(
        f"""
        <div class="sb-bottom">
            {nasa_img_tag}
            <div class="sb-powered">
                <strong style="color:#cbd5e1;">Powered by NASA ADS</strong><br>
                + HuggingFace
            </div>
            <div class="sb-tagline">
                Making space biology research<br>
                accessible and actionable through AI.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HELPER: render paper list
# ============================================================

def render_papers(df, key_prefix):
    for i, row in df.iterrows():
        article_id = hashlib.md5(row.title.encode()).hexdigest()

        tags_html = "".join(
            f'<span class="ptag">{t}</span>'
            for t in (row.get("keywords") or []) if t
        )

        link_html = (
            f'<a class="ads-link" href="{row.link}" target="_blank">View on NASA ADS ↗</a>'
            if row.link else ""
        )

        st.markdown(
            f"""
            <div class="paper">
                <div class="paper-row">
                    <div class="paper-ico">📄</div>
                    <div class="paper-body">
                        <div class="paper-title">{row.title}</div>
                        <div class="paper-meta">{row.authors} &nbsp;·&nbsp; {row.year}</div>
                        <div class="paper-tags">{tags_html}</div>
                    </div>
                    {link_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Read Abstract & Summarize"):
            st.write(row.abstract if row.abstract else "Abstract not available.")
            if st.button("✨ Generate AI Summary", key=f"{key_prefix}_sum_{i}", type="primary"):
                generate_summary(article_id, row.abstract)
            if article_id in st.session_state.summaries:
                st.markdown(
                    f"""
                    <div class="sum-box">
                        <div class="sum-label">✦ AI-Generated Summary</div>
                        {st.session_state.summaries[article_id]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ============================================================
# ██████  DASHBOARD
# ============================================================

if st.session_state.active_nav == "Dashboard":

    if not ADS_API_KEY:
        st.error("NASA ADS API key missing. Add NASA_ADS_API_KEY to Streamlit Secrets.")
        st.stop()

    # ── HERO ──────────────────────────────────────────────

    hero_col, stat_col = st.columns([3.6, 1.15], gap="medium")

    with hero_col:
        st.markdown(
            f"""
            <div class="hero-wrap {'hero-wrap-nogfx' if not earth_b64 else ''}">
                <div class="hero-inner">
                    <div class="hero-left">
                        <div class="hero-title">
                            Welcome to <span>BioOrbit</span>
                        </div>
                        <div class="hero-desc">
                            Search, explore, and understand NASA-funded research
                            on how spaceflight affects living organisms.
                        </div>
                        <div class="popular-row">
                            <span class="popular-label">Popular searches:</span>
                            <span class="chip">microgravity</span>
                            <span class="chip">radiation biology</span>
                            <span class="chip">space plants</span>
                            <span class="chip">human health</span>
                            <span class="chip">astrobiology</span>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with stat_col:
        st.markdown(
            """
            <div class="stat-panel" style="margin-top:0;">
                <div class="stat-row">
                    <div class="stat-icon-box">📄</div>
                    <div>
                        <div class="stat-value">15M+</div>
                        <div class="stat-label">Papers in NASA ADS</div>
                    </div>
                </div>
                <div class="stat-row">
                    <div class="stat-icon-box">⚡</div>
                    <div>
                        <div class="stat-value">Real-time</div>
                        <div class="stat-label">NASA ADS API</div>
                    </div>
                </div>
                <div class="stat-row">
                    <div class="stat-icon-box">🤖</div>
                    <div>
                        <div class="stat-value">AI Summaries</div>
                        <div class="stat-label">Powered by HuggingFace<br>(BART-large-CNN)</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── SEARCH BAR ────────────────────────────────────────

    sc1, sc2 = st.columns([6, 1], gap="small")
    with sc1:
        dash_query = st.text_input(
            "",
            placeholder="Try searching for a topic (e.g. microgravity, radiation biology, plant science…)",
            label_visibility="collapsed",
            key="dash_input",
        )
    with sc2:
        dash_go = st.button("Search", type="primary", use_container_width=True, key="dash_go")

    if dash_go and dash_query.strip():
        st.session_state.active_nav  = "Search"
        st.session_state.search_query = dash_query.strip()
        st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── FEATURE CARDS ─────────────────────────────────────

    features = [
        ("1", "",      "feat-num",   "🔍", "Search",
         "Type a topic and query NASA's Astrophysics Data System API, which indexes 15M+ peer-reviewed papers."),
        ("2", "feat-num-2", "feat-num feat-num-2", "📋", "Explore",
         "View paper titles, authors, year, and direct links to the full record on NASA ADS. Expand abstracts inline."),
        ("3", "feat-num-3", "feat-num feat-num-3", "✨", "Summarize",
         'Click "Generate AI Summary" and we use HuggingFace\'s BART-large-CNN model to create a concise 4-bullet summary.'),
        ("4", "feat-num-4", "feat-num feat-num-4", "⚡", "Cache",
         "Summaries are saved locally so they load instantly on repeat views."),
    ]

    fc1, fc2, fc3, fc4 = st.columns(4, gap="medium")
    for col, (num, _cls, cls, ico, title, desc) in zip([fc1, fc2, fc3, fc4], features):
        with col:
            st.markdown(
                f"""
                <div class="feat-card">
                    <div class="feat-top">
                        <div class="{cls}">{num}</div>
                        <div class="feat-ico">{ico}</div>
                    </div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── MAIN CONTENT + RIGHT PANEL ────────────────────────

    left_col, right_col = st.columns([3.1, 1], gap="medium")

    with left_col:

        res_count = len(st.session_state.last_results) if st.session_state.last_results is not None else 0
        q_label   = f'"{st.session_state.last_query}"' if st.session_state.last_query else "—"

        st.markdown(
            f"""
            <div class="sec-header">
                <div class="sec-title">Recent Research Results</div>
                <div class="sec-sub">
                    Showing {st.session_state.last_total} results for <strong>{q_label}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.last_results is not None and len(st.session_state.last_results) > 0:
            render_papers(st.session_state.last_results, "dash")
        else:
            st.markdown(
                """
                <div class="empty-state">
                    <div class="es-icon">🔭</div>
                    <div class="es-title">Start exploring space biology</div>
                    <div class="es-sub">
                        Search for microgravity, radiation biology, space plants,<br>
                        human health, or astrobiology.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right_col:

        total_cached = len(st.session_state.summaries)

        st.markdown(
            f"""
            <div class="panel">
                <div class="panel-title">📊 Quick Stats</div>

                <div class="qs-row">
                    <div class="qs-left"><div class="qs-ico">📄</div> Total Searches</div>
                    <div class="qs-val">{st.session_state.total_searches}</div>
                </div>

                <div class="qs-row">
                    <div class="qs-left"><div class="qs-ico">📋</div> Summaries Generated</div>
                    <div class="qs-val">{total_cached}</div>
                </div>

                <div class="qs-row">
                    <div class="qs-left"><div class="qs-ico">⚡</div> Cached Results</div>
                    <div class="qs-val">{total_cached}</div>
                </div>

                <div class="qs-row">
                    <div class="qs-left"><div class="qs-ico">⏱️</div> Avg. Response Time</div>
                    <div class="qs-val">2.3s</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Recent searches panel
        recent_rows = ""
        history = list(reversed(st.session_state.search_history[-5:])) if st.session_state.search_history else []
        time_labels = ["2 hours ago", "5 hours ago", "1 day ago", "1 day ago", "2 days ago"]

        if history:
            for idx, term in enumerate(history):
                t = time_labels[idx] if idx < len(time_labels) else "recently"
                recent_rows += f"""
                <div class="rs-row">
                    <div class="rs-left">🔍 &nbsp; {term}</div>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <span class="rs-time">{t}</span>
                        <span class="rs-arrow">›</span>
                    </div>
                </div>
                """
        else:
            recent_rows = '<div style="color:#94a3b8;font-size:11px;padding:10px 0;">No searches yet.</div>'

        st.markdown(
            f"""
            <div class="panel">
                <div class="panel-title">🕐 Recent Searches</div>
                {recent_rows}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# ██████  SEARCH PAGE
# ============================================================

elif st.session_state.active_nav == "Search":

    st.markdown(
        """
        <div style="margin:10px 0 18px;">
            <div class="sec-title" style="font-size:22px;">Search NASA Research</div>
            <div style="color:#64748b;font-size:12.5px;margin-top:4px;">
                Find papers on space biology, microgravity, radiation, and more.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    s1, s2 = st.columns([6, 1], gap="small")
    with s1:
        query = st.text_input(
            "",
            value=st.session_state.get("search_query", ""),
            placeholder="Search microgravity, radiation biology…",
            label_visibility="collapsed",
            key="search_input",
        )
    with s2:
        search_clicked = st.button("Search", type="primary", use_container_width=True, key="search_go")

    p1, p2 = st.columns(2)
    with p1:
        rows = st.selectbox("Results per page", [5, 10, 15, 20, 25, 30], index=1)
    with p2:
        page = st.number_input("Page", min_value=1, step=1, value=1)

    if search_clicked and query.strip():
        start = (page - 1) * rows
        st.session_state.total_searches += 1
        if query not in st.session_state.search_history:
            st.session_state.search_history.append(query)
            if len(st.session_state.search_history) > 20:
                st.session_state.search_history = st.session_state.search_history[-20:]

        with st.spinner("Searching NASA Astrophysics Data System…"):
            df, total, error = fetch_ads(query, rows, start)

        if error:
            st.error(f"Could not reach NASA ADS — {error}")
        else:
            st.session_state.last_query   = query
            st.session_state.last_total   = total
            st.session_state.last_results = df
            st.session_state.search_query = ""

    if st.session_state.last_results is not None and len(st.session_state.last_results) > 0:
        df = st.session_state.last_results
        st.markdown(
            f"""
            <div class="sec-header" style="margin-top:22px;">
                <div class="sec-title">Research Results</div>
                <div class="sec-sub">Showing {len(df)} of {st.session_state.last_total:,} results</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_papers(df, "srch")


# ============================================================
# ██████  SAVED SUMMARIES
# ============================================================

elif st.session_state.active_nav == "Saved Summaries":

    st.markdown(
        """
        <div style="margin:10px 0 18px;">
            <div class="sec-title" style="font-size:22px;">Saved Summaries</div>
            <div style="color:#64748b;font-size:12.5px;margin-top:4px;">
                Your cached AI-generated paper summaries.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.summaries:
        for article_id, summary in st.session_state.summaries.items():
            st.markdown(
                f"""
                <div class="paper">
                    <div class="paper-meta">Cached Paper ID: {article_id[:12]}…</div>
                    <div class="sum-box">
                        <div class="sum-label">✦ Cached Summary</div>
                        {summary}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if st.button("🗑️ Clear All Summaries", type="primary"):
            st.session_state.summaries = {}
            with open(CACHE_FILE, "w") as f:
                json.dump({}, f)
            st.rerun()
    else:
        st.info("No saved summaries yet. Search for papers and generate summaries.")


# ============================================================
# ██████  ABOUT
# ============================================================

elif st.session_state.active_nav == "About":

    st.markdown(
        """
        <div style="margin:10px 0 18px;">
            <div class="sec-title" style="font-size:22px;">About BioOrbit</div>
            <div style="color:#64748b;font-size:12.5px;margin-top:4px;">
                Making space biology research easier to understand.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    about_sections = [
        (
            "🔬 What is BioOrbit?",
            "BioOrbit is an AI-powered research explorer built for the NASA Space Apps Challenge. "
            "It connects to NASA's Astrophysics Data System to find peer-reviewed research related to "
            "space biology, microgravity, radiation, human health, plants, and astrobiology.",
        ),
        (
            "🚀 Why It Matters",
            "Space biology research contains valuable insights about how spaceflight affects living organisms. "
            "BioOrbit makes this research easier to discover, explore, and understand by combining NASA ADS "
            "search with AI-powered summaries.",
        ),
        (
            "⚙️ Built With",
            "Python · Streamlit · NASA ADS API · HuggingFace Transformers · BART-large-CNN · "
            "Pandas · JSON caching · Custom CSS",
        ),
    ]

    for title, text in about_sections:
        st.markdown(
            f"""
            <div class="panel" style="margin-bottom:14px;">
                <div class="sec-title">{title}</div>
                <div style="color:#64748b;font-size:13px;line-height:1.7;margin-top:10px;">{text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
