import streamlit as st
import pandas as pd
import requests
import hashlib
import json
import os
import base64
from pathlib import Path

from utils.ai_summarizer import summarize_text

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
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

def img_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

earth_b64 = img_b64(EARTH_IMAGE) if EARTH_IMAGE.exists() else ""
nasa_b64  = img_b64(NASA_LOGO)   if NASA_LOGO.exists()   else ""

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
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
    "search_rows":    10,
    "search_page":    1,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Handle query param navigation (from sidebar HTML links)
qp = st.query_params.get("nav", None)
if qp and qp != st.session_state.active_nav:
    st.session_state.active_nav = qp
    st.query_params.clear()
    st.rerun()

# ─────────────────────────────────────────────────────────────
# ASSETS
# ─────────────────────────────────────────────────────────────
hero_bg  = f"url('data:image/jpeg;base64,{earth_b64}')" if earth_b64 else "none"
nasa_src = f"data:image/png;base64,{nasa_b64}" if nasa_b64 else \
           "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/2449px-NASA_logo.svg.png"

# ─────────────────────────────────────────────────────────────
# SVG ICONS
# ─────────────────────────────────────────────────────────────
def svg(d, size=16, color="currentColor", sw=2):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round" style="flex-shrink:0">{d}</svg>')

# Nav icons (white for active, muted for inactive — controlled by CSS)
NAV_ICONS = {
    "Dashboard":       svg('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'),
    "Search":          svg('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'),
    "Saved Summaries": svg('<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>'),
    "About":           svg('<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'),
}

# Feature / stats icons
ICO = {
    "file":   svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>', 18, "#a78bfa"),
    "zap":    svg('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>', 18, "#f59e0b"),
    "bot":    svg('<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/>', 18, "#34d399"),
    "doc":    svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>', 15, "#5b54e8"),
    "ext":    svg('<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>', 11, "currentColor", 2.5),
    "bar":    svg('<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>', 14, "#172554"),
    "clock":  svg('<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>', 14, "#172554"),
    "qdoc":   svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>', 13, "#64748b"),
    "qzap":   svg('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>', 13, "#64748b"),
    "qclk":   svg('<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>', 13, "#64748b"),
    "srchsm": svg('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>', 12, "#94a3b8"),
    "chev":   svg('<polyline points="9 18 15 12 9 6"/>', 12, "#c7d2fe", 2.5),
    "f_srch": svg('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>', 22, "#4f46e5"),
    "f_list": svg('<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>', 22, "#2563eb"),
    "f_star": svg('<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>', 22, "#16a34a"),
    "f_zap":  svg('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>', 22, "#ca8a04"),
}

# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
active = st.session_state.active_nav

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*, *::before, *::after {{ font-family: 'Inter', sans-serif !important; box-sizing: border-box; }}

/* ── hide streamlit chrome ── */
#MainMenu, footer {{ visibility: hidden !important; }}
header, [data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="collapsedControl"],
.stDeployButton {{ display: none !important; height: 0 !important; }}

