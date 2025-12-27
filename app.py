import streamlit as st
import pandas as pd
import requests, os, hashlib
from dotenv import load_dotenv
from utils.ai_summarizer import summarize_text

# ------------------ CONFIG ------------------
load_dotenv()
ADS_API_KEY = os.getenv("NASA_ADS_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

st.set_page_config(
    page_title="BioOrbit",
    page_icon="🧬",
    layout="wide"
)

# ------------------ SESSION STATE ------------------
for key in ["query", "summaries"]:
    if key not in st.session_state:
        st.session_state[key] = {}

# ------------------ UI STYLES ------------------
st.markdown("""
<style>
body {background-color:#000;color:#fff;}
input {background:#1e1e1e;color:white;}
.result-card {
    background:#111;padding:15px;border-radius:10px;
    border-left:4px solid #6BE6C1;margin-bottom:12px;
}
.link-button {
    display:inline-block;margin-top:6px;
    padding:4px 8px;background:#6BE6C1;
    color:black;text-decoration:none;border-radius:6px;
}
</style>
""", unsafe_allow_html=True)

# ------------------ TITLE ------------------
st.title("🧬 BioOrbit")
st.caption("Live NASA Space Biology Research Explorer (Powered by NASA ADS)")

# ------------------ NASA ADS SEARCH ------------------
@st.cache_data(show_spinner=False)
def fetch_ads_results(query, rows=15):
    url = "https://api.adsabs.harvard.edu/v1/search/query"
    headers = {
        "Authorization": f"Bearer {ADS_API_KEY}"
    }
    params = {
        "q": f"{query} biology microgravity",
        "fl": "title,abstract,doi,year,author",
        "rows": rows
    }

    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    docs = r.json()["response"]["docs"]

    data = []
    for d in docs:
        data.append({
            "title": d.get("title", [""])[0],
            "abstract": d.get("abstract", ""),
            "year": d.get("year", ""),
            "authors": ", ".join(d.get("author", [])[:3]),
            "link": f"https://ui.adsabs.harvard.edu/abs/{d.get('doi',[None])[0]}" if d.get("doi") else ""
        })

    return pd.DataFrame(data)

# ------------------ SEARCH BAR ------------------
query = st.text_input(
    "Search NASA Space Biology Studies",
    placeholder="e.g. microgravity, radiation, plant growth"
)

# ------------------ SEARCH RESULTS ------------------
if query:
    if not ADS_API_KEY:
        st.error("❌ NASA ADS API key missing.")
        st.stop()

    with st.spinner("🔎 Searching NASA ADS database..."):
        df = fetch_ads_results(query)

    if df.empty:
        st.warning("No studies found.")
        st.stop()

    st.success(f"Found {len(df)} studies")

    for i, row in df.iterrows():
        article_id = hashlib.md5(row.title.encode()).hexdigest()

        st.markdown(f"""
        <div class="result-card">
            <h4>{row.title}</h4>
            <p style="color:#aaa;font-size:0.9em;">
                {row.authors} • {row.year}
            </p>
            {"<a class='link-button' target='_blank' href='"+row.link+"'>🔗 View Publication</a>" if row.link else ""}
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"✨ Summarize ({i+1})", key=f"sum_{i}"):
            if not GROQ_API_KEY:
                st.warning("GROQ API key missing.")
            elif not row.abstract:
                st.warning("No abstract available.")
            else:
                with st.spinner("🤖 Generating AI summary..."):
                    if article_id not in st.session_state.summaries:
                        summary = summarize_text(row.abstract[:6000], GROQ_API_KEY)
                        st.session_state.summaries[article_id] = summary

                st.markdown(f"""
                <div style="background:#1a1a1a;padding:15px;
                            border-left:4px solid #6BE6C1;
                            border-radius:8px;margin-bottom:20px;">
                    <h5>📝 AI Summary</h5>
                    <p>{st.session_state.summaries[article_id]}</p>
                </div>
                """, unsafe_allow_html=True)

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("🚀 Powered by NASA ADS • Built for Space Biology Research")
