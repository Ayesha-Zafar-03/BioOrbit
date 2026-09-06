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
CACHE_FILE  = "summary_cache.json"
BASE_DIR    = Path(__file__).resolve().parent
EARTH_IMAGE = BASE_DIR / "assets" / "eathbackgroug.jpg"
NASA_LOGO   = BASE_DIR / "assets" / "logonasa.png"

# ============================================================
# HELPERS
# ============================================================

def img_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

earth_b64 = img_b64(EARTH_IMAGE) if EARTH_IMAGE.exists() else ""
nasa_b64  = img_b64(NASA_LOGO)   if NASA_LOGO.exists()   else ""

# ============================================================
# SESSION STATE
# ============================================================

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE) as f:
            _cache = json.load(f)
    except Exception:
        _cache = {}
else:
    _cache = {}

for k, v in {
    "summaries":      _cache,
    "total_searches": 0,
    "search_history": [],
    "active_nav":     "Dashboard",
    "last_results":   None,
    "last_query":     "",
    "last_total":     0,
    "search_query":   "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# SVG ICON LIBRARY
# ============================================================

# All icons rendered as inline SVG — no emojis anywhere

ICO = {
    # sidebar nav
    "home": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>""",
    "search": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>""",
    "bookmark": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>""",
    "info": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>""",
    # stat panel
    "file": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>""",
    "zap": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>""",
    "bot": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>""",
    # feature cards
    "search_lg": """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>""",
    "list": """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>""",
    "sparkle": """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/></svg>""",
    "zap_lg": """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ca8a04" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>""",
    # paper / quick stats
    "paper_ico": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#5b54e8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>""",
    "qs_search": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>""",
    "qs_file": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>""",
    "qs_zap": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>""",
    "qs_clock": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>""",
    "qs_bar": """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#172554" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>""",
    "clock_sm": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#172554" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>""",
    "search_sm": """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>""",
    "external": """<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>""",
    "chevron": """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#c7d2fe" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>""",
}

# ============================================================
# CSS
# ============================================================

hero_bg = (
    f"url('data:image/jpeg;base64,{earth_b64}')"
    if earth_b64 else "none"
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

*, *::before, *::after {{
    font-family: 'Inter', sans-serif !important;
    box-sizing: border-box;
}}

/* ── app shell ── */
.stApp {{ background: #eef0f7 !important; }}
#MainMenu, footer, header {{ visibility: hidden !important; }}
.stDeployButton {{ display: none !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
.block-container {{
    padding: 0 1.1rem 2rem !important;
    max-width: 100% !important;
}}

/* ============================================================
   SIDEBAR
   ============================================================ */

[data-testid="stSidebar"] {{
    background: #0b1121 !important;
    min-width: 250px !important;
    max-width: 250px !important;
}}

[data-testid="stSidebarContent"] {{
    padding: 24px 14px 20px !important;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    gap: 0;
}}

/* ── brand ── */
.sb-brand {{
    display: flex;
    align-items: center;
    gap: 11px;
    padding-bottom: 20px;
    margin-bottom: 14px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}}

/* orbit ring logo — pure CSS */
.orbit-logo {{
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: 2px solid #7c6ff0;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    flex-shrink: 0;
}}
.orbit-logo::before {{
    content: "";
    position: absolute;
    width: 56px;
    height: 18px;
    border: 2px solid #7c6ff0;
    border-radius: 50%;
    transform: rotate(-30deg);
}}
.orbit-dot {{
    width: 10px;
    height: 10px;
    background: #a78bfa;
    border-radius: 50%;
    position: relative;
    z-index: 1;
}}

.sb-name {{ color: #fff; font-size: 21px; font-weight: 800; line-height: 1; }}
.sb-sub  {{ color: #7a8fa8; font-size: 10.5px; line-height: 1.45; margin-top: 3px; }}

/* ── nav ── */
.nav-section {{ flex: 1; }}

[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    border: none !important;
    color: #7a8fa8 !important;
    text-align: left !important;
    border-radius: 9px !important;
    padding: 10px 14px !important;
    margin-bottom: 2px !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    transition: background .15s, color .15s;
}}

[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(99,102,241,0.13) !important;
    color: #ffffff !important;
}}

/* active nav */
.nav-active [data-testid="stSidebar"] .stButton > button,
.nav-active .stButton > button {{
    background: linear-gradient(90deg,#4f46e5,#5b54e8) !important;
    color: #fff !important;
}}

/* ── sidebar bottom ── */
.sb-bottom {{
    margin-top: auto;
    padding-top: 18px;
    border-top: 1px solid rgba(255,255,255,0.06);
}}
.sb-nasa-img {{ width: 58px; height: auto; margin-bottom: 9px; display: block; }}
.sb-powered  {{ font-size: 11px; color: #8899b4; line-height: 1.5; }}
.sb-powered strong {{ color: #c8d5e8; }}
.sb-tagline  {{ font-size: 10.5px; color: #4a5a6e; line-height: 1.55; margin-top: 9px; }}

/* ============================================================
   HERO — full-width banner with image bg
   ============================================================ */

.hero-wrap {{
    border-radius: 14px;
    overflow: hidden;
    position: relative;
    min-height: 290px;
    background:
        linear-gradient(90deg,
            rgba(4,10,26,.97) 0%,
            rgba(4,10,26,.90) 34%,
            rgba(4,10,26,.30) 65%,
            rgba(4,10,26,.0) 100%
        ),
        {hero_bg};
    background-size: cover;
    background-position: center right;
    display: flex;
    align-items: center;
    padding: 36px 36px 32px;
}}

.hero-left {{
    flex: 1;
    position: relative;
    z-index: 2;
}}

.hero-title {{
    color: #fff;
    font-size: 40px;
    font-weight: 800;
    letter-spacing: -1.2px;
    line-height: 1.1;
    margin: 0 0 12px;
}}
.hero-title span {{ color: #8b7cf6; }}

.hero-desc {{
    color: #c0cfe4;
    font-size: 14.5px;
    line-height: 1.65;
    max-width: 480px;
    margin-bottom: 24px;
}}

/* popular row inside hero */
.popular-row {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 7px;
}}
.popular-lbl {{ color: #8899b4; font-size: 12px; white-space: nowrap; }}
.chip {{
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.22);
    background: rgba(255,255,255,0.06);
    color: #c0cfe4;
    font-size: 11.5px;
    cursor: default;
}}

/* ── stat panel inside hero ── */
.stat-panel {{
    background: rgba(4,12,32,.82);
    border: 1px solid rgba(148,163,184,.22);
    backdrop-filter: blur(8px);
    border-radius: 13px;
    padding: 6px 16px;
    min-width: 210px;
    flex-shrink: 0;
    align-self: flex-start;
    position: relative;
    z-index: 2;
}}

.stat-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 13px 0;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}}
.stat-row:last-child {{ border-bottom: none; }}

.stat-ico-box {{
    width: 36px;
    height: 36px;
    border-radius: 9px;
    background: rgba(99,102,241,.22);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}

.stat-val   {{ color:#fff; font-size:15px; font-weight:700; line-height:1.1; }}
.stat-lbl   {{ color:#7a8fa8; font-size:10px; margin-top:2px; line-height:1.4; }}

/* ============================================================
   SEARCH BAR  (below hero)
   ============================================================ */

.search-bar-wrap {{
    display: flex;
    gap: 10px;
    margin: 16px 0 20px;
}}

/* Streamlit input override */
.stTextInput > div > div > input {{
    border-radius: 9px !important;
    border: 1.5px solid #d8deee !important;
    font-size: 13.5px !important;
    padding: 12px 14px !important;
    background: #fff !important;
    color: #172554 !important;
    height: 48px !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,.12) !important;
}}

/* ============================================================
   FEATURE CARDS
   ============================================================ */

.feat-grid {{
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 14px;
    margin-bottom: 22px;
}}
.feat-card {{
    background: #fff;
    border: 1px solid #e2e8f4;
    border-radius: 14px;
    padding: 20px;
    min-height: 174px;
    transition: box-shadow .2s, border-color .2s;
}}
.feat-card:hover {{ border-color:#c7d2fe; box-shadow:0 8px 28px rgba(79,70,229,.09); }}
.feat-top {{ display:flex; align-items:center; gap:11px; margin-bottom:14px; }}

.feat-num {{
    width:34px; height:34px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:14px; font-weight:800; flex-shrink:0;
}}
.fn1 {{ background:#eef2ff; color:#4f46e5; }}
.fn2 {{ background:#eff6ff; color:#2563eb; }}
.fn3 {{ background:#f0fdf4; color:#16a34a; }}
.fn4 {{ background:#fefce8; color:#ca8a04; }}

.feat-card h3 {{ color:#172554; font-size:15px; font-weight:700; margin:0 0 7px; }}
.feat-card p  {{ color:#64748b; font-size:12px; line-height:1.65; margin:0; }}

/* ============================================================
   CONTENT LAYOUT
   ============================================================ */

.content-grid {{
    display: grid;
    grid-template-columns: 1fr 274px;
    gap: 16px;
    align-items: start;
}}

.sec-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}}
.sec-title {{ color:#172554; font-size:16px; font-weight:700; }}
.sec-sub   {{ color:#64748b; font-size:11.5px; }}

/* ============================================================
   PAPER CARDS
   ============================================================ */

.paper {{
    background: #fff;
    border: 1px solid #e2e8f4;
    border-radius: 12px;
    padding: 15px 16px;
    margin-bottom: 10px;
    transition: border-color .2s;
}}
.paper:hover {{ border-color:#c7d2fe; }}

.paper-row {{ display:flex; align-items:flex-start; gap:13px; }}

.paper-ico {{
    width:36px; height:36px; border-radius:50%;
    background:#eef2ff; color:#5b54e8;
    display:flex; align-items:center; justify-content:center;
    flex-shrink:0;
}}

.paper-body {{ flex:1; min-width:0; }}
.paper-title {{ color:#172554; font-size:13px; font-weight:600; line-height:1.45; }}
.paper-meta  {{ color:#64748b; font-size:10.5px; margin-top:4px; }}
.paper-tags  {{ margin-top:7px; }}

.ptag {{
    display:inline-block;
    background:#eff6ff; color:#3b5cde;
    padding:3px 9px; border-radius:12px;
    font-size:9.5px; font-weight:500;
    margin-right:5px; margin-bottom:2px;
}}

.ads-link {{
    display:inline-flex; align-items:center; gap:5px;
    border:1px solid #c7d2fe; border-radius:7px;
    padding:7px 12px; color:#4f46e5;
    font-size:10.5px; font-weight:600;
    text-decoration:none; white-space:nowrap;
    flex-shrink:0; background:#fafbff;
    transition: background .15s;
}}
.ads-link:hover {{ background:#eef2ff; text-decoration:none; }}

/* empty state */
.empty-state {{
    background:#fff; border:1px solid #e2e8f4;
    border-radius:13px; padding:46px 20px; text-align:center;
}}
.es-icon  {{ font-size:34px; margin-bottom:12px; }}
.es-title {{ color:#172554; font-size:15px; font-weight:700; margin-bottom:6px; }}
.es-sub   {{ color:#64748b; font-size:12px; line-height:1.6; }}

/* ============================================================
   RIGHT PANEL
   ============================================================ */

.panel {{
    background:#fff; border:1px solid #e2e8f4;
    border-radius:13px; padding:18px; margin-bottom:14px;
}}
.panel-title {{
    color:#172554; font-size:14px; font-weight:700;
    margin-bottom:14px; display:flex; align-items:center; gap:7px;
}}

/* quick stats rows */
.qs-row {{
    display:flex; align-items:center; justify-content:space-between;
    padding:11px 0; border-bottom:1px solid #f1f5f9;
}}
.qs-row:last-child {{ border-bottom:none; }}
.qs-left {{
    display:flex; align-items:center; gap:9px;
    color:#64748b; font-size:11.5px;
}}
.qs-ico {{
    width:30px; height:30px; border-radius:50%;
    background:#f1f5f9; display:flex; align-items:center; justify-content:center;
    flex-shrink:0;
}}
.qs-val {{ color:#172554; font-size:14px; font-weight:700; }}

/* recent search rows */
.rs-row {{
    display:flex; justify-content:space-between; align-items:center;
    padding:9px 0; border-bottom:1px solid #f1f5f9;
}}
.rs-row:last-child {{ border-bottom:none; }}
.rs-left {{
    display:flex; align-items:center; gap:8px;
    color:#475569; font-size:12px;
}}
.rs-time {{ color:#94a3b8; font-size:10px; white-space:nowrap; }}

/* ============================================================
   SUMMARY BOX
   ============================================================ */

.sum-box {{
    background:#f8fafc; border-left:3px solid #6366f1;
    padding:12px 14px; border-radius:7px; margin-top:10px;
    color:#475569; font-size:12px; line-height:1.7;
}}
.sum-label {{
    color:#6366f1; font-size:9.5px; font-weight:800;
    text-transform:uppercase; letter-spacing:.05em; margin-bottom:6px;
}}

/* ============================================================
   STREAMLIT BUTTON OVERRIDES
   ============================================================ */

.stButton > button {{
    border-radius:8px !important;
    font-weight:600 !important;
    font-size:13px !important;
    padding:11px 20px !important;
    border:1px solid #d8deee !important;
    background:#fff !important;
    color:#172554 !important;
    height:48px !important;
    transition: background .15s, border-color .15s;
}}
.stButton > button:hover {{
    background:#f1f5f9 !important;
    border-color:#c7d2fe !important;
}}
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg,#4f46e5,#6366f1) !important;
    color:#fff !important;
    border:none !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: linear-gradient(135deg,#4338ca,#4f46e5) !important;
}}

/* selectbox / number input */
.stSelectbox > div > div {{
    border-radius:8px !important; border:1.5px solid #d8deee !important;
}}
.stNumberInput input {{
    border-radius:8px !important; border:1.5px solid #d8deee !important;
}}

/* expander */
[data-testid="stExpander"] {{
    border:1px solid #e2e8f4 !important;
    border-radius:9px !important;
    background:#fff !important;
    margin-bottom:8px !important;
}}

/* divider */
hr {{ border-color: #e2e8f4 !important; }}

@media (max-width:900px) {{
    .feat-grid {{ grid-template-columns:1fr 1fr; }}
    .content-grid {{ grid-template-columns:1fr; }}
    .hero-title {{ font-size:27px; }}
    .stat-panel {{ display:none; }}
}}
</style>
""", unsafe_allow_html=True)

# ============================================================
# NASA ADS
# ============================================================

@st.cache_data(ttl=3600)
def fetch_ads(query, rows=10, start=0):
    url     = "https://api.adsabs.harvard.edu/v1/search/query"
    headers = {"Authorization": f"Bearer {ADS_API_KEY}"}
    clean   = " ".join(query.split())
    params  = {
        "q":     f'title:"{clean}" OR abstract:"{clean}"',
        "fl":    "title,abstract,author,year,doi,keyword",
        "rows":  rows,
        "start": start,
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        data = r.json().get("response", {})
    except requests.RequestException as e:
        return pd.DataFrame(), 0, str(e)

    total = data.get("numFound", 0)
    rows_out = []
    for p in data.get("docs", []):
        doi = p.get("doi", [None])
        rows_out.append({
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
    return pd.DataFrame(rows_out), total, ""

# ============================================================
# AI SUMMARY
# ============================================================

def generate_summary(article_id, abstract):
    if article_id not in st.session_state.summaries:
        with st.spinner("Generating AI summary…"):
            raw     = summarize_text(abstract)
            sents   = raw.replace("\n", " ").split(". ")
            bullets = [f"• {s.strip().rstrip('.')}" for s in sents if s.strip()][:4]
            summary = "<br>".join(bullets)
            st.session_state.summaries[article_id] = summary
            with open(CACHE_FILE, "w") as f:
                json.dump(st.session_state.summaries, f, indent=2)

# ============================================================
# RENDER PAPER LIST
# ============================================================

def _paper_card_html(row):
    """Return safe HTML for a single paper card (no injected variables that could break tags)."""
    tags_html = "".join(
        f'<span class="ptag">{t}</span>'
        for t in (row.get("keywords") or []) if t
    )
    # Build link separately, never injected mid-tag
    if row.get("link"):
        link_part = (
            f'<a class="ads-link" href="{row["link"]}" target="_blank">'
            f'View on NASA ADS&#8203;</a>'
        )
    else:
        link_part = '<span style="width:120px;display:inline-block;"></span>'

    title   = str(row.get("title",   "") or "").replace("<", "&lt;").replace(">", "&gt;")
    authors = str(row.get("authors", "") or "").replace("<", "&lt;").replace(">", "&gt;")
    year    = str(row.get("year",    "") or "").replace("<", "&lt;").replace(">", "&gt;")

    paper_ico = ICO["paper_ico"]

    return (
        '<div class="paper">'
          '<div class="paper-row">'
            f'<div class="paper-ico">{paper_ico}</div>'
            '<div class="paper-body">'
              f'<div class="paper-title">{title}</div>'
              f'<div class="paper-meta">{authors} &nbsp;&middot;&nbsp; {year}</div>'
              f'<div class="paper-tags">{tags_html}</div>'
            '</div>'
            f'{link_part}'
          '</div>'
        '</div>'
    )


def render_papers(df, key_prefix):
    for i, row in df.iterrows():
        aid = hashlib.md5(str(row.get("title", i)).encode()).hexdigest()

        # Render paper card as its own isolated markdown block
        st.markdown(_paper_card_html(row), unsafe_allow_html=True)

        # Expander below the card — completely separate Streamlit element
        with st.expander("Read Abstract & Summarize"):
            abstract = row.get("abstract") or ""
            st.write(abstract if abstract else "Abstract not available.")

            if st.button("Generate AI Summary", key=f"{key_prefix}_sum_{i}", type="primary"):
                generate_summary(aid, abstract)

            if aid in st.session_state.summaries:
                st.markdown(
                    '<div class="sum-box">'
                    '<div class="sum-label">AI-Generated Summary</div>'
                    + st.session_state.summaries[aid]
                    + '</div>',
                    unsafe_allow_html=True,
                )

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # Brand
    st.markdown("""
    <div class="sb-brand">
        <div class="orbit-logo"><div class="orbit-dot"></div></div>
        <div>
            <div class="sb-name">BioOrbit</div>
            <div class="sb-sub">NASA Space Biology<br>Research Explorer</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Nav items — icon labels use HTML span trick
    nav_items = [
        ("Dashboard",       ICO["home"],     "Home"),
        ("Search",          ICO["search"],   "Search"),
        ("Saved Summaries", ICO["bookmark"], "Saved Summaries"),
        ("About",           ICO["info"],     "About"),
    ]

    st.markdown('<div class="nav-section">', unsafe_allow_html=True)
    for page, _ico, label in nav_items:
        is_active = st.session_state.active_nav == page
        if is_active:
            st.markdown("<div class='nav-active'>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{page}", use_container_width=True):
            st.session_state.active_nav = page
            st.rerun()
        if is_active:
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Bottom
    nasa_src = (
        f"data:image/png;base64,{nasa_b64}"
        if nasa_b64
        else "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/2449px-NASA_logo.svg.png"
    )
    st.markdown(f"""
    <div class="sb-bottom">
        <img class="sb-nasa-img" src="{nasa_src}">
        <div class="sb-powered">
            <strong>Powered by NASA ADS</strong><br>+ HuggingFace
        </div>
        <div class="sb-tagline">
            Making space biology research<br>accessible and actionable through AI.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# ██  DASHBOARD
# ============================================================

if st.session_state.active_nav == "Dashboard":

    if not ADS_API_KEY:
        st.error("NASA ADS API key missing. Add NASA_ADS_API_KEY to Streamlit Secrets.")
        st.stop()

    # ── HERO + STAT PANEL side by side ──────────────────────
    hero_col, stat_col = st.columns([3.6, 1.1], gap="medium")

    with hero_col:
        st.markdown(f"""
        <div class="hero-wrap">
            <div class="hero-left">
                <div class="hero-title">Welcome to <span>BioOrbit</span></div>
                <div class="hero-desc">
                    Search, explore, and understand NASA-funded research
                    on how spaceflight affects living organisms.
                </div>
                <div class="popular-row">
                    <span class="popular-lbl">Popular searches:</span>
                    <span class="chip">microgravity</span>
                    <span class="chip">radiation biology</span>
                    <span class="chip">space plants</span>
                    <span class="chip">human health</span>
                    <span class="chip">astrobiology</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with stat_col:
        st.markdown(f"""
        <div class="stat-panel">
            <div class="stat-row">
                <div class="stat-ico-box">{ICO["file"]}</div>
                <div>
                    <div class="stat-val">15M+</div>
                    <div class="stat-lbl">Papers in NASA ADS</div>
                </div>
            </div>
            <div class="stat-row">
                <div class="stat-ico-box">{ICO["zap"]}</div>
                <div>
                    <div class="stat-val">Real-time</div>
                    <div class="stat-lbl">NASA ADS API</div>
                </div>
            </div>
            <div class="stat-row">
                <div class="stat-ico-box">{ICO["bot"]}</div>
                <div>
                    <div class="stat-val">AI Summaries</div>
                    <div class="stat-lbl">Powered by HuggingFace<br>(BART-large-CNN)</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── SEARCH BAR ──────────────────────────────────────────
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
        st.session_state.active_nav   = "Search"
        st.session_state.search_query = dash_query.strip()
        st.rerun()

    # ── FEATURE CARDS ───────────────────────────────────────
    features = [
        ("1", "fn1", ICO["search_lg"], "Search",
         "Type a topic and query NASA's Astrophysics Data System API, which indexes 15M+ peer-reviewed papers."),
        ("2", "fn2", ICO["list"],      "Explore",
         "View paper titles, authors, year, and direct links to the full record on NASA ADS. Expand abstracts inline."),
        ("3", "fn3", ICO["sparkle"],   "Summarize",
         'Click "Generate AI Summary" and we use HuggingFace\'s BART-large-CNN model to create a concise 4-bullet summary.'),
        ("4", "fn4", ICO["zap_lg"],    "Cache",
         "Summaries are saved locally so they load instantly on repeat views."),
    ]

    fc1, fc2, fc3, fc4 = st.columns(4, gap="medium")
    for col, (num, fn_cls, ico, title, desc) in zip([fc1, fc2, fc3, fc4], features):
        with col:
            st.markdown(f"""
            <div class="feat-card">
                <div class="feat-top">
                    <div class="feat-num {fn_cls}">{num}</div>
                    <div>{ico}</div>
                </div>
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    # ── MAIN CONTENT + RIGHT PANEL ──────────────────────────
    left_col, right_col = st.columns([3.1, 1], gap="medium")

    with left_col:
        q_label = f'"{st.session_state.last_query}"' if st.session_state.last_query else "—"
        st.markdown(f"""
        <div class="sec-header">
            <div class="sec-title">Recent Research Results</div>
            <div class="sec-sub">
                Showing {st.session_state.last_total} results for <strong>{q_label}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.last_results is not None and len(st.session_state.last_results) > 0:
            render_papers(st.session_state.last_results, "dash")
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="es-title">Start exploring space biology</div>
                <div class="es-sub">
                    Search for microgravity, radiation biology, space plants,<br>
                    human health, or astrobiology above.
                </div>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        total_cached = len(st.session_state.summaries)

        st.markdown(f"""
        <div class="panel">
            <div class="panel-title">{ICO["qs_bar"]} Quick Stats</div>
            <div class="qs-row">
                <div class="qs-left"><div class="qs-ico">{ICO["qs_file"]}</div>Total Searches</div>
                <div class="qs-val">{st.session_state.total_searches}</div>
            </div>
            <div class="qs-row">
                <div class="qs-left"><div class="qs-ico">{ICO["qs_file"]}</div>Summaries Generated</div>
                <div class="qs-val">{total_cached}</div>
            </div>
            <div class="qs-row">
                <div class="qs-left"><div class="qs-ico">{ICO["qs_zap"]}</div>Cached Results</div>
                <div class="qs-val">{total_cached}</div>
            </div>
            <div class="qs-row">
                <div class="qs-left"><div class="qs-ico">{ICO["qs_clock"]}</div>Avg. Response Time</div>
                <div class="qs-val">2.3s</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Recent searches
        history = list(reversed(st.session_state.search_history[-5:])) if st.session_state.search_history else []
        time_labels = ["2 hours ago", "5 hours ago", "1 day ago", "1 day ago", "2 days ago"]

        rows_html = ""
        if history:
            for idx, term in enumerate(history):
                t = time_labels[idx] if idx < len(time_labels) else "recently"
                rows_html += f"""
                <div class="rs-row">
                    <div class="rs-left">{ICO["search_sm"]} &nbsp;{term}</div>
                    <div style="display:flex;align-items:center;gap:5px;">
                        <span class="rs-time">{t}</span>
                        {ICO["chevron"]}
                    </div>
                </div>"""
        else:
            rows_html = '<div style="color:#94a3b8;font-size:11px;padding:10px 0;">No searches yet.</div>'

        st.markdown(f"""
        <div class="panel">
            <div class="panel-title">{ICO["clock_sm"]} Recent Searches</div>
            {rows_html}
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# ██  SEARCH PAGE
# ============================================================

elif st.session_state.active_nav == "Search":

    st.markdown("""
    <div style="margin:14px 0 18px;">
        <div class="sec-title" style="font-size:22px;">Search NASA Research</div>
        <div style="color:#64748b;font-size:12.5px;margin-top:4px;">
            Find papers on space biology, microgravity, radiation, and more.
        </div>
    </div>
    """, unsafe_allow_html=True)

    s1, s2 = st.columns([6, 1], gap="small")
    with s1:
        query = st.text_input(
            "", value=st.session_state.get("search_query", ""),
            placeholder="Search microgravity, radiation biology…",
            label_visibility="collapsed", key="search_input",
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
        st.markdown(f"""
        <div class="sec-header" style="margin-top:22px;">
            <div class="sec-title">Research Results</div>
            <div class="sec-sub">Showing {len(df)} of {st.session_state.last_total:,} results</div>
        </div>
        """, unsafe_allow_html=True)
        render_papers(df, "srch")

# ============================================================
# ██  SAVED SUMMARIES
# ============================================================

elif st.session_state.active_nav == "Saved Summaries":

    st.markdown("""
    <div style="margin:14px 0 18px;">
        <div class="sec-title" style="font-size:22px;">Saved Summaries</div>
        <div style="color:#64748b;font-size:12.5px;margin-top:4px;">Your cached AI-generated paper summaries.</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.summaries:
        for aid, summary in st.session_state.summaries.items():
            st.markdown(f"""
            <div class="paper">
                <div class="paper-meta" style="margin-bottom:8px;">Cached Paper ID: {aid[:12]}…</div>
                <div class="sum-box">
                    <div class="sum-label">Cached Summary</div>
                    {summary}
                </div>
            </div>
            """, unsafe_allow_html=True)
        if st.button("Clear All Summaries", type="primary"):
            st.session_state.summaries = {}
            with open(CACHE_FILE, "w") as f:
                json.dump({}, f)
            st.rerun()
    else:
        st.info("No saved summaries yet. Search for papers and generate summaries.")

# ============================================================
# ██  ABOUT
# ============================================================

elif st.session_state.active_nav == "About":

    st.markdown("""
    <div style="margin:14px 0 18px;">
        <div class="sec-title" style="font-size:22px;">About BioOrbit</div>
        <div style="color:#64748b;font-size:12.5px;margin-top:4px;">Making space biology research easier to understand.</div>
    </div>
    """, unsafe_allow_html=True)

    for title, text in [
        ("What is BioOrbit?",
         "BioOrbit is an AI-powered research explorer built for the NASA Space Apps Challenge. "
         "It connects to NASA's Astrophysics Data System to find peer-reviewed research related to "
         "space biology, microgravity, radiation, human health, plants, and astrobiology."),
        ("Why It Matters",
         "Space biology research contains valuable insights about how spaceflight affects living organisms. "
         "BioOrbit makes this research easier to discover, explore, and understand by combining NASA ADS "
         "search with AI-powered summaries."),
        ("Built With",
         "Python · Streamlit · NASA ADS API · HuggingFace Transformers · BART-large-CNN · "
         "Pandas · JSON caching · Custom CSS"),
    ]:
        st.markdown(f"""
        <div class="panel" style="margin-bottom:14px;">
            <div class="sec-title">{title}</div>
            <div style="color:#64748b;font-size:13px;line-height:1.7;margin-top:10px;">{text}</div>
        </div>
        """, unsafe_allow_html=True)