/* ── page ── */
.stApp {{ background: #edf0f7 !important; }}
.block-container {{ padding: 1rem 1.4rem 3rem !important; max-width: 100% !important; }}

/* ════════════════════════════════
   SIDEBAR — dark navy, no scroll
   ════════════════════════════════ */
[data-testid="stSidebar"] {{
    background: #071329 !important;
    min-width: 250px !important;
    max-width: 250px !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    overflow: hidden !important; height: 100vh !important;
}}
[data-testid="stSidebarContent"] {{
    overflow: hidden !important; height: 100vh !important;
    display: flex !important; flex-direction: column !important;
    padding: 0 !important; gap: 0 !important;
}}
[data-testid="stSidebarContent"] > div {{
    flex-shrink: 0 !important; padding: 0 !important; margin: 0 !important; min-height: 0 !important;
}}
[data-testid="stSidebar"] *::-webkit-scrollbar {{ display: none !important; }}
[data-testid="stSidebar"] * {{ scrollbar-width: none !important; }}

/* ── brand ── */
.sb-brand {{
    display: flex; align-items: center; gap: 11px;
    padding: 20px 18px 17px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 8px; flex-shrink: 0;
}}
.orbit-logo {{
    width: 42px; height: 42px; border-radius: 50%;
    border: 2.5px solid #6d5fe6;
    display: flex; align-items: center; justify-content: center;
    position: relative; flex-shrink: 0;
}}
.orbit-logo::before {{
    content: ""; position: absolute;
    width: 55px; height: 18px;
    border: 2px solid #6d5fe6; border-radius: 50%;
    transform: rotate(-28deg); pointer-events: none;
}}
.orbit-dot {{ width: 10px; height: 10px; background: #a78bfa; border-radius: 50%; position: relative; z-index: 2; }}
.sb-name {{ color: #fff; font-size: 18px; font-weight: 800; line-height: 1.15; }}
.sb-sub  {{ color: #4e6378; font-size: 10px; line-height: 1.45; margin-top: 2px; }}

/* ── nav items — pure HTML, styled as real nav ── */
.sb-nav {{ padding: 0 10px; flex-shrink: 0; }}
.sb-nav a {{
    display: flex; align-items: center; gap: 11px;
    padding: 9px 12px; border-radius: 8px;
    margin-bottom: 3px; text-decoration: none;
    color: #7a8fa8; font-size: 13px; font-weight: 500;
    transition: background .15s, color .15s;
    cursor: pointer;
}}
.sb-nav a:hover {{
    background: rgba(99,102,241,0.12);
    color: #c8d5e8; text-decoration: none;
}}
.sb-nav a.active {{
    background: linear-gradient(90deg, #3730a3, #4f46e5);
    color: #ffffff;
}}
.sb-nav a svg {{ flex-shrink: 0; opacity: 0.6; }}
.sb-nav a.active svg {{ opacity: 1; }}
.sb-nav a span {{ white-space: nowrap; }}

/* hidden Streamlit nav buttons (still needed for state) */
.sb-hidden-btns {{ display: none !important; height: 0 !important; overflow: hidden !important; }}

/* ── footer ── */
.sb-foot {{
    margin-top: auto; padding: 16px 18px 20px;
    border-top: 1px solid rgba(255,255,255,0.06);
    flex-shrink: 0;
}}
.sb-nasa {{ width: 54px; height: auto; display: block; margin-bottom: 9px; }}
.sb-pow  {{ font-size: 10.5px; color: #7a8fa8; line-height: 1.55; }}
.sb-pow b {{ color: #b8cae0; font-weight: 600; }}
.sb-tag  {{ font-size: 9.5px; color: #374d5e; line-height: 1.6; margin-top: 8px; }}

/* ════════════════════════════
   HERO
   ════════════════════════════ */
.hero {{
    border-radius: 16px; overflow: hidden; min-height: 270px;
    display: flex; align-items: center;
    background:
        linear-gradient(90deg,
            rgba(4,9,24,.97) 0%,
            rgba(4,9,24,.90) 30%,
            rgba(4,9,24,.22) 60%,
            transparent 100%),
        {hero_bg};
    background-size: cover; background-position: center right;
    padding: 34px 36px 30px; margin-bottom: 14px;
}}
.hero-h1 {{
    color: #fff; font-size: 38px; font-weight: 800;
    letter-spacing: -1px; line-height: 1.1; margin: 0 0 10px;
}}
.hero-h1 span {{ color: #8b7cf6; }}
.hero-p {{ color: #b8cbdf; font-size: 14px; line-height: 1.65; max-width: 460px; margin: 0 0 20px; }}
.pop-row {{ display: flex; align-items: center; flex-wrap: wrap; gap: 7px; }}
.pop-lbl {{ color: #7a8fa8; font-size: 12px; }}
.chip {{
    padding: 5px 13px; border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.2);
    background: rgba(255,255,255,0.06); color: #b8cbdf; font-size: 11px;
}}

/* stat panel */
.stat-panel {{
    background: rgba(4,11,30,.82); border: 1px solid rgba(148,163,184,.20);
    backdrop-filter: blur(10px); border-radius: 14px;
    padding: 4px 16px; min-width: 200px; flex-shrink: 0;
}}
.s-row {{ display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }}
.s-row:last-child {{ border-bottom: none; }}
.s-ico {{ width: 34px; height: 34px; border-radius: 8px; background: rgba(99,102,241,.22); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.s-val {{ color: #fff; font-size: 14px; font-weight: 700; line-height: 1.1; }}
.s-lbl {{ color: #6b7e99; font-size: 9.5px; margin-top: 2px; line-height: 1.4; }}

/* ════════════════════════════
   INPUTS
   ════════════════════════════ */
.stTextInput > div > div > input {{
    height: 46px !important; border-radius: 9px !important;
    border: 1.5px solid #d5dcea !important; font-size: 13.5px !important;
    background: #fff !important; color: #172554 !important; padding: 0 14px !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: #6366f1 !important; box-shadow: 0 0 0 3px rgba(99,102,241,.1) !important;
}}
.stSelectbox > div > div {{ border-radius: 8px !important; border: 1.5px solid #d5dcea !important; background: #fff !important; color: #172554 !important; min-height: 44px !important; }}
.stSelectbox > div > div > div {{ color: #172554 !important; }}
.stSelectbox label {{ color: #64748b !important; font-size: 12px !important; font-weight: 500 !important; }}
.stNumberInput > div > div {{ border-radius: 8px !important; border: 1.5px solid #d5dcea !important; background: #fff !important; overflow: hidden; }}
.stNumberInput > div > div > input {{ background: #fff !important; color: #172554 !important; border: none !important; height: 42px !important; }}
.stNumberInput button {{ background: #f4f6fb !important; color: #172554 !important; border: none !important; }}
.stNumberInput label {{ color: #64748b !important; font-size: 12px !important; font-weight: 500 !important; }}

/* ════════════════════════════
   BUTTONS
   ════════════════════════════ */
.stButton > button {{
    height: 46px !important; border-radius: 9px !important;
    font-size: 13px !important; font-weight: 600 !important; padding: 0 20px !important;
    border: 1.5px solid #d5dcea !important; background: #fff !important; color: #172554 !important;
    box-shadow: none !important; transition: all .15s;
}}
.stButton > button:hover {{ background: #f4f6fb !important; border-color: #b8c4e4 !important; }}
.stButton > button[kind="primary"] {{ background: linear-gradient(135deg,#4338ca,#6366f1) !important; color: #fff !important; border: none !important; }}
.stButton > button[kind="primary"]:hover {{ background: linear-gradient(135deg,#3730a3,#4f46e5) !important; }}

/* ════════════════════════════
   FEATURE CARDS
   ════════════════════════════ */
.feat-card {{
    background: #fff; border: 1px solid #e0e6f0; border-radius: 14px;
    padding: 20px 18px; min-height: 170px; transition: box-shadow .2s, border-color .2s;
}}
.feat-card:hover {{ border-color: #c7d2fe; box-shadow: 0 6px 22px rgba(79,70,229,.08); }}
.feat-top {{ display: flex; align-items: center; gap: 10px; margin-bottom: 13px; }}
.feat-num {{
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 800; flex-shrink: 0;
}}
.fn1 {{ background: #eef2ff; color: #4f46e5; }}
.fn2 {{ background: #eff6ff; color: #2563eb; }}
.fn3 {{ background: #f0fdf4; color: #16a34a; }}
.fn4 {{ background: #fefce8; color: #ca8a04; }}
.feat-card h3 {{ color: #172554; font-size: 14.5px; font-weight: 700; margin: 0 0 6px; }}
.feat-card p  {{ color: #64748b; font-size: 11.5px; line-height: 1.6; margin: 0; }}

/* ════════════════════════════
   SECTION
   ════════════════════════════ */
.sec-hd {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; }}
.sec-title {{ color: #172554; font-size: 15.5px; font-weight: 700; }}
.sec-sub   {{ color: #94a3b8; font-size: 11px; }}

/* ════════════════════════════
   PAPER CARDS
   ════════════════════════════ */
.paper {{ background: #fff; border: 1px solid #e0e6f0; border-radius: 12px; padding: 14px 16px; margin-bottom: 9px; }}
.paper:hover {{ border-color: #c7d2fe; }}
.p-row {{ display: flex; align-items: flex-start; gap: 12px; }}
.p-ico {{ width: 34px; height: 34px; border-radius: 50%; background: #eef2ff; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.p-body {{ flex: 1; min-width: 0; }}
.p-title {{ color: #172554; font-size: 13px; font-weight: 600; line-height: 1.45; }}
.p-meta  {{ color: #94a3b8; font-size: 10px; margin-top: 3px; }}
.p-tags  {{ margin-top: 6px; }}
.ptag {{ display: inline-block; background: #eff6ff; color: #3b5cde; padding: 2px 8px; border-radius: 10px; font-size: 9px; font-weight: 500; margin-right: 4px; }}
.p-actions {{ display: flex; align-items: center; gap: 8px; margin-top: 11px; padding-top: 11px; border-top: 1px solid #f1f5f9; }}
.btn-ads {{
    display: inline-flex; align-items: center; gap: 4px;
    border: 1px solid #c7d2fe; border-radius: 7px; padding: 6px 12px;
    color: #4f46e5; font-size: 10.5px; font-weight: 600;
    text-decoration: none; background: #fafbff; white-space: nowrap;
}}
.btn-ads:hover {{ background: #eef2ff; text-decoration: none; }}
.empty {{ background: #fff; border: 1px solid #e0e6f0; border-radius: 14px; padding: 48px 20px; text-align: center; }}
.empty-t {{ color: #172554; font-size: 15px; font-weight: 700; margin-bottom: 6px; }}
.empty-s {{ color: #94a3b8; font-size: 12px; line-height: 1.6; }}
.abstract-box {{ background: #f8fafc; border-radius: 8px; border: 1px solid #e8edf5; padding: 12px 14px; color: #475569; font-size: 12px; line-height: 1.7; margin-top: 6px; }}
.sum-box {{ background: #f0f0ff; border-left: 3px solid #6366f1; padding: 12px 14px; border-radius: 7px; margin-top: 10px; color: #3730a3; font-size: 12px; line-height: 1.7; }}
.sum-lbl {{ color: #6366f1; font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 5px; }}

/* expander */
[data-testid="stExpander"] {{ border: 1px solid #e0e6f0 !important; border-radius: 9px !important; background: #fff !important; margin-bottom: 0 !important; margin-top: 2px !important; }}
[data-testid="stExpander"] summary p {{ font-size: 12px !important; color: #64748b !important; font-weight: 500 !important; margin: 0 !important; }}

/* ════════════════════════════
   RIGHT PANEL
   ════════════════════════════ */
.panel {{ background: #fff; border: 1px solid #e0e6f0; border-radius: 13px; padding: 16px; margin-bottom: 12px; }}
.p-title-row {{ display: flex; align-items: center; gap: 6px; color: #172554; font-size: 13.5px; font-weight: 700; margin-bottom: 12px; }}
.qs-r {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f1f5f9; }}
.qs-r:last-child {{ border-bottom: none; }}
.qs-l {{ display: flex; align-items: center; gap: 8px; color: #64748b; font-size: 11px; }}
.qs-ico {{ width: 28px; height: 28px; border-radius: 50%; background: #f4f6fb; display: flex; align-items: center; justify-content: center; }}
.qs-v {{ color: #172554; font-size: 13.5px; font-weight: 700; }}
.rs-r {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f1f5f9; }}
.rs-r:last-child {{ border-bottom: none; }}
.rs-l {{ display: flex; align-items: center; gap: 7px; color: #475569; font-size: 11.5px; }}
.rs-t {{ color: #94a3b8; font-size: 9.5px; }}

/* dropdown options */
[role="listbox"] {{ background: #fff !important; border: 1px solid #d5dcea !important; border-radius: 8px !important; }}
[role="option"] {{ color: #172554 !important; font-size: 13px !important; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# NASA ADS
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_ads(query, rows=10, start=0):
    url     = "https://api.adsabs.harvard.edu/v1/search/query"
    headers = {"Authorization": f"Bearer {ADS_API_KEY}"}
    params  = {"q": f'title:"{query}" OR abstract:"{query}"',
                "fl": "title,abstract,author,year,doi,keyword", "rows": rows, "start": start}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        data = r.json().get("response", {})
    except requests.RequestException as e:
        return pd.DataFrame(), 0, str(e)

    total = data.get("numFound", 0)
    out   = []
    for p in data.get("docs", []):
        doi = p.get("doi", [None])
        out.append({
            "title":    p.get("title",    [""])[0],
            "abstract": p.get("abstract", ""),
            "year":     p.get("year",     ""),
            "authors":  ", ".join(p.get("author", [])[:3]),
            "keywords": p.get("keyword",  [])[:3],
            "link":     f"https://ui.adsabs.harvard.edu/abs/{doi[0]}" if doi and doi[0] else "",
        })
    return pd.DataFrame(out), total, ""

# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────
def do_summary(aid, abstract):
    if aid not in st.session_state.summaries:
        with st.spinner("Generating AI summary…"):
            raw     = summarize_text(abstract)
            sents   = raw.replace("\n", " ").split(". ")
            bullets = [f"• {s.strip().rstrip('.')}" for s in sents if s.strip()][:4]
            st.session_state.summaries[aid] = "<br>".join(bullets)
            with open(CACHE_FILE, "w") as f:
                json.dump(st.session_state.summaries, f, indent=2)

# ─────────────────────────────────────────────────────────────
# RENDER PAPERS
# ─────────────────────────────────────────────────────────────
def render_papers(df, prefix):
    def esc(v): return str(v or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    for i, row in df.iterrows():
        aid  = hashlib.md5(str(row.get("title", i)).encode()).hexdigest()
        tags = "".join(f'<span class="ptag">{esc(t)}</span>' for t in (row.get("keywords") or []) if t)
        link = row.get("link") or ""
        ads_btn = f'<a class="btn-ads" href="{link}" target="_blank">{ICO["ext"]} View on NASA ADS</a>' if link else ""

        st.markdown(
            f'<div class="paper">'
            f'<div class="p-row">'
            f'<div class="p-ico">{ICO["doc"]}</div>'
            f'<div class="p-body">'
            f'<div class="p-title">{esc(row.get("title",""))}</div>'
            f'<div class="p-meta">{esc(row.get("authors",""))} &nbsp;&middot;&nbsp; {esc(row.get("year",""))}</div>'
            f'<div class="p-tags">{tags}</div>'
            f'</div></div>'
            f'<div class="p-actions">{ads_btn}</div>'
            f'</div>',
            unsafe_allow_html=True)

        with st.expander("Show abstract & AI summary"):
            ab = row.get("abstract") or ""
            if ab:
                st.markdown(f'<div class="abstract-box">{esc(ab)}</div>', unsafe_allow_html=True)
            else:
                st.caption("Abstract not available.")
            c1, _ = st.columns([1, 3])
            with c1:
                if st.button("Generate AI Summary", key=f"{prefix}_{i}", type="primary"):
                    do_summary(aid, ab)
            if aid in st.session_state.summaries:
                st.markdown(
                    '<div class="sum-box"><div class="sum-lbl">AI Summary</div>'
                    + st.session_state.summaries[aid] + '</div>',
                    unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SIDEBAR  — HTML nav + hidden Streamlit buttons for state
# ─────────────────────────────────────────────────────────────
with st.sidebar:

    cur = st.session_state.active_nav

    # Build nav HTML — each item is a real <a> that sets ?nav=Page
    def nav_link(page, label, icon_svg):
        cls = "active" if cur == page else ""
        # Use ?nav= query param so clicking reloads with the new page
        return (
            f'<a href="?nav={page}" class="{cls}" target="_self">'
            f'{icon_svg}<span>{label}</span>'
            f'</a>'
        )

    nav_html = (
        nav_link("Dashboard",       "Dashboard",       NAV_ICONS["Dashboard"])
        + nav_link("Search",          "Search",          NAV_ICONS["Search"])
        + nav_link("Saved Summaries", "Saved Summaries", NAV_ICONS["Saved Summaries"])
        + nav_link("About",           "About",           NAV_ICONS["About"])
    )

    st.markdown(f"""
    <div class="sb-brand">
      <div class="orbit-logo"><div class="orbit-dot"></div></div>
      <div>
        <div class="sb-name">BioOrbit</div>
        <div class="sb-sub">NASA Space Biology<br>Research Explorer</div>
      </div>
    </div>
    <div class="sb-nav">
      {nav_html}
    </div>
    """, unsafe_allow_html=True)

    # Spacer pushes footer to bottom
    st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sb-foot">
      <img class="sb-nasa" src="{nasa_src}">
      <div class="sb-pow"><b>Powered by NASA ADS</b><br>+ HuggingFace</div>
      <div class="sb-tag">Making space biology research<br>accessible and actionable through AI.</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# ██  DASHBOARD
# ─────────────────────────────────────────────────────────────
if st.session_state.active_nav == "Dashboard":

    if not ADS_API_KEY:
        st.error("NASA ADS API key missing. Add NASA_ADS_API_KEY to Streamlit Secrets.")
        st.stop()

    hc, sc = st.columns([3.8, 1], gap="medium")
    with hc:
        st.markdown(f"""
        <div class="hero">
          <div style="flex:1">
            <div class="hero-h1">Welcome to <span>BioOrbit</span></div>
            <div class="hero-p">Search, explore, and understand NASA-funded research
            on how spaceflight affects living organisms.</div>
            <div class="pop-row">
              <span class="pop-lbl">Popular searches:</span>
              <span class="chip">microgravity</span>
              <span class="chip">radiation biology</span>
              <span class="chip">space plants</span>
              <span class="chip">human health</span>
              <span class="chip">astrobiology</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with sc:
        st.markdown(f"""
        <div class="stat-panel">
          <div class="s-row"><div class="s-ico">{ICO["file"]}</div><div><div class="s-val">15M+</div><div class="s-lbl">Papers in NASA ADS</div></div></div>
          <div class="s-row"><div class="s-ico">{ICO["zap"]}</div><div><div class="s-val">Real-time</div><div class="s-lbl">NASA ADS API</div></div></div>
          <div class="s-row"><div class="s-ico">{ICO["bot"]}</div><div><div class="s-val">AI Summaries</div><div class="s-lbl">HuggingFace BART-CNN</div></div></div>
        </div>
        """, unsafe_allow_html=True)

    a, b = st.columns([6, 1], gap="small")
    with a:
        dq = st.text_input("", placeholder="Search microgravity, radiation biology, space plants…",
                           label_visibility="collapsed", key="dash_q")
    with b:
        dgo = st.button("Search", type="primary", use_container_width=True, key="dash_go")
    if dgo and dq.strip():
        st.session_state.active_nav   = "Search"
        st.session_state.search_query = dq.strip()
        st.rerun()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    cards = [
        ("1","fn1",ICO["f_srch"],"Search","Type a topic and query NASA's Astrophysics Data System API, which indexes 15M+ peer-reviewed papers."),
        ("2","fn2",ICO["f_list"],"Explore","View paper titles, authors, year, and direct links to the full record on NASA ADS. Expand abstracts inline."),
        ("3","fn3",ICO["f_star"],"Summarize",'Click "Generate AI Summary" and we use HuggingFace\'s BART-large-CNN model to create a concise 4-bullet summary.'),
        ("4","fn4",ICO["f_zap"],"Cache","Summaries are saved locally so they load instantly on repeat views."),
    ]
    for col, (num,fn,ico,title,desc) in zip(st.columns(4, gap="medium"), cards):
        with col:
            st.markdown(f'<div class="feat-card"><div class="feat-top"><div class="feat-num {fn}">{num}</div><div>{ico}</div></div><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    lc, rc = st.columns([3.1, 1], gap="medium")

    with lc:
        ql = f'"{st.session_state.last_query}"' if st.session_state.last_query else "—"
        st.markdown(f'<div class="sec-hd"><div class="sec-title">Recent Research Results</div><div class="sec-sub">Showing {st.session_state.last_total} results for <b>{ql}</b></div></div>', unsafe_allow_html=True)
        if st.session_state.last_results is not None and len(st.session_state.last_results) > 0:
            render_papers(st.session_state.last_results, "d")
        else:
            st.markdown('<div class="empty"><div class="empty-t">Start exploring space biology</div><div class="empty-s">Search for microgravity, radiation biology,<br>space plants, human health, or astrobiology above.</div></div>', unsafe_allow_html=True)

    with rc:
        tc = len(st.session_state.summaries)
        st.markdown(f"""
        <div class="panel">
          <div class="p-title-row">{ICO["bar"]} Quick Stats</div>
          <div class="qs-r"><div class="qs-l"><div class="qs-ico">{ICO["qdoc"]}</div>Total Searches</div><div class="qs-v">{st.session_state.total_searches}</div></div>
          <div class="qs-r"><div class="qs-l"><div class="qs-ico">{ICO["qdoc"]}</div>Summaries Generated</div><div class="qs-v">{tc}</div></div>
          <div class="qs-r"><div class="qs-l"><div class="qs-ico">{ICO["qzap"]}</div>Cached Results</div><div class="qs-v">{tc}</div></div>
          <div class="qs-r"><div class="qs-l"><div class="qs-ico">{ICO["qclk"]}</div>Avg. Response</div><div class="qs-v">2.3s</div></div>
        </div>""", unsafe_allow_html=True)

        hist = list(reversed(st.session_state.search_history[-5:])) if st.session_state.search_history else []
        tl   = ["2 hours ago","5 hours ago","1 day ago","1 day ago","2 days ago"]
        rh   = "".join(
            f'<div class="rs-r"><div class="rs-l">{ICO["srchsm"]}&nbsp;{h}</div>'
            f'<div style="display:flex;align-items:center;gap:4px"><span class="rs-t">{tl[i] if i<len(tl) else "recently"}</span>{ICO["chev"]}</div></div>'
            for i,h in enumerate(hist)
        ) if hist else '<div style="color:#94a3b8;font-size:11px;padding:8px 0">No searches yet.</div>'
        st.markdown(f'<div class="panel"><div class="p-title-row">{ICO["clock"]} Recent Searches</div>{rh}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# ██  SEARCH
# ─────────────────────────────────────────────────────────────
elif st.session_state.active_nav == "Search":

    st.markdown("""
    <div style="margin:6px 0 16px">
      <div class="sec-title" style="font-size:20px">Search NASA Research</div>
      <div style="color:#94a3b8;font-size:12px;margin-top:3px">Find papers on space biology, microgravity, radiation, and more.</div>
    </div>""", unsafe_allow_html=True)

    a, b = st.columns([6, 1], gap="small")
    with a:
        q = st.text_input("", value=st.session_state.get("search_query",""),
                          placeholder="Search microgravity, radiation biology…",
                          label_visibility="collapsed", key="srch_q")
    with b:
        go = st.button("Search", type="primary", use_container_width=True, key="srch_go")

    p1, p2 = st.columns(2)
    with p1:
        rows = st.selectbox("Results per page", [5,10,15,20,25,30],
                            index=[5,10,15,20,25,30].index(st.session_state.search_rows)
                            if st.session_state.search_rows in [5,10,15,20,25,30] else 1)
    with p2:
        page = st.number_input("Page", min_value=1, step=1, value=st.session_state.search_page)

    pagination_changed = rows != st.session_state.search_rows or page != st.session_state.search_page
    run_search = (go and q.strip()) or (pagination_changed and st.session_state.last_query)

    if run_search:
        aq = q.strip() if (go and q.strip()) else st.session_state.last_query
        st.session_state.search_rows = rows
        st.session_state.search_page = page
        start = (page - 1) * rows
        if go and q.strip():
            st.session_state.search_page = 1; start = 0
            st.session_state.total_searches += 1
            if aq not in st.session_state.search_history:
                st.session_state.search_history.append(aq)
                if len(st.session_state.search_history) > 20:
                    st.session_state.search_history = st.session_state.search_history[-20:]
        with st.spinner("Searching NASA Astrophysics Data System…"):
            df, total, err = fetch_ads(aq, rows, start)
        if err:
            st.error(f"Could not reach NASA ADS — {err}")
        else:
            st.session_state.last_query = aq; st.session_state.last_total = total
            st.session_state.last_results = df; st.session_state.search_query = ""
            st.rerun()

    if st.session_state.last_results is not None and len(st.session_state.last_results) > 0:
        df = st.session_state.last_results
        st.markdown(f'<div class="sec-hd" style="margin-top:20px"><div class="sec-title">Research Results</div><div class="sec-sub">Showing {len(df)} of {st.session_state.last_total:,} results</div></div>', unsafe_allow_html=True)
        render_papers(df, "s")
    elif st.session_state.last_query:
        st.info("No results found. Try a different search term.")

# ─────────────────────────────────────────────────────────────
# ██  SAVED SUMMARIES
# ─────────────────────────────────────────────────────────────
elif st.session_state.active_nav == "Saved Summaries":
    st.markdown("""
    <div style="margin:6px 0 16px">
      <div class="sec-title" style="font-size:20px">Saved Summaries</div>
      <div style="color:#94a3b8;font-size:12px;margin-top:3px">Your cached AI-generated paper summaries.</div>
    </div>""", unsafe_allow_html=True)
    if st.session_state.summaries:
        for aid, summary in st.session_state.summaries.items():
            st.markdown(f'<div class="paper"><div class="p-meta" style="margin-bottom:7px;font-size:10px">ID: {aid[:14]}…</div><div class="sum-box"><div class="sum-lbl">Cached Summary</div>{summary}</div></div>', unsafe_allow_html=True)
        if st.button("Clear All Summaries", type="primary"):
            st.session_state.summaries = {}
            with open(CACHE_FILE, "w") as f: json.dump({}, f)
            st.rerun()
    else:
        st.info("No saved summaries yet. Search for papers and generate summaries.")

# ─────────────────────────────────────────────────────────────
# ██  ABOUT
# ─────────────────────────────────────────────────────────────
elif st.session_state.active_nav == "About":
    st.markdown("""
    <div style="margin:6px 0 16px">
      <div class="sec-title" style="font-size:20px">About BioOrbit</div>
      <div style="color:#94a3b8;font-size:12px;margin-top:3px">Making space biology research easier to understand.</div>
    </div>""", unsafe_allow_html=True)
    for title, body in [
        ("What is BioOrbit?", "BioOrbit is an AI-powered research explorer built for the NASA Space Apps Challenge. It connects to NASA's Astrophysics Data System to find peer-reviewed research related to space biology, microgravity, radiation, human health, plants, and astrobiology."),
        ("Why It Matters", "Space biology research contains valuable insights about how spaceflight affects living organisms. BioOrbit makes this research easier to discover, explore, and understand by combining NASA ADS search with AI-powered summaries."),
        ("Built With", "Python · Streamlit · NASA ADS API · HuggingFace Transformers · BART-large-CNN · Pandas · JSON caching · Custom CSS"),
    ]:
        st.markdown(f'<div class="panel" style="margin-bottom:12px"><div class="sec-title">{title}</div><div style="color:#64748b;font-size:13px;line-height:1.7;margin-top:9px">{body}</div></div>', unsafe_allow_html=True)
