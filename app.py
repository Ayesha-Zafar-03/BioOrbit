import streamlit as st
import pandas as pd
from utils.search_engine import load_dataset, search_publications
from utils.ai_summarizer import summarize_text
from dotenv import load_dotenv
import os, requests, hashlib, time
from bs4 import BeautifulSoup

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY", "")

# -------------------------------
# Page settings
# -------------------------------
st.set_page_config(page_title="BioOrbit", layout="wide", page_icon="🧬")

# Initialize session state
for key in ['query', 'summarizing', 'fetched_content', 'summaries']:
    if key not in st.session_state:
        st.session_state[key] = {} if key != 'query' else ""

# -------------------------------
# Hide sidebar
# -------------------------------
st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Custom CSS for dark theme & buttons
# -------------------------------
st.markdown("""
<style>
body, [data-testid="stAppViewContainer"] { background-color: #000000; color: #FFFFFF; }
input, textarea, select { background-color: #2C2F36 !important; color: white !important; border-radius: 8px; border: 1px solid #444; }
.stButton>button { background-color: #3A3F47; color: white; border-radius: 10px; border: 1px solid #666; transition: all 0.3s ease; }
.stButton>button:hover { background-color: #6BE6C1; color: black; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(107, 230, 193, 0.3); }
.link-button { display: inline-block; padding: 4px 10px; margin-left: 10px; background-color: #6BE6C1; color: black !important; border-radius: 6px; text-decoration: none; font-weight: 600; transition: all 0.3s ease; }
.link-button:hover { background-color: #4ad1a5; transform: translateY(-1px); }
.result-card { background-color: #1A1A1A; padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 4px solid #6BE6C1; transition: all 0.3s ease; }
.result-card:hover { background-color: #222222; box-shadow: 0 4px 12px rgba(107, 230, 193, 0.2); }
.warning-box { background-color: #2C2F36; padding: 10px; border-radius: 6px; border-left: 3px solid #FFA500; margin: 10px 0; }
.loading-shimmer { background: linear-gradient(90deg, #1A1A1A 25%, #2C2F36 50%, #1A1A1A 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# App Title & Subtitle (Centered)
# -------------------------------
st.markdown("""
<h1 style="text-align: center; margin-bottom: 5px;">🧬 BioOrbit</h1>
<p style="text-align: center; color:#AAAAAA; margin-top:0; font-size:1.1rem;">
Explore NASA's 608 space biology studies — online or offline!
</p>
""", unsafe_allow_html=True)
st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# -------------------------------
# Example Queries (Centered)
# -------------------------------
st.markdown("<h3 style='text-align:center; margin-bottom:10px;'>Try these example searches:</h3>", unsafe_allow_html=True)
with st.container():
    col1, col2, col3 = st.columns([1,1,1], gap="medium")
    with col1:
        if st.button("🌱 Plant Biology"):
            st.session_state.query = "plant"
            st.session_state.summarizing = {}
            st.experimental_rerun()
    with col2:
        if st.button("🧫 Microgravity"):
            st.session_state.query = "microgravity"
            st.session_state.summarizing = {}
            st.experimental_rerun()
    with col3:
        if st.button("🧬 Stem Cells"):
            st.session_state.query = "stem cells"
            st.session_state.summarizing = {}
            st.experimental_rerun()
st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# -------------------------------
# Search Bar (Centered)
# -------------------------------
st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
query = st.text_input(
    "Search NASA Space Biology Studies",
    placeholder="e.g., microgravity, radiation, plants...",
    value=st.session_state.query,
    key="search_input"
)
st.markdown("</div>", unsafe_allow_html=True)
if query != st.session_state.query:
    st.session_state.query = query
    st.session_state.summarizing = {}

# -------------------------------
# Load Dataset (Cached)
# -------------------------------
@st.cache_data
def load_data():
    return load_dataset("nasa_space_biology_608.csv")
df = load_data()

# -------------------------------
# Fetch article text function (Cached)
# -------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_article_text(url):
    if not url:
        return "", "no_url"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        response = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        if response.status_code != 200: return "", f"http_error_{response.status_code}"
        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup.find_all(['script','style','nav','footer','header','aside','iframe']):
            element.decompose()
        paragraphs = soup.find_all('p', limit=30)
        text_content = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]
        full_text = ' '.join(text_content)
        full_text = ' '.join(full_text.split())
        status = "success" if len(full_text) > 300 else "insufficient"
        return full_text[:8000], status
    except:
        return "", "error"

# -------------------------------
# Get content for summary
# -------------------------------
def get_content_for_summary(content, content_source, link, article_id):
    if content and len(content.strip()) > 500 and content_source != "title_only":
        return content, "dataset", len(content)
    if article_id in st.session_state.fetched_content:
        cached_text, cached_status = st.session_state.fetched_content[article_id]
        if cached_text and len(cached_text) > 100:
            return cached_text, cached_status, len(cached_text)
    if link:
        fetched_text, status = fetch_article_text(link)
        st.session_state.fetched_content[article_id] = (fetched_text, status)
        if fetched_text and len(fetched_text) > 100:
            return fetched_text, status, len(fetched_text)
    return content, content_source, len(content) if content else 0

# -------------------------------
# Generate summary (cached)
# -------------------------------
def generate_summary_cached(article_text, article_id, api_key):
    if article_id in st.session_state.summaries:
        return st.session_state.summaries[article_id], True
    summary = summarize_text(article_text, api_key)
    st.session_state.summaries[article_id] = summary
    return summary, False

# -------------------------------
# Search & Display Results
# -------------------------------
if st.session_state.query:
    try:
        with st.spinner("Searching NASA database..."):
            results = search_publications(st.session_state.query, df)
        if results.empty:
            st.warning("No results found.")
        else:
            st.success(f"Found {len(results)} studies for '{st.session_state.query}'")
            st.markdown("<hr>", unsafe_allow_html=True)
            for i, row in enumerate(results.itertuples(), start=1):
                title = row.title
                link = getattr(row, "link","")
                content = getattr(row,"content","")
                content_source = getattr(row,"content_source","")
                article_id = f"{st.session_state.query}_{i}_{hashlib.md5(title.encode()).hexdigest()[:8]}"
                
                st.markdown(f"""
                <div class="result-card">
                    <h4 style="margin-bottom:5px;">{i}. {title}</h4>
                    {"<a href='" + link + "' target='_blank' class='link-button'>🔗 View Publication</a>" if link else ""}
                </div>
                """, unsafe_allow_html=True)
                
                with st.container():
                    summarize_button = st.button(f"✨ Summarize Article {i}", key=f"summarize_{i}")
                    if summarize_button: st.session_state.summarizing[i] = True
                    if st.session_state.summarizing.get(i, False):
                        if not api_key:
                            st.markdown("""<div class="warning-box">⚠️ <strong>API Key Required</strong><br>Please provide your GROQ API key in the .env file.</div>""", unsafe_allow_html=True)
                        else:
                            if article_id in st.session_state.summaries:
                                summary = st.session_state.summaries[article_id]
                                st.markdown(f"""
                                <div style="background-color:#1A1A1A;padding:15px;border-radius:8px;
                                border-left:4px solid #6BE6C1;margin-bottom:15px;">
                                <h5 style="color:#6BE6C1;">📝 AI Summary (cached)</h5>
                                <p style="color:#FFFFFF;line-height:1.6;">{summary}</p></div>
                                """, unsafe_allow_html=True)
                            else:
                                summary_placeholder = st.empty()
                                with summary_placeholder.container():
                                    st.markdown("""<div class="loading-shimmer" style="padding:15px;border-radius:8px;height:80px;margin-bottom:15px;"><p style="color:#999;">⏳ Generating summary...</p></div>""", unsafe_allow_html=True)
                                article_text, source_status, char_count = get_content_for_summary(content, content_source, link, article_id)
                                if char_count >= 100:
                                    try:
                                        optimized_text = article_text[:6000]
                                        summary, _ = generate_summary_cached(optimized_text, article_id, api_key)
                                        with summary_placeholder.container():
                                            st.markdown(f"""
                                            <div style="background-color:#1A1A1A;padding:15px;border-radius:8px;
                                                border-left:4px solid #6BE6C1;margin-bottom:15px;">
                                                <h5 style="color:#6BE6C1;">📝 AI Summary ({char_count} chars)</h5>
                                                <p style="color:#FFFFFF;line-height:1.6;">{summary}</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                    except Exception as e:
                                        with summary_placeholder.container():
                                            st.markdown(f"""<div class="warning-box">❌ <strong>Summary Generation Failed</strong><br>Error: {str(e)}</div>""", unsafe_allow_html=True)
                                else:
                                    with summary_placeholder.container():
                                        st.markdown(f"""<div style="background-color:#1E2128;padding:15px;border-radius:8px;border-left:4px solid #FFA500;margin-bottom:15px;">
                                        <h5 style="color:#FFA500;">📄 Basic Information</h5>
                                        <p style="color:#CCC;"><strong>Title:</strong> {title}</p>
                                        {f'<p style="color:#CCC;"><strong>Available text:</strong> {article_text[:200]}</p>' if article_text else ''}
                                        <p style="color:#999;font-size:0.9em;margin-top:10px;">⚠️ Limited content available ({char_count} characters). Visit the publication link for full details.</p></div>""", unsafe_allow_html=True)
                st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Search Error: {e}")

# -------------------------------
# Footer
# -------------------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.caption("Built with ❤️ for Space Biology Research | Dataset: NASA Space Biology Studies")
