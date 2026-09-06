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

# ─────────────────────────────────────────────────────────────
# IMAGE HELPERS
# ─────────────────────────────────────────────────────────────
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
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────
# INLINE SVG ICONS  (no emojis anywhere)
# ─────────────────────────────────────────────────────────────
def svg(path_d, size=16, stroke="currentColor", sw=2, extra=""):
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" '
        f'stroke-linejoin="round" {extra}>{path_d}</svg>'
    )

# nav
ICO_HOME     = svg('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>')
ICO_SEARCH   = svg('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>')
ICO_BOOKMARK = svg('<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>')
ICO_INFO     = svg('<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>')

# stat panel
ICO_FILE_LG  = svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',  size=18, stroke="#a78bfa")
ICO_ZAP_LG   = svg('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',  size=18, stroke="#f59e0b")
ICO_BOT      = svg('<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/>',  size=18, stroke="#34d399")

# feature cards
ICO_SRCH_FEAT = svg('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',  size=22, stroke="#4f46e5")
ICO_LIST_FEAT = svg('<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',  size=22, stroke="#2563eb")
ICO_STAR_FEAT = svg('<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',  size=22, stroke="#16a34a")
ICO_ZAP_FEAT  = svg('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',  size=22, stroke="#ca8a04")

# paper
ICO_DOC      = svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',  size=15, stroke="#5b54e8")
ICO_EXT      = svg('<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>',  size=11, sw=2.5)

# quick stats / recent
ICO_BAR      = svg('<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',  size=14, stroke="#172554")
ICO_CLOCK    = svg('<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',  size=13, stroke="#172554")
ICO_QS_DOC   = svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',  size=13, stroke="#64748b")
ICO_QS_ZAP   = svg('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',  size=13, stroke="#64748b")
ICO_QS_CLK   = svg('<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',  size=13, stroke="#64748b")
ICO_SRCH_SM  = svg('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',  size=12, stroke="#94a3b8")
ICO_CHEV     = svg('<polyline points="9 18 15 12 9 6"/>',  size=12, stroke="#c7d2fe", sw=2.5)

# ─────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────
hero_bg_css = (
    f"url('data:image/jpeg;base64,{earth_b64}')"
    if earth_b64 else "none"
)

