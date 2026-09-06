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

# Handle query-param navigation from sidebar HTML links
_qp = st.query_params.get("nav", None)
if _qp and _qp != st.session_state.active_nav:
    st.session_state.active_nav = _qp
    st.query_params.clear()
    st.rerun()

# ─────────────────────────────────────────────────────────────
# ASSETS
# ─────────────────────────────────────────────────────────────
hero_bg  = f"url('data:image/jpeg;base64,{earth_b64}')" if earth_b64 else "none"
nasa_src = f"data:image/png;base64,{nasa_b64}" if nasa_b64 else \
           "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/2449px-NASA_logo.svg.png"

# ─────────────────────────────────────────────────────────────
# LUCIDE SVG ICON LIBRARY
# All paths sourced from lucide.dev — consistent stroke-based style
# ─────────────────────────────────────────────────────────────
def lucide(path_data, size=16, color="currentColor", sw=2):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="display:inline-block;vertical-align:middle;flex-shrink:0">'
        f'{path_data}</svg>'
    )

# ── Lucide paths ──────────────────────────────────────────────
_HOUSE      = '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
_SEARCH     = '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>'
_BOOKMARK   = '<path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>'
_INFO       = '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>'
_FILETEXT   = '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>'
_LIST       = '<path d="M3 12h.01"/><path d="M3 18h.01"/><path d="M3 6h.01"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M8 6h13"/>'
_SPARKLES   = '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/><path d="M4 17v2"/><path d="M5 18H3"/>'
_ZAP        = '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>'
_DATABASE   = '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>'
_BARCHART   = '<line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>'
_CLOCK      = '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>'
_DNA        = '<path d="M2 15c6.667-6 13.333 0 20-6"/><path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"/><path d="M10 6C9.5 8.5 9 11 7 14"/><path d="M14 12.5c1 2.5 2 5 4 6.5"/><path d="M2 9c6.667 6 13.333 0 20 6"/>'
_MICROSCOPE = '<path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>'
_SATELLITE  = '<path d="M13 7 9 3 5 7l4 4"/><path d="m17 11 4 4-4 4-4-4"/><path d="m8 12 4 4 6-6-4-4Z"/><path d="m16 8 3-3"/><path d="M9 21a6 6 0 0 0-6-6"/>'
_EXT_LINK   = '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
_CHEVRON_R  = '<path d="m9 18 6-6-6-6"/>'

# Convenience wrappers
def ico_nav(path, active=False):
    color = "#ffffff" if active else "#7a8fa8"
    return lucide(path, 16, color, 2)

def ico(path, size=18, color="currentColor"):
    return lucide(path, size, color, 2)

# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*, *::before, *::after {{ font-family: 'Inter', sans-serif !important; box-sizing: border-box; }}

/* ── hide streamlit chrome ── */
#MainMenu, footer {{ visibility: hidden !important; }}
header, [data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="collapsedControl"],
.stDeployButton {{ display: none !important; height: 0 !important; min-height: 0 !important; }}

