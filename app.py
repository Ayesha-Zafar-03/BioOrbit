import streamlit as st
import pandas as pd
import requests
import hashlib

# =================================================
# SECRETS
# =================================================
ADS_API_KEY = st.secrets.get("NASA_ADS_API_KEY", "")
HF_API_KEY = st.secrets.get("HF_API_KEY", "")

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
st.write("HF key loaded:", bool(HF_API_KEY))

# =================================================
# SESSION STATE
# =================================================
if "summaries" not in st.session_state:
    st.session_state.summaries = {}

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
    padding:12px;
    border-radius:10px;
    border-left:4px solid #6BE6C1;
    margin-bottom:10px;
}
.summary-box {
    background:#1A1A1A;
    padding:15px;
    border-radius:8px;
    border-left:4px solid #6BE6C1;
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
st.title("🧬 BioOrbit")
st.caption("Explore NASA Space Biology Research")

# =================================================
# STOP IF KEYS MISSING
# =================================================
if not ADS_API_KEY or not HF_API_KEY:
    st.error("❌ API keys missing in Streamlit Secrets.")
    st.stop()

# =================================================
# HF SUMMARIZER
# =================================================
HF_MODEL = "facebook/bart-large-cnn"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

def summarize_text(text):
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": text[:3000],
        "parameters": {
            "max_length": 150,
            "min_length": 60,
            "do_sample": False
        }
    }

    r = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)

    if r.status_code != 200:
        return f"❌ HF Error {r.status_code}: {r.text}"

    result = r.json()
    return result[0]["summary_text"]

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

    for i, row in df.iterrows():
        article_id = hashlib.md5(row.title.encode()).hexdigest()

        st.markdown(f"""
        <div class="result-card">
            <h4>{row.title}</h4>
            <p style="color:#aaa;">{row.authors} • {row.year}</p>
            {"<a class='link-button' target='_blank' href='"+row.link+"'>🔗 View</a>" if row.link else ""}
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"✨ Summarize {i+1}", key=f"s{i}"):
            if article_id not in st.session_state.summaries:
                with st.spinner("🤖 Generating summary..."):
                    st.session_state.summaries[article_id] = summarize_text(row.abstract)

            st.markdown(f"""
            <div class="summary-box">
                <h5>📝 AI Summary</h5>
                <p>{st.session_state.summaries[article_id]}</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.caption("Powered by NASA ADS + HuggingFace 🤗")
