import streamlit as st
import pandas as pd
import requests
import hashlib
import json
import os

# =================================================
# IMPORT SUMMARIZER
# =================================================
from utils.ai_summarizer import summarize_text

# =================================================
# SECRETS
# =================================================
ADS_API_KEY = st.secrets.get("NASA_ADS_API_KEY", "")

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="BioOrbit",
    page_icon="🧬",
    layout="wide"
)

# =================================================
# DEBUG
# =================================================
st.write("NASA ADS key loaded:", bool(ADS_API_KEY))

# =================================================
# SESSION STATE & CACHE FILE
# =================================================
CACHE_FILE = "summary_cache.json"

# Load cache file if exists
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cached_summaries = json.load(f)
else:
    cached_summaries = {}

if "summaries" not in st.session_state:
    st.session_state.summaries = cached_summaries

# =================================================
# BLACK UI
# =================================================
st.markdown("""
<style>
body, [data-testid="stAppViewContainer"] {
    background-color:#000;
    color:#fff;
}
input, textarea {
    background:#2C2F36;
    color:white;
}
.stButton>button {
    background:#3A3F47;
    color:white;
    border-radius:8px;
}
.stButton>button:hover {
    background:#6BE6C1;
    color:black;
}
.result-card {
    background:#1A1A1A;
    padding:15px;
    border-radius:10px;
    border-left:4px solid #6BE6C1;
    margin-bottom:10px;
}
.summary-box {
    background:#222222;
    padding:12px;
    border-radius:8px;
    border-left:4px solid #6BE6C1;
    margin-bottom:20px;
    white-space: pre-line;
}
.link-button {
    background:#6BE6C1;
    color:black;
    padding:4px 8px;
    border-radius:6px;
    text-decoration:none;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# TITLE
# =================================================
st.markdown("""
<div style='text-align: center;'>
    <h1>🧬 BioOrbit</h1>
    <p style='color: #aaa;'>Explore NASA Space Biology Research</p>
</div>
""", unsafe_allow_html=True)

# =================================================
# STOP IF KEYS MISSING
# =================================================
if not ADS_API_KEY:
    st.error("❌ NASA ADS API key missing in Streamlit Secrets.")
    st.stop()

# =================================================
# NASA ADS FETCH
# =================================================
@st.cache_data(ttl=3600)
def fetch_ads(query, rows, start):
    url = "https://api.adsabs.harvard.edu/v1/search/query"
    headers = {"Authorization": f"Bearer {ADS_API_KEY}"}
    params = {
        "q": query,
        "fl": "title,abstract,author,year,doi",
        "rows": rows,
        "start": start
    }

    r = requests.get(url, headers=headers, params=params, timeout=20)
    if r.status_code != 200:
        return pd.DataFrame(), 0, r.text

    data = r.json()["response"]
    total = data["numFound"]

    rows_data = []
    for d in data["docs"]:
        rows_data.append({
            "title": d.get("title", [""])[0],
            "abstract": d.get("abstract", ""),
            "year": d.get("year", ""),
            "authors": ", ".join(d.get("author", [])[:3]),
            "link": f"https://ui.adsabs.harvard.edu/abs/{d.get('doi',[None])[0]}"
            if d.get("doi") else ""
        })

    return pd.DataFrame(rows_data), total, ""

# =================================================
# SEARCH UI
# =================================================
query = st.text_input("Search Space Biology", placeholder="microgravity, radiation, plants")
rows = st.slider("Results per page", 5, 30, 10)
page = st.number_input("Page", min_value=1, step=1)
start = (page - 1) * rows

# =================================================
# RESULTS
# =================================================
if query:
    with st.spinner("🔎 Searching NASA ADS..."):
        df, total, error = fetch_ads(query, rows, start)

    if error:
        st.error("NASA ADS error")
        st.code(error)
        st.stop()

    st.success(f"📊 Total papers found: {total}")
    st.caption(f"Page {page} • {rows} results")

    for i, row in df.iterrows():
        article_id = hashlib.md5(row.title.encode()).hexdigest()

        # Paper card
        st.markdown(f"""
        <div class="result-card">
            <h4>{row.title}</h4>
            <p style="color:#aaa;"><b>Authors:</b> {row.authors}  <b>Year:</b> {row.year}</p>
            {"<a class='link-button' target='_blank' href='"+row.link+"'>🔗 View</a>" if row.link else ""}
        </div>
        """, unsafe_allow_html=True)

        # Summary button + summary box
        if st.button(f"✨ Summarize {i+1}", key=f"s{i}"):
            if article_id not in st.session_state.summaries:
                with st.spinner("🤖 Generating summary..."):
                    summary_text = summarize_text(row.abstract)
                    # Convert to 4-bullet summary
                    bullets = summary_text.split(". ")
                    bullets = [f"• {b.strip()}" for b in bullets if b][:4]
                    st.session_state.summaries[article_id] = "<br>".join(bullets)

                    # Save to cache file
                    with open(CACHE_FILE, "w") as f:
                        json.dump(st.session_state.summaries, f)

            st.markdown(f"""
            <div class="summary-box">
                <h5> AI Summary</h5>
                <p>{st.session_state.summaries[article_id]}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Powered by NASA ADS + HuggingFace 🤗 + Ayesha Zafar")