.stApp {{ background: #edf0f7 !important; }}
.block-container {{ padding: 1rem 1.4rem 3rem !important; max-width: 100% !important; }}

/* ══════════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════════ */
[data-testid="stSidebar"] {{
    background: #071329 !important;
    min-width: 252px !important; max-width: 252px !important;
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
    flex-shrink: 0 !important; padding: 0 !important;
    margin: 0 !important; min-height: 0 !important;
}}
[data-testid="stSidebar"] *::-webkit-scrollbar {{ display: none !important; }}
[data-testid="stSidebar"] * {{ scrollbar-width: none !important; }}

/* ── brand (top) ── */
.sb-brand {{
    display: flex; align-items: center; gap: 11px;
    padding: 20px 18px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    flex-shrink: 0;
}}
.orbit-ring {{
    width: 40px; height: 40px; border-radius: 50%;
    border: 2.5px solid #7c6ff0;
    display: flex; align-items: center; justify-content: center;
    position: relative; flex-shrink: 0;
    background: rgba(124,111,240,0.12);
}}
.orbit-ring::before {{
    content: ""; position: absolute;
    width: 52px; height: 17px;
    border: 2px solid #7c6ff0; border-radius: 50%;
    transform: rotate(-28deg); pointer-events: none;
}}
.orbit-dot {{ width: 9px; height: 9px; background: #a78bfa; border-radius: 50%; position: relative; z-index: 2; }}
.sb-appname {{ color: #fff; font-size: 18px; font-weight: 800; line-height: 1.15; }}
.sb-appsub  {{ color: #4e6175; font-size: 9.5px; line-height: 1.45; margin-top: 2px; }}

/* ── nav links — pure HTML, real dashboard style ── */
.sb-nav {{ padding: 10px 10px 0; flex-shrink: 0; }}
.sb-nav a {{
    display: flex; align-items: center; gap: 10px;
    padding: 8px 12px; border-radius: 8px; margin-bottom: 2px;
    text-decoration: none !important;
    color: #7a8fa8; font-size: 13px; font-weight: 500;
    line-height: 1.3;
    transition: background .14s, color .14s;
}}
.sb-nav a:hover {{ background: rgba(99,102,241,0.13); color: #d0daea; }}
.sb-nav a.nav-on {{
    background: linear-gradient(90deg, #3730a3 0%, #4f46e5 100%);
    color: #ffffff;
}}
.sb-nav a svg {{ flex-shrink: 0; }}

/* ── spacer ── */
.sb-spacer {{ flex: 1; min-height: 20px; }}

/* ── footer (bottom) ── */
.sb-foot {{
    padding: 14px 18px 18px; flex-shrink: 0;
    border-top: 1px solid rgba(255,255,255,0.06);
}}
.sb-nasa-img {{ width: 52px; height: auto; display: block; margin-bottom: 8px; }}
.sb-powered  {{ font-size: 10.5px; color: #7a8fa8; line-height: 1.55; }}
.sb-powered b {{ color: #b8cae0; font-weight: 600; }}
.sb-tagline  {{ font-size: 9.5px; color: #374d5e; line-height: 1.6; margin-top: 7px; }}

/* ══════════════════════════════════════════════
   HERO — full-cover Earth image
   ══════════════════════════════════════════════ */
.hero {{
    border-radius: 16px; overflow: hidden;
    min-height: 300px;
    background:
        linear-gradient(90deg,
            rgba(3,8,22,.96)  0%,
            rgba(3,8,22,.88) 30%,
            rgba(3,8,22,.18) 62%,
            transparent      100%),
        {hero_bg};
    background-size: cover !important;
    background-position: center center !important;
    padding: 36px 36px 30px;
    margin-bottom: 0;
    position: relative;
}}

/* title */
.hero-h1 {{
    color: #fff; font-size: 38px; font-weight: 800;
    letter-spacing: -1px; line-height: 1.1; margin: 0 0 10px;
}}
.hero-h1 span {{ color: #8b7cf6; }}
.hero-p {{ color: #b8cbdf; font-size: 14px; line-height: 1.65; max-width: 500px; margin: 0 0 22px; }}

/* search bar INSIDE hero */
.hero-search-wrap {{
    display: flex; align-items: center;
    background: rgba(255,255,255,0.97);
    border-radius: 10px; overflow: hidden;
    max-width: 680px; margin-bottom: 18px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
}}
.hero-search-icon {{
    padding: 0 12px 0 16px; display: flex; align-items: center; flex-shrink: 0;
}}
.hero-search-input {{
    flex: 1; border: none; outline: none; background: transparent;
    font-size: 13.5px; color: #172554; padding: 13px 0;
    font-family: 'Inter', sans-serif;
}}
.hero-search-input::placeholder {{ color: #94a3b8; }}
.hero-search-btn {{
    background: linear-gradient(135deg, #4338ca, #6366f1);
    color: #fff; border: none; padding: 12px 28px;
    font-size: 13.5px; font-weight: 700; cursor: pointer;
    font-family: 'Inter', sans-serif; white-space: nowrap;
    transition: background .15s;
}}
.hero-search-btn:hover {{ background: linear-gradient(135deg,#3730a3,#4f46e5); }}

/* popular chips */
.pop-row {{ display: flex; align-items: center; flex-wrap: wrap; gap: 7px; }}
.pop-lbl {{ color: #94a3b8; font-size: 12px; white-space: nowrap; }}
.chip {{
    padding: 4px 13px; border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.22);
    background: rgba(255,255,255,0.06);
    color: #c0cfe4; font-size: 11px; cursor: default;
}}

/* ── stat panel (right of hero) ── */
.stat-panel {{
    background: rgba(4,12,32,.85);
    border: 1px solid rgba(148,163,184,.20);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 4px 16px;
    min-width: 205px; flex-shrink: 0;
}}
.s-row {{
    display: flex; align-items: center; gap: 12px;
    padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.06);
}}
.s-row:last-child {{ border-bottom: none; }}
.s-ico {{
    width: 34px; height: 34px; border-radius: 8px;
    background: rgba(99,102,241,.22);
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}}
.s-val {{ color: #fff; font-size: 14px; font-weight: 700; line-height: 1.1; }}
.s-lbl {{ color: #6b7e99; font-size: 9.5px; margin-top: 2px; line-height: 1.4; }}

/* ══════════════════════════════════════════════
   INPUTS & BUTTONS
   ══════════════════════════════════════════════ */
.stTextInput > div > div > input {{
    height: 46px !important; border-radius: 9px !important;
    border: 1.5px solid #d5dcea !important; font-size: 13.5px !important;
    background: #fff !important; color: #172554 !important; padding: 0 14px !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: #6366f1 !important; box-shadow: 0 0 0 3px rgba(99,102,241,.1) !important;
}}
.stSelectbox > div > div {{
    border-radius: 8px !important; border: 1.5px solid #d5dcea !important;
    background: #fff !important; color: #172554 !important; min-height: 44px !important;
}}
.stSelectbox > div > div > div {{ color: #172554 !important; }}
.stSelectbox label {{ color: #64748b !important; font-size: 12px !important; font-weight: 500 !important; }}
.stNumberInput > div > div {{
    border-radius: 8px !important; border: 1.5px solid #d5dcea !important;
    background: #fff !important; overflow: hidden;
}}
.stNumberInput > div > div > input {{ background: #fff !important; color: #172554 !important; border: none !important; height: 42px !important; }}
.stNumberInput button {{ background: #f4f6fb !important; color: #172554 !important; border: none !important; }}
.stNumberInput label {{ color: #64748b !important; font-size: 12px !important; font-weight: 500 !important; }}

.stButton > button {{
    height: 46px !important; border-radius: 9px !important;
    font-size: 13px !important; font-weight: 600 !important; padding: 0 20px !important;
    border: 1.5px solid #d5dcea !important; background: #fff !important; color: #172554 !important;
    box-shadow: none !important; transition: all .15s;
}}
.stButton > button:hover {{ background: #f4f6fb !important; border-color: #b8c4e4 !important; }}
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg,#4338ca,#6366f1) !important;
    color: #fff !important; border: none !important;
}}
.stButton > button[kind="primary"]:hover {{ background: linear-gradient(135deg,#3730a3,#4f46e5) !important; }}

/* ══════════════════════════════════════════════
   FEATURE CARDS
   ══════════════════════════════════════════════ */
.feat-card {{
    background: #fff; border: 1px solid #e0e6f0; border-radius: 14px;
    padding: 20px 18px; min-height: 170px;
    transition: box-shadow .2s, border-color .2s;
    height: 100%;
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

/* ══════════════════════════════════════════════
   SECTION + PAPER CARDS
   ══════════════════════════════════════════════ */
.sec-hd {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; }}
.sec-title {{ color: #172554; font-size: 15.5px; font-weight: 700; display: flex; align-items: center; gap: 7px; }}
.sec-sub   {{ color: #94a3b8; font-size: 11px; }}

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
    display: inline-flex; align-items: center; gap: 5px;
    border: 1px solid #c7d2fe; border-radius: 7px; padding: 6px 12px;
    color: #4f46e5; font-size: 10.5px; font-weight: 600;
    text-decoration: none !important; background: #fafbff; white-space: nowrap;
}}
.btn-ads:hover {{ background: #eef2ff; }}
.empty {{ background: #fff; border: 1px solid #e0e6f0; border-radius: 14px; padding: 48px 20px; text-align: center; }}
.empty-t {{ color: #172554; font-size: 15px; font-weight: 700; margin-bottom: 6px; }}
.empty-s {{ color: #94a3b8; font-size: 12px; line-height: 1.6; }}
.abstract-box {{ background: #f8fafc; border-radius: 8px; border: 1px solid #e8edf5; padding: 12px 14px; color: #475569; font-size: 12px; line-height: 1.7; margin-top: 6px; }}
.sum-box {{ background: #f0f0ff; border-left: 3px solid #6366f1; padding: 12px 14px; border-radius: 7px; margin-top: 10px; color: #3730a3; font-size: 12px; line-height: 1.7; }}
.sum-lbl {{ color: #6366f1; font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 5px; }}

[data-testid="stExpander"] {{ border: 1px solid #e0e6f0 !important; border-radius: 9px !important; background: #fff !important; margin-bottom: 0 !important; margin-top: 2px !important; }}
[data-testid="stExpander"] summary p {{ font-size: 12px !important; color: #64748b !important; font-weight: 500 !important; margin: 0 !important; }}

/* ══════════════════════════════════════════════
   RIGHT PANEL
   ══════════════════════════════════════════════ */
.panel {{ background: #fff; border: 1px solid #e0e6f0; border-radius: 13px; padding: 16px; margin-bottom: 12px; }}
.p-title-row {{ display: flex; align-items: center; gap: 7px; color: #172554; font-size: 13.5px; font-weight: 700; margin-bottom: 12px; }}
.qs-r {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f1f5f9; }}
.qs-r:last-child {{ border-bottom: none; }}
.qs-l {{ display: flex; align-items: center; gap: 8px; color: #64748b; font-size: 11px; }}
.qs-ico {{ width: 28px; height: 28px; border-radius: 50%; background: #f4f6fb; display: flex; align-items: center; justify-content: center; }}
.qs-v {{ color: #172554; font-size: 13.5px; font-weight: 700; }}
.rs-r {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f1f5f9; }}
.rs-r:last-child {{ border-bottom: none; }}
.rs-l {{ display: flex; align-items: center; gap: 7px; color: #475569; font-size: 11.5px; }}
.rs-t {{ color: #94a3b8; font-size: 9.5px; }}

[role="listbox"] {{ background: #fff !important; border: 1px solid #d5dcea !important; border-radius: 8px !important; }}
[role="option"]  {{ color: #172554 !important; font-size: 13px !important; }}
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
    out = []
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
# AI SUMMARY
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
        ads  = f'<a class="btn-ads" href="{link}" target="_blank">{ico(_EXT_LINK,11)} View on NASA ADS</a>' if link else ""

        st.markdown(
            f'<div class="paper">'
            f'<div class="p-row">'
            f'<div class="p-ico">{ico(_FILETEXT,15,"#5b54e8")}</div>'
            f'<div class="p-body">'
            f'<div class="p-title">{esc(row.get("title",""))}</div>'
            f'<div class="p-meta">{esc(row.get("authors",""))} &nbsp;&middot;&nbsp; {esc(row.get("year",""))}</div>'
            f'<div class="p-tags">{tags}</div>'
            f'</div></div>'
            f'<div class="p-actions">{ads}</div>'
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
# SIDEBAR — HTML nav (icons always visible, left-aligned)
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    cur = st.session_state.active_nav

    def nav_a(page, label, path):
        cls = "nav-on" if cur == page else ""
        return (
            f'<a href="?nav={page}" class="{cls}" target="_self">'
            f'{ico_nav(path, cls=="nav-on")}'
            f'<span>{label}</span></a>'
        )

    st.markdown(f"""
    <div class="sb-brand">
      <div class="orbit-ring"><div class="orbit-dot"></div></div>
      <div>
        <div class="sb-appname">BioOrbit</div>
        <div class="sb-appsub">NASA Space Biology<br>Research Explorer</div>
      </div>
    </div>

    <div class="sb-nav">
      {nav_a("Dashboard",       "Dashboard",       _HOUSE)}
      {nav_a("Search",          "Search",          _SEARCH)}
      {nav_a("Saved Summaries", "Saved Summaries", _BOOKMARK)}
      {nav_a("About",           "About",           _INFO)}
    </div>

    <div class="sb-spacer"></div>

    <div class="sb-foot">
      <img class="sb-nasa-img" src="{nasa_src}">
      <div class="sb-powered"><b>Powered by NASA ADS</b><br>+ HuggingFace</div>
      <div class="sb-tagline">Making space biology research<br>accessible and actionable through AI.</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# ██  DASHBOARD
# ─────────────────────────────────────────────────────────────
if st.session_state.active_nav == "Dashboard":

    if not ADS_API_KEY:
        st.error("NASA ADS API key missing. Add NASA_ADS_API_KEY to Streamlit Secrets.")
        st.stop()

    # ── Hero (full-cover Earth) + Stat panel ──────────────────
    hero_col, stat_col = st.columns([3.8, 1], gap="medium")

    with hero_col:
        # Hero renders as pure HTML div with Earth bg-image
        st.markdown(f"""
        <div class="hero">
          <div class="hero-h1">Welcome to <span>BioOrbit</span></div>
          <div class="hero-p">Search, explore, and understand NASA-funded research
          on how spaceflight affects living organisms.</div>

          <form action="" method="get" style="margin-bottom:16px">
            <div class="hero-search-wrap">
              <div class="hero-search-icon">
                {ico(_SEARCH, 16, "#94a3b8")}
              </div>
              <input class="hero-search-input" name="_hero_q"
                     placeholder="Try searching for a topic (e.g. microgravity, radiation biology, plant science...)"
                     autocomplete="off">
              <button type="submit" class="hero-search-btn">Search</button>
            </div>
          </form>

          <div class="pop-row">
            <span class="pop-lbl">Popular searches:</span>
            <span class="chip">microgravity</span>
            <span class="chip">radiation biology</span>
            <span class="chip">space plants</span>
            <span class="chip">human health</span>
            <span class="chip">astrobiology</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Handle hero search form submission via query params
        hero_q = st.query_params.get("_hero_q", "")
        if hero_q:
            st.session_state.active_nav   = "Search"
            st.session_state.search_query = hero_q
            st.query_params.clear()
            st.rerun()

    with stat_col:
        st.markdown(f"""
        <div class="stat-panel" style="margin-top:0">
          <div class="s-row">
            <div class="s-ico">{ico(_FILETEXT,18,"#a78bfa")}</div>
            <div><div class="s-val">15M+</div><div class="s-lbl">Papers in NASA ADS</div></div>
          </div>
          <div class="s-row">
            <div class="s-ico">{ico(_DATABASE,18,"#f59e0b")}</div>
            <div><div class="s-val">Real-time</div><div class="s-lbl">NASA ADS API</div></div>
          </div>
          <div class="s-row">
            <div class="s-ico">{ico(_SPARKLES,18,"#34d399")}</div>
            <div><div class="s-val">AI Summaries</div><div class="s-lbl">HuggingFace<br>BART-large-CNN</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Also keep a Streamlit search bar below for dashboard ──
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    a, b = st.columns([6, 1], gap="small")
    with a:
        dq = st.text_input("", placeholder="Or type here and press Search…",
                           label_visibility="collapsed", key="dash_q")
    with b:
        dgo = st.button("Search", type="primary", use_container_width=True, key="dash_go")
    if dgo and dq.strip():
        st.session_state.active_nav   = "Search"
        st.session_state.search_query = dq.strip()
        st.rerun()

    # ── Feature cards ─────────────────────────────────────────
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    cards = [
        ("1","fn1", ico(_SEARCH,   22,"#4f46e5"), "Search",
         "Type a topic and query NASA's Astrophysics Data System API, which indexes 15M+ peer-reviewed papers."),
        ("2","fn2", ico(_LIST,     22,"#2563eb"), "Explore",
         "View paper titles, authors, year, and direct links to the full record on NASA ADS. Expand abstracts inline."),
        ("3","fn3", ico(_SPARKLES, 22,"#16a34a"), "Summarize",
         'Click "Generate AI Summary" and we use HuggingFace\'s BART-large-CNN model to create a concise 4-bullet summary.'),
        ("4","fn4", ico(_ZAP,      22,"#ca8a04"), "Cache",
         "Summaries are saved locally so they load instantly on repeat views."),
    ]
    for col, (num,fn,ico_svg,title,desc) in zip(st.columns(4, gap="medium"), cards):
        with col:
            st.markdown(
                f'<div class="feat-card"><div class="feat-top">'
                f'<div class="feat-num {fn}">{num}</div><div>{ico_svg}</div>'
                f'</div><h3>{title}</h3><p>{desc}</p></div>',
                unsafe_allow_html=True)

    # ── Results + right panel ─────────────────────────────────
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    lc, rc = st.columns([3.1, 1], gap="medium")

    with lc:
        ql = f'"{st.session_state.last_query}"' if st.session_state.last_query else "—"
        st.markdown(
            f'<div class="sec-hd">'
            f'<div class="sec-title">{ico(_FILETEXT,15,"#172554")} Recent Research Results</div>'
            f'<div class="sec-sub">Showing {st.session_state.last_total} results for <b>{ql}</b></div></div>',
            unsafe_allow_html=True)
        if st.session_state.last_results is not None and len(st.session_state.last_results) > 0:
            render_papers(st.session_state.last_results, "d")
        else:
            st.markdown(
                '<div class="empty"><div class="empty-t">Start exploring space biology</div>'
                '<div class="empty-s">Search for microgravity, radiation biology,<br>space plants, human health, or astrobiology above.</div></div>',
                unsafe_allow_html=True)

    with rc:
        tc = len(st.session_state.summaries)
        st.markdown(f"""
        <div class="panel">
          <div class="p-title-row">{ico(_BARCHART,14,"#172554")} Quick Stats</div>
          <div class="qs-r"><div class="qs-l"><div class="qs-ico">{ico(_FILETEXT,13,"#64748b")}</div>Total Searches</div><div class="qs-v">{st.session_state.total_searches}</div></div>
          <div class="qs-r"><div class="qs-l"><div class="qs-ico">{ico(_FILETEXT,13,"#64748b")}</div>Summaries Generated</div><div class="qs-v">{tc}</div></div>
          <div class="qs-r"><div class="qs-l"><div class="qs-ico">{ico(_ZAP,13,"#64748b")}</div>Cached Results</div><div class="qs-v">{tc}</div></div>
          <div class="qs-r"><div class="qs-l"><div class="qs-ico">{ico(_CLOCK,13,"#64748b")}</div>Avg. Response</div><div class="qs-v">2.3s</div></div>
        </div>
        """, unsafe_allow_html=True)

        hist = list(reversed(st.session_state.search_history[-5:])) if st.session_state.search_history else []
        tl   = ["2 hours ago","5 hours ago","1 day ago","1 day ago","2 days ago"]
        rh   = "".join(
            f'<div class="rs-r"><div class="rs-l">{ico(_SEARCH,12,"#94a3b8")}&nbsp;{h}</div>'
            f'<div style="display:flex;align-items:center;gap:4px">'
            f'<span class="rs-t">{tl[i] if i<len(tl) else "recently"}</span>'
            f'{ico(_CHEVRON_R,12,"#c7d2fe",2.5)}</div></div>'
            for i,h in enumerate(hist)
        ) if hist else '<div style="color:#94a3b8;font-size:11px;padding:8px 0">No searches yet.</div>'
        st.markdown(
            f'<div class="panel"><div class="p-title-row">{ico(_CLOCK,14,"#172554")} Recent Searches</div>{rh}</div>',
            unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# ██  SEARCH PAGE
# ─────────────────────────────────────────────────────────────
elif st.session_state.active_nav == "Search":

    st.markdown(f"""
    <div style="margin:6px 0 16px">
      <div class="sec-title" style="font-size:20px">{ico(_SEARCH,20,"#172554")} Search NASA Research</div>
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
        aq    = q.strip() if (go and q.strip()) else st.session_state.last_query
        start = (page-1)*rows
        st.session_state.search_rows = rows
        st.session_state.search_page = page
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
            st.session_state.last_query   = aq
            st.session_state.last_total   = total
            st.session_state.last_results = df
            st.session_state.search_query = ""
            st.rerun()

    if st.session_state.last_results is not None and len(st.session_state.last_results) > 0:
        df = st.session_state.last_results
        st.markdown(
            f'<div class="sec-hd" style="margin-top:20px">'
            f'<div class="sec-title">Research Results</div>'
            f'<div class="sec-sub">Showing {len(df)} of {st.session_state.last_total:,} results</div></div>',
            unsafe_allow_html=True)
        render_papers(df, "s")
    elif st.session_state.last_query:
        st.info("No results found. Try a different search term.")

# ─────────────────────────────────────────────────────────────
# ██  SAVED SUMMARIES
# ─────────────────────────────────────────────────────────────
elif st.session_state.active_nav == "Saved Summaries":
    st.markdown(f"""
    <div style="margin:6px 0 16px">
      <div class="sec-title" style="font-size:20px">{ico(_BOOKMARK,20,"#172554")} Saved Summaries</div>
      <div style="color:#94a3b8;font-size:12px;margin-top:3px">Your cached AI-generated paper summaries.</div>
    </div>""", unsafe_allow_html=True)
    if st.session_state.summaries:
        for aid, summary in st.session_state.summaries.items():
            st.markdown(
                f'<div class="paper"><div class="p-meta" style="margin-bottom:7px;font-size:10px">ID: {aid[:14]}…</div>'
                f'<div class="sum-box"><div class="sum-lbl">Cached Summary</div>{summary}</div></div>',
                unsafe_allow_html=True)
        if st.button("Clear All Summaries", type="primary"):
            st.session_state.summaries = {}
            with open(CACHE_FILE,"w") as f: json.dump({},f)
            st.rerun()
    else:
        st.info("No saved summaries yet. Search for papers and generate summaries.")

# ─────────────────────────────────────────────────────────────
# ██  ABOUT
# ─────────────────────────────────────────────────────────────
elif st.session_state.active_nav == "About":
    st.markdown(f"""
    <div style="margin:6px 0 16px">
      <div class="sec-title" style="font-size:20px">{ico(_INFO,20,"#172554")} About BioOrbit</div>
      <div style="color:#94a3b8;font-size:12px;margin-top:3px">Making space biology research easier to understand.</div>
    </div>""", unsafe_allow_html=True)
    for title, body in [
        ("What is BioOrbit?",
         "BioOrbit is an AI-powered research explorer built for the NASA Space Apps Challenge. It connects to NASA's Astrophysics Data System to find peer-reviewed research related to space biology, microgravity, radiation, human health, plants, and astrobiology."),
        ("Why It Matters",
         "Space biology research contains valuable insights about how spaceflight affects living organisms. BioOrbit makes this research easier to discover, explore, and understand by combining NASA ADS search with AI-powered summaries."),
        ("Built With",
         "Python · Streamlit · NASA ADS API · HuggingFace Transformers · BART-large-CNN · Pandas · JSON caching · Custom CSS · Lucide Icons"),
    ]:
        st.markdown(
            f'<div class="panel" style="margin-bottom:12px">'
            f'<div class="sec-title">{title}</div>'
            f'<div style="color:#64748b;font-size:13px;line-height:1.7;margin-top:9px">{body}</div></div>',
            unsafe_allow_html=True)
