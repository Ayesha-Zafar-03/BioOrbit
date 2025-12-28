import streamlit as st
import pandas as pd
import requests
import hashlib

# -------------------------------------------------
# STREAMLIT CLOUD SECRETS
# -------------------------------------------------
ADS_API_KEY = st.secrets.get("NASA_ADS_API_KEY", "")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="BioOrbit",
    page_icon="🧬",
    layout="wide"
)

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "summaries" not in st.session_state:
    st.session_state.summaries = {}

# -------------------------------------------------
# HIDE SIDEBAR
# -------------------------------------------------
st.markdown("""
<style>
[data-testid="stSidebar"] {display:none;}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# ORIGINAL BLACK CSS (UNCHANGED)
# -------------------------------------------------
st.markdown("""
<style>
body, [data-testid="stAppViewContainer"] {
    background-color:#000;
    color:#fff;
}
input, textarea, select {
    background-color:#2C2F36;
    color:white;
    border-radius:8px;
    border:1px solid #444;
}
.stButton>button {
    background-color:#3A3F47;
    color:white;
    border-radius:10px;
    border:1px solid #666;
    transition:all 0.3s ease;
    padding:5px 12px;
    margin:2px;
}
.stButton>button:hover {
    background-color:#6BE6C1;
    color:black;
    transform: translateY(-2px);
    box-shadow:0 4px 8px rgba(107,230,193,0.3);
}
.link-button {
    display:inline-block;
    padding:4px 8px;
    margin-left:5px;
    background-color:#6BE6C1;
    color:black !important;
    border-radius:6px;
    text-decoration:none;
    font-weight:600;
}
.link-button:hover {
    background-color:#4ad1a5;
}
.result-card {
    background-color:#1A1A1A;
    padding:12px;
    border-radius:10px;
    margin-bottom:10px;
    border-left:4px solid #6BE6C1;
}
.warning-box {
    background-color:#2C2F36;
    padding:10px;
    border-radius:6px;
    border-left:3px solid #FFA500;
}
.summary-box {
    background-color:#1A1A1A;
    padding:15px;
    border-radius:8px;
    border-left:4px solid #6BE6C1;
    margin-bottom:15px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# TITLE
# -------------------------------------------------
st.title("🧬 BioOrbit")
st.caption("Explore NASA Space Biology Studies — Live via NASA ADS")

# -------------------------------------------------
# KEY CHECK
# -------------------------------------------------
if not ADS_API_KEY:
    st.error("❌ NASA ADS API key missing. Add it in Streamlit Secrets.")
    st.stop()

# -------------------------------------------------
# NASA ADS SEARCH
# -------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ads_results(query, rows=10):
    url = "https://api.adsabs.harvard.edu/v1/search/query"
    headers = {
        "Authorization": f"Bearer {ADS_API_KEY}",
        "Accept": "application/json"
    }
    params = {
        "q": f'"{query}" biology',
        "fl": "title,abstract,doi,year,author",
        "rows": rows
    }

    r = requests.get(url, headers=headers, params=params, timeout=20)
    if r.status_code != 200:
        return pd.DataFrame(), r.status_code, r.text

    docs = r.json().get("response", {}).get("docs", [])

    data = []
    for d in docs:
        data.append({
            "title": d.get("title", [""])[0],
            "abstract": d.get("abstract", ""),
            "year": d.get("year", ""),
            "authors": ", ".join(d.get("author", [])[:3]),
            "link": (
                f"https://ui.adsabs.harvard.edu/abs/{d.get('doi',[None])[0]}"
                if d.get("doi") else ""
            )
        })

    return pd.DataFrame(data), 200, ""

# -------------------------------------------------
# GROQ SUMMARIZER
# -------------------------------------------------
def summarize_text(text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role":"system","content":"Summarize this NASA space biology research in clear academic language."},
            {"role":"user","content":text}
        ],
        "temperature":0.3
    }

    r = requests.post(url, headers=headers, json=payload, timeout=30)
    if r.status_code != 200:
        return "❌ Summary generation failed."
    return r.json()["choices"][0]["message"]["content"]

# -------------------------------------------------
# SEARCH BAR
# -------------------------------------------------
query = st.text_input(
    "Search NASA Space Biology Studies",
    placeholder="e.g., microgravity, radiation, plants"
)

# -------------------------------------------------
# RESULTS
# -------------------------------------------------
if query:
    with st.spinner("🔎 Searching NASA ADS database..."):
        df, status, error_text = fetch_ads_results(query)

    if status != 200:
        st.error(f"NASA ADS API Error {status}")
        st.code(error_text)
        st.stop()

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

        if st.button(f"✨ Summarize Article {i+1}", key=f"sum_{i}"):
            if not GROQ_API_KEY:
                st.markdown("<div class='warning-box'>⚠️ GROQ API key missing.</div>", unsafe_allow_html=True)
            elif not row.abstract:
                st.markdown("<div class='warning-box'>⚠️ No abstract available.</div>", unsafe_allow_html=True)
            else:
                with st.spinner("🤖 Generating summary..."):
                    if article_id not in st.session_state.summaries:
                        st.session_state.summaries[article_id] = summarize_text(row.abstract[:6000])

                st.markdown(f"""
                <div class="summary-box">
                    <h5>📝 AI Summary</h5>
                    <p>{st.session_state.summaries[article_id]}</p>
                </div>
                """, unsafe_allow_html=True)

# -------------------------------------------------
# FOOTER
# -------------------------------------------------
st.markdown("---")
st.caption("Built with ❤️ for Space Biology Research | Powered by NASA ADS")