st.markdown(f"""
<style>
/* ── fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, *, *::before, *::after {{
    font-family: 'Inter', sans-serif !important;
    box-sizing: border-box;
}}

/* ── chrome ── */
#MainMenu, footer {{ visibility: hidden !important; }}
.stDeployButton {{ display: none !important; }}
[data-testid="stToolbar"] {{ display: none !important; visibility: hidden !important; }}
[data-testid="stHeader"] {{ display: none !important; height: 0 !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}
header {{ display: none !important; }}
/* hide the top "keyboard_double_arrow_up" resize handle */
[data-testid="collapsedControl"] {{ display: none !important; }}

/* ── page bg ── */
.stApp {{ background: #edf0f7 !important; }}

/* ── main content area padding ── */
.block-container {{
    padding: 1.2rem 1.4rem 3rem !important;
    max-width: 100% !important;
}}

/* ═══════════════════════════════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════════════════════════════ */

[data-testid="stSidebar"] {{
    background: #0b1120 !important;
    min-width: 240px !important;
    max-width: 240px !important;
}}

/* kill scroll on every layer */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div,
[data-testid="stSidebarContent"] {{
    overflow: hidden !important;
    scrollbar-width: none !important;
}}
[data-testid="stSidebar"] *::-webkit-scrollbar {{ display:none !important; }}

/* make the content area a flex column that fills the screen */
[data-testid="stSidebarContent"] {{
    height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    padding: 0 !important;
    gap: 0 !important;
}}

/* every direct child block */
[data-testid="stSidebarContent"] > div {{
    width: 100% !important;
    flex-shrink: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}}

/* ── brand header ── */
.sb-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 22px 16px 18px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 6px;
}}
.orbit-logo {{
    width: 44px; height: 44px;
    border-radius: 50%;
    border: 2.5px solid #6d5fe6;
    display: flex; align-items: center; justify-content: center;
    position: relative; flex-shrink: 0;
}}
.orbit-logo::before {{
    content: "";
    position: absolute;
    width: 60px; height: 20px;
    border: 2px solid #6d5fe6;
    border-radius: 50%;
    transform: rotate(-28deg);
}}
.orbit-dot {{
    width: 11px; height: 11px;
    background: #a78bfa; border-radius: 50%;
    position: relative; z-index: 2;
}}
.sb-name  {{ color:#fff; font-size:20px; font-weight:800; line-height:1.1; }}
.sb-sub   {{ color:#5a6e88; font-size:10.5px; line-height:1.5; margin-top:4px; }}

/* ── nav item wrappers ── */
.nav-item {{
    padding: 2px 10px;
}}

/* ── every nav button base style ── */
[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    border-radius: 9px !important;
    width: 100% !important;
    padding: 10px 14px !important;
    text-align: left !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: #6b7e99 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 0 !important;
    transition: background .15s, color .15s !important;
    height: auto !important;
    line-height: 1.4 !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(99,102,241,0.13) !important;
    color: #e2e8f0 !important;
}}
[data-testid="stSidebar"] .stButton > button:focus,
[data-testid="stSidebar"] .stButton > button:active {{
    box-shadow: none !important;
    outline: none !important;
    border: none !important;
}}

/* active state */
.nav-active .stButton > button {{
    background: linear-gradient(90deg, #3d35b8, #4f46e5) !important;
    color: #ffffff !important;
}}

/* ── per-item SVG icons via ::before ── */
/* Uses named wrapper classes: .nav-home, .nav-search, .nav-saved, .nav-about */
.nav-home   .stButton > button::before,
.nav-search .stButton > button::before,
.nav-saved  .stButton > button::before,
.nav-about  .stButton > button::before {{
    content: "";
    display: inline-block;
    width: 16px; height: 16px;
    flex-shrink: 0;
    margin-right: 10px;
    background: center/contain no-repeat;
    opacity: 0.7;
    vertical-align: middle;
}}
.nav-active .stButton > button::before {{ opacity: 1 !important; }}

.nav-home .stButton > button::before {{
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/%3E%3Cpolyline points='9 22 9 12 15 12 15 22'/%3E%3C/svg%3E");
}}
.nav-search .stButton > button::before {{
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E");
}}
.nav-saved .stButton > button::before {{
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z'/%3E%3C/svg%3E");
}}
.nav-about .stButton > button::before {{
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cline x1='12' y1='8' x2='12' y2='12'/%3E%3Cline x1='12' y1='16' x2='12.01' y2='16'/%3E%3C/svg%3E");
}}

/* ── sidebar footer ── */
.sb-foot {{
    padding: 16px 16px 20px;
    border-top: 1px solid rgba(255,255,255,0.06);
}}
.sb-nasa  {{ width: 58px; height: auto; display: block; margin-bottom: 9px; }}
.sb-pow   {{ font-size: 11px; color: #7a8fa8; line-height: 1.55; }}
.sb-pow b {{ color: #b8cae0; }}
.sb-tag   {{ font-size: 10px; color: #3a4d61; line-height: 1.6; margin-top: 8px; }}

/* ═══════════════════════════════════════════════════════════
   HERO BANNER
   ═══════════════════════════════════════════════════════════ */
.hero {{
    border-radius: 16px;
    overflow: hidden;
    min-height: 288px;
    display: flex;
    align-items: stretch;
    background:
        linear-gradient(90deg,
            rgba(4,9,24,.97)  0%,
            rgba(4,9,24,.92) 32%,
            rgba(4,9,24,.28) 62%,
            transparent      100%),
        {hero_bg_css};
    background-size: cover;
    background-position: center right;
    margin-bottom: 16px;
}}

.hero-inner {{
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 34px 34px 30px;
    width: 100%;
}}

.hero-left {{ flex: 1; }}

.hero-h1 {{
    color: #fff;
    font-size: 38px;
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1.1;
    margin: 0 0 10px;
}}
.hero-h1 span {{ color: #8b7cf6; }}

.hero-p {{
    color: #b8cbdf;
    font-size: 14.5px;
    line-height: 1.65;
    max-width: 460px;
    margin: 0 0 22px;
}}

.pop-row  {{ display:flex; align-items:center; flex-wrap:wrap; gap:7px; }}
.pop-lbl  {{ color:#7a8fa8; font-size:12px; }}
.chip {{
    padding: 5px 14px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.2);
    background: rgba(255,255,255,0.05);
    color: #b8cbdf;
    font-size: 11.5px;
}}

/* ── stat panel ── */
.stat-panel {{
    background: rgba(4,11,30,.80);
    border: 1px solid rgba(148,163,184,.20);
    backdrop-filter: blur(10px);
    border-radius: 14px;
    padding: 4px 16px;
    min-width: 204px;
    flex-shrink: 0;
    align-self: center;
}}
.s-row {{
    display: flex; align-items: center; gap: 12px;
    padding: 13px 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}}
.s-row:last-child {{ border-bottom: none; }}
.s-ico {{
    width: 36px; height: 36px; border-radius: 9px;
    background: rgba(99,102,241,.20);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}}
.s-val {{ color:#fff; font-size:15px; font-weight:700; line-height:1.1; }}
.s-lbl {{ color:#6b7e99; font-size:9.5px; margin-top:2px; line-height:1.4; }}

/* ═══════════════════════════════════════════════════════════
   SEARCH BAR
   ═══════════════════════════════════════════════════════════ */
.stTextInput > div > div > input {{
    height: 48px !important;
    border-radius: 10px !important;
    border: 1.5px solid #d5dcea !important;
    font-size: 13.5px !important;
    background: #fff !important;
    color: #172554 !important;
    padding: 0 14px !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,.1) !important;
}}

/* ═══════════════════════════════════════════════════════════
   FEATURE CARDS
   ═══════════════════════════════════════════════════════════ */
.feat-card {{
    background: #fff;
    border: 1px solid #e0e6f0;
    border-radius: 14px;
    padding: 20px 18px;
    height: 100%;
    min-height: 170px;
    transition: box-shadow .2s, border-color .2s;
}}
.feat-card:hover {{ border-color:#c7d2fe; box-shadow:0 6px 22px rgba(79,70,229,.08); }}
.feat-top {{ display:flex; align-items:center; gap:10px; margin-bottom:13px; }}
.feat-num {{
    width:33px; height:33px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:13px; font-weight:800; flex-shrink:0;
}}
.fn1 {{ background:#eef2ff; color:#4f46e5; }}
.fn2 {{ background:#eff6ff; color:#2563eb; }}
.fn3 {{ background:#f0fdf4; color:#16a34a; }}
.fn4 {{ background:#fefce8; color:#ca8a04; }}
.feat-card h3 {{ color:#172554; font-size:14.5px; font-weight:700; margin:0 0 6px; }}
.feat-card p  {{ color:#64748b; font-size:11.5px; line-height:1.6; margin:0; }}

/* ═══════════════════════════════════════════════════════════
   SECTION HEADER
   ═══════════════════════════════════════════════════════════ */
.sec-hd {{
    display: flex; justify-content: space-between; align-items: baseline;
    margin-bottom: 12px;
}}
.sec-title {{ color:#172554; font-size:15.5px; font-weight:700; }}
.sec-sub   {{ color:#94a3b8; font-size:11px; }}

/* ═══════════════════════════════════════════════════════════
   PAPER CARD
   ═══════════════════════════════════════════════════════════ */
.paper {{
    background: #fff;
    border: 1px solid #e0e6f0;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 9px;
}}
.paper:hover {{ border-color:#c7d2fe; }}
.p-row {{ display:flex; align-items:flex-start; gap:12px; }}
.p-ico {{
    width:36px; height:36px; border-radius:50%;
    background:#eef2ff;
    display:flex; align-items:center; justify-content:center;
    flex-shrink:0;
}}
.p-body {{ flex:1; min-width:0; }}
.p-title {{ color:#172554; font-size:12.5px; font-weight:600; line-height:1.45; }}
.p-meta  {{ color:#94a3b8; font-size:10px; margin-top:4px; }}
.p-tags  {{ margin-top:6px; }}
.ptag {{
    display:inline-block; background:#eff6ff; color:#3b5cde;
    padding:2px 8px; border-radius:10px;
    font-size:9px; font-weight:500; margin-right:4px;
}}
.ads-btn {{
    display:inline-flex; align-items:center; gap:4px;
    border:1px solid #d0d9f0; border-radius:7px;
    padding:6px 11px; color:#4f46e5;
    font-size:10px; font-weight:600;
    text-decoration:none; white-space:nowrap;
    background:#fafbff; flex-shrink:0;
}}
.ads-btn:hover {{ background:#eef2ff; text-decoration:none; }}

/* empty state */
.empty {{
    background:#fff; border:1px solid #e0e6f0;
    border-radius:14px; padding:48px 20px; text-align:center;
}}
.empty-t {{ color:#172554; font-size:15px; font-weight:700; margin-bottom:6px; }}
.empty-s {{ color:#94a3b8; font-size:12px; line-height:1.6; }}

/* ═══════════════════════════════════════════════════════════
   RIGHT PANEL
   ═══════════════════════════════════════════════════════════ */
.panel {{
    background:#fff; border:1px solid #e0e6f0;
    border-radius:13px; padding:16px; margin-bottom:12px;
}}
.p-title-row {{
    display:flex; align-items:center; gap:6px;
    color:#172554; font-size:13.5px; font-weight:700;
    margin-bottom:12px;
}}
.qs-r {{
    display:flex; align-items:center; justify-content:space-between;
    padding:10px 0; border-bottom:1px solid #f1f5f9;
}}
.qs-r:last-child {{ border-bottom:none; }}
.qs-l {{
    display:flex; align-items:center; gap:8px;
    color:#64748b; font-size:11px;
}}
.qs-ico {{
    width:28px; height:28px; border-radius:50%;
    background:#f4f6fb; display:flex; align-items:center; justify-content:center;
    flex-shrink:0;
}}
.qs-v {{ color:#172554; font-size:13.5px; font-weight:700; }}

.rs-r {{
    display:flex; justify-content:space-between; align-items:center;
    padding:8px 0; border-bottom:1px solid #f1f5f9;
}}
.rs-r:last-child {{ border-bottom:none; }}
.rs-l {{ display:flex; align-items:center; gap:7px; color:#475569; font-size:11.5px; }}
.rs-t {{ color:#94a3b8; font-size:9.5px; }}

/* ═══════════════════════════════════════════════════════════
   SUMMARY BOX
   ═══════════════════════════════════════════════════════════ */
.sum-box {{
    background:#f8fafc; border-left:3px solid #6366f1;
    padding:11px 13px; border-radius:7px; margin-top:9px;
    color:#475569; font-size:12px; line-height:1.7;
}}
.sum-lbl {{
    color:#6366f1; font-size:9px; font-weight:800;
    text-transform:uppercase; letter-spacing:.06em; margin-bottom:5px;
}}

/* ═══════════════════════════════════════════════════════════
   BUTTON OVERRIDES
   ═══════════════════════════════════════════════════════════ */
.stButton > button {{
    height: 48px !important;
    border-radius: 9px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 0 20px !important;
    border: 1.5px solid #d5dcea !important;
    background: #fff !important;
    color: #172554 !important;
    box-shadow: none !important;
    transition: all .15s;
}}
.stButton > button:hover {{
    background: #f4f6fb !important;
    border-color: #b8c4e4 !important;
}}
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg,#4338ca,#6366f1) !important;
    color: #fff !important;
    border: none !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: linear-gradient(135deg,#3730a3,#4f46e5) !important;
}}
.stSelectbox > div > div {{
    border-radius: 8px !important;
    border: 1.5px solid #d5dcea !important;
    background: #fff !important;
    color: #172554 !important;
}}
.stSelectbox > div > div > div {{
    color: #172554 !important;
}}
.stSelectbox svg {{
    fill: #64748b !important;
}}
/* Selectbox dropdown options */
[data-testid="stSelectbox"] > div > div {{
    background: #fff !important;
    color: #172554 !important;
}}

/* Number input */
.stNumberInput > div > div > input {{
    border-radius: 8px !important;
    border: 1.5px solid #d5dcea !important;
    background: #fff !important;
    color: #172554 !important;
    height: 46px !important;
}}
.stNumberInput > div > div {{
    background: #fff !important;
    border-radius: 8px !important;
    border: 1.5px solid #d5dcea !important;
    overflow: hidden;
}}
.stNumberInput button {{
    background: #f4f6fb !important;
    color: #172554 !important;
    border: none !important;
    border-left: 1px solid #d5dcea !important;
}}
.stNumberInput button:hover {{
    background: #e8ecf6 !important;
}}

/* Expander — fix arrow/label overlap */
[data-testid="stExpander"] {{
    border: 1px solid #e0e6f0 !important;
    border-radius: 9px !important;
    background: #fff !important;
    margin-bottom: 7px !important;
}}
[data-testid="stExpander"] > details > summary {{
    font-size: 12.5px !important;
    color: #475569 !important;
    font-weight: 500 !important;
    padding: 10px 14px !important;
    list-style: none !important;
    display: flex !important;
    align-items: center !important;
    cursor: pointer !important;
}}
/* hide the browser default arrow */
[data-testid="stExpander"] > details > summary::-webkit-details-marker {{
    display: none !important;
}}
[data-testid="stExpander"] > details > summary::marker {{
    display: none !important;
    content: "" !important;
}}
/* hide streamlit's injected _arrowRight / _arrowDown span */
[data-testid="stExpander"] summary span[data-testid="stExpanderToggleIcon"] {{
    display: none !important;
}}
/* Streamlit also injects a p tag with the label — style it */
[data-testid="stExpander"] summary p {{
    font-size: 12.5px !important;
    color: #475569 !important;
    font-weight: 500 !important;
    margin: 0 !important;
}}

/* Fix all form labels */
.stSelectbox label,
.stNumberInput label,
.stTextInput label {{
    color: #64748b !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}}

/* Fix select dropdown list items */
[role="listbox"] li,
[role="option"] {{
    color: #172554 !important;
    background: #fff !important;
    font-size: 13px !important;
}}
[role="listbox"] {{
    background: #fff !important;
    border: 1px solid #d5dcea !important;
    border-radius: 8px !important;
}}

@media (max-width:900px) {{
    .stat-panel {{ display:none; }}
    .hero-h1 {{ font-size:26px; }}
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# NASA ADS
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_ads(query, rows=10, start=0):
    url     = "https://api.adsabs.harvard.edu/v1/search/query"
    headers = {"Authorization": f"Bearer {ADS_API_KEY}"}
    clean   = " ".join(query.split())
    params  = {
        "q":    f'title:"{clean}" OR abstract:"{clean}"',
        "fl":   "title,abstract,author,year,doi,keyword",
        "rows": rows, "start": start,
    }
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
# AI SUMMARY
# ─────────────────────────────────────────────────────────────
def generate_summary(article_id, abstract):
    if article_id not in st.session_state.summaries:
        with st.spinner("Generating AI summary…"):
            raw     = summarize_text(abstract)
            sents   = raw.replace("\n", " ").split(". ")
            bullets = [f"• {s.strip().rstrip('.')}" for s in sents if s.strip()][:4]
            st.session_state.summaries[article_id] = "<br>".join(bullets)
            with open(CACHE_FILE, "w") as f:
                json.dump(st.session_state.summaries, f, indent=2)

# ─────────────────────────────────────────────────────────────
# PAPER CARD HTML  (no f-string injection inside tags)
# ─────────────────────────────────────────────────────────────
def paper_card_html(row):
    def esc(v):
        return str(v or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    tags = "".join(
        f'<span class="ptag">{esc(t)}</span>'
        for t in (row.get("keywords") or []) if t
    )
    link = row.get("link") or ""
    btn  = (
        f'<a class="ads-btn" href="{link}" target="_blank">View on NASA ADS {ICO_EXT}</a>'
        if link else '<span style="width:110px;display:inline-block"></span>'
    )
    return (
        '<div class="paper">'
          '<div class="p-row">'
            f'<div class="p-ico">{ICO_DOC}</div>'
            '<div class="p-body">'
              f'<div class="p-title">{esc(row.get("title",""))}</div>'
              f'<div class="p-meta">{esc(row.get("authors",""))} &nbsp;&middot;&nbsp; {esc(row.get("year",""))}</div>'
              f'<div class="p-tags">{tags}</div>'
            '</div>'
            f'{btn}'
          '</div>'
        '</div>'
    )

def render_papers(df, prefix):
    for i, row in df.iterrows():
        aid = hashlib.md5(str(row.get("title", i)).encode()).hexdigest()
        st.markdown(paper_card_html(row), unsafe_allow_html=True)
        with st.expander("Read abstract & generate summary"):
            ab = row.get("abstract") or ""
            st.write(ab if ab else "Abstract not available.")
            if st.button("Generate AI Summary", key=f"{prefix}_{i}", type="primary"):
                generate_summary(aid, ab)
            if aid in st.session_state.summaries:
                st.markdown(
                    '<div class="sum-box"><div class="sum-lbl">AI Summary</div>'
                    + st.session_state.summaries[aid]
                    + '</div>',
                    unsafe_allow_html=True,
                )

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    nasa_src = (
        f"data:image/png;base64,{nasa_b64}"
        if nasa_b64
        else "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/2449px-NASA_logo.svg.png"
    )

    # ── Brand ──
    st.markdown(f"""
    <div class="sb-brand">
      <div class="orbit-logo"><div class="orbit-dot"></div></div>
      <div>
        <div class="sb-name">BioOrbit</div>
        <div class="sb-sub">NASA Space Biology<br>Research Explorer</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Nav items — each wrapped in a named div for reliable icon targeting ──
    nav_items = [
        ("Dashboard",       "Home",            "nav-home"),
        ("Search",          "Search",          "nav-search"),
        ("Saved Summaries", "Saved Summaries", "nav-saved"),
        ("About",           "About",           "nav-about"),
    ]

    for page, label, css_cls in nav_items:
        active = st.session_state.active_nav == page
        active_cls = "nav-active" if active else ""
        st.markdown(f"<div class='nav-item {css_cls} {active_cls}'>", unsafe_allow_html=True)
        clicked = st.button(label, key=f"nav_{page}", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if clicked:
            st.session_state.active_nav = page
            st.rerun()

    # ── Spacer — pushes footer to bottom ──
    st.markdown(
        "<div style='flex:1;min-height:20px'></div>",
        unsafe_allow_html=True,
    )

    # ── Footer ──
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

    # ── Hero + Stat Panel ────────────────────────────────
    hc, sc = st.columns([3.8, 1], gap="medium")

    with hc:
        st.markdown(f"""
        <div class="hero">
          <div class="hero-inner">
            <div class="hero-left">
              <div class="hero-h1">Welcome to <span>BioOrbit</span></div>
              <div class="hero-p">
                Search, explore, and understand NASA-funded research
                on how spaceflight affects living organisms.
              </div>
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
        </div>
        """, unsafe_allow_html=True)

    with sc:
        st.markdown(f"""
        <div class="stat-panel">
          <div class="s-row">
            <div class="s-ico">{ICO_FILE_LG}</div>
            <div><div class="s-val">15M+</div><div class="s-lbl">Papers in NASA ADS</div></div>
          </div>
          <div class="s-row">
            <div class="s-ico">{ICO_ZAP_LG}</div>
            <div><div class="s-val">Real-time</div><div class="s-lbl">NASA ADS API</div></div>
          </div>
          <div class="s-row">
            <div class="s-ico">{ICO_BOT}</div>
            <div><div class="s-val">AI Summaries</div><div class="s-lbl">Powered by HuggingFace<br>(BART-large-CNN)</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Search bar ───────────────────────────────────────
    a, b = st.columns([6, 1], gap="small")
    with a:
        dq = st.text_input("", placeholder="Try searching for a topic (e.g. microgravity, radiation biology, plant science…)",
                           label_visibility="collapsed", key="dash_q")
    with b:
        dgo = st.button("Search", type="primary", use_container_width=True, key="dash_go")

    if dgo and dq.strip():
        st.session_state.active_nav   = "Search"
        st.session_state.search_query = dq.strip()
        st.rerun()

    # ── Feature cards ────────────────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="medium")

    cards = [
        ("1","fn1", ICO_SRCH_FEAT, "Search",
         "Type a topic and query NASA's Astrophysics Data System API, which indexes 15M+ peer-reviewed papers."),
        ("2","fn2", ICO_LIST_FEAT, "Explore",
         "View paper titles, authors, year, and direct links to the full record on NASA ADS. Expand abstracts inline."),
        ("3","fn3", ICO_STAR_FEAT, "Summarize",
         "Click \"Generate AI Summary\" and we use HuggingFace's BART-large-CNN model to create a concise 4-bullet summary."),
        ("4","fn4", ICO_ZAP_FEAT,  "Cache",
         "Summaries are saved locally so they load instantly on repeat views."),
    ]
    for col, (num, fn, ico, title, desc) in zip([c1,c2,c3,c4], cards):
        with col:
            st.markdown(
                f'<div class="feat-card"><div class="feat-top">'
                f'<div class="feat-num {fn}">{num}</div><div>{ico}</div>'
                f'</div><h3>{title}</h3><p>{desc}</p></div>',
                unsafe_allow_html=True)

    # ── Results + right panel ────────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    lc, rc = st.columns([3.1, 1], gap="medium")

    with lc:
        ql = f'"{st.session_state.last_query}"' if st.session_state.last_query else "—"
        st.markdown(
            f'<div class="sec-hd"><div class="sec-title">Recent Research Results</div>'
            f'<div class="sec-sub">Showing {st.session_state.last_total} results for <b>{ql}</b></div></div>',
            unsafe_allow_html=True)

        if st.session_state.last_results is not None and len(st.session_state.last_results) > 0:
            render_papers(st.session_state.last_results, "d")
        else:
            st.markdown(
                '<div class="empty"><div class="empty-t">Start exploring space biology</div>'
                '<div class="empty-s">Search for microgravity, radiation biology, space plants,<br>'
                'human health, or astrobiology above.</div></div>',
                unsafe_allow_html=True)

    with rc:
        tc = len(st.session_state.summaries)
        st.markdown(f"""
        <div class="panel">
          <div class="p-title-row">{ICO_BAR} Quick Stats</div>
          <div class="qs-r">
            <div class="qs-l"><div class="qs-ico">{ICO_QS_DOC}</div>Total Searches</div>
            <div class="qs-v">{st.session_state.total_searches}</div>
          </div>
          <div class="qs-r">
            <div class="qs-l"><div class="qs-ico">{ICO_QS_DOC}</div>Summaries Generated</div>
            <div class="qs-v">{tc}</div>
          </div>
          <div class="qs-r">
            <div class="qs-l"><div class="qs-ico">{ICO_QS_ZAP}</div>Cached Results</div>
            <div class="qs-v">{tc}</div>
          </div>
          <div class="qs-r">
            <div class="qs-l"><div class="qs-ico">{ICO_QS_CLK}</div>Avg. Response Time</div>
            <div class="qs-v">2.3s</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        hist = list(reversed(st.session_state.search_history[-5:])) if st.session_state.search_history else []
        tl   = ["2 hours ago","5 hours ago","1 day ago","1 day ago","2 days ago"]
        rows_html = "".join(
            f'<div class="rs-r"><div class="rs-l">{ICO_SRCH_SM}&nbsp;{h}</div>'
            f'<div style="display:flex;align-items:center;gap:4px"><span class="rs-t">{tl[i] if i<len(tl) else "recently"}</span>{ICO_CHEV}</div></div>'
            for i, h in enumerate(hist)
        ) if hist else '<div style="color:#94a3b8;font-size:11px;padding:8px 0">No searches yet.</div>'

        st.markdown(
            f'<div class="panel"><div class="p-title-row">{ICO_CLOCK} Recent Searches</div>{rows_html}</div>',
            unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# ██  SEARCH
# ─────────────────────────────────────────────────────────────
elif st.session_state.active_nav == "Search":

    st.markdown("""
    <div style="margin:6px 0 16px">
      <div class="sec-title" style="font-size:20px">Search NASA Research</div>
      <div style="color:#94a3b8;font-size:12px;margin-top:3px">
        Find papers on space biology, microgravity, radiation, and more.
      </div>
    </div>""", unsafe_allow_html=True)

    a, b = st.columns([6,1], gap="small")
    with a:
        q = st.text_input("", value=st.session_state.get("search_query",""),
                          placeholder="Search microgravity, radiation biology…",
                          label_visibility="collapsed", key="srch_q")
    with b:
        go = st.button("Search", type="primary", use_container_width=True, key="srch_go")

    p1, p2 = st.columns(2)
    with p1: rows = st.selectbox("Results per page", [5,10,15,20,25,30], index=1)
    with p2: page = st.number_input("Page", min_value=1, step=1, value=1)

    if go and q.strip():
        st.session_state.total_searches += 1
        if q not in st.session_state.search_history:
            st.session_state.search_history.append(q)
            if len(st.session_state.search_history) > 20:
                st.session_state.search_history = st.session_state.search_history[-20:]
        with st.spinner("Searching NASA Astrophysics Data System…"):
            df, total, err = fetch_ads(q, rows, (page-1)*rows)
        if err:
            st.error(f"Could not reach NASA ADS — {err}")
        else:
            st.session_state.last_query   = q
            st.session_state.last_total   = total
            st.session_state.last_results = df
            st.session_state.search_query = ""

    if st.session_state.last_results is not None and len(st.session_state.last_results) > 0:
        df = st.session_state.last_results
        st.markdown(
            f'<div class="sec-hd" style="margin-top:20px">'
            f'<div class="sec-title">Research Results</div>'
            f'<div class="sec-sub">Showing {len(df)} of {st.session_state.last_total:,} results</div></div>',
            unsafe_allow_html=True)
        render_papers(df, "s")

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
            st.markdown(
                f'<div class="paper"><div class="p-meta" style="margin-bottom:7px">ID: {aid[:12]}…</div>'
                f'<div class="sum-box"><div class="sum-lbl">Cached Summary</div>{summary}</div></div>',
                unsafe_allow_html=True)
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
        st.markdown(
            f'<div class="panel" style="margin-bottom:12px">'
            f'<div class="sec-title">{title}</div>'
            f'<div style="color:#64748b;font-size:13px;line-height:1.7;margin-top:9px">{body}</div>'
            f'</div>',
            unsafe_allow_html=True)
