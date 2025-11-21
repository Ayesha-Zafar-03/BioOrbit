import streamlit as st
import pandas as pd
from utils.search_engine import load_dataset, search_publications
from utils.ai_summarizer import summarize_text
from dotenv import load_dotenv
import os, requests, hashlib, time
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY", "")

# Page settings
st.set_page_config(page_title="BioOrbit", layout="wide", page_icon="🧬")

# Initialize session state
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'summarizing' not in st.session_state:
    st.session_state.summarizing = {}
if 'fetched_content' not in st.session_state:
    st.session_state.fetched_content = {}
if 'summaries' not in st.session_state:
    st.session_state.summaries = {}

# Hide sidebar
st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# Custom CSS
st.markdown("""
<style>
body, [data-testid="stAppViewContainer"] {background-color:#000;color:#fff;}
input, textarea, select {background-color:#2C2F36;color:white;border-radius:8px;border:1px solid #444;}
.stButton>button {background-color:#3A3F47;color:white;border-radius:10px;border:1px solid #666;transition: all 0.3s ease;padding:5px 12px;margin:2px;}
.stButton>button:hover {background-color:#6BE6C1;color:black;transform: translateY(-2px);box-shadow:0 4px 8px rgba(107,230,193,0.3);}
.link-button {display:inline-block;padding:4px 8px;margin-left:5px;background-color:#6BE6C1;color:black !important;border-radius:6px;text-decoration:none;font-weight:600;transition:all 0.3s ease;}
.link-button:hover {background-color:#4ad1a5;transform: translateY(-1px);}
.result-card {background-color:#1A1A1A;padding:10px 12px;border-radius:10px;margin-bottom:8px;border-left:4px solid #6BE6C1;transition:all 0.3s ease;}
.result-card:hover {background-color:#222222;box-shadow:0 4px 12px rgba(107,230,193,0.2);}
.warning-box {background-color:#2C2F36;padding:8px;border-radius:6px;border-left:3px solid #FFA500;margin:6px 0;}
.loading-shimmer {background:linear-gradient(90deg,#1A1A1A 25%,#2C2F36 50%,#1A1A1A 75%);background-size:200% 100%;animation:shimmer 1.5s infinite;height:90px;margin-bottom:8px;padding:10px;border-radius:8px;}
@keyframes shimmer {0% {background-position:200% 0;} 100% {background-position:-200% 0;}}
</style>
""", unsafe_allow_html=True)

# App title
st.title("🧬 BioOrbit")
st.caption("Explore NASA's 608 space biology studies — online or offline!")

# Load dataset
@st.cache_data
def load_data():
    return load_dataset("nasa_space_biology_608.csv")

df = load_data()

# Optimized article fetching
@st.cache_data(show_spinner=False, ttl=3600)
@st.cache_data(show_spinner=False, ttl=3600)
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_article_text(url):
    """Advanced scraper with fallbacks: HTML, OpenGraph, Schema.org,
       meta description, abstract divs, and PDF via DOI resolution."""

    if not url:
        return "", "no_url"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=12, allow_redirects=True)

        if response.status_code != 200:
            return "", f"http_error_{response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove junk
        for tag in ["script", "style", "nav", "footer", "header", "iframe", "aside"]:
            for t in soup.find_all(tag):
                t.decompose()

        # --------------------------
        # 1️⃣ Extract OpenGraph description
        # --------------------------
        og = soup.find("meta", property="og:description")
        if og and og.get("content"):
            text = og["content"].strip()
            if len(text) > 40:
                return text, "og_description"

        # --------------------------
        # 2️⃣ Extract Schema.org description
        # --------------------------
        schema_desc = soup.find("meta", {"itemprop": "description"})
        if schema_desc and schema_desc.get("content"):
            text = schema_desc["content"].strip()
            if len(text) > 40:
                return text, "schema_description"

        # --------------------------
        # 3️⃣ Meta description fallback
        # --------------------------
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            text = meta["content"].strip()
            if len(text) > 40:
                return text, "meta_description"

        # --------------------------
        # 4️⃣ Extract Abstract (common for journals)
        # --------------------------
        abstract_labels = ["abstract", "article__abstract", "section--abstract"]

        for cls in abstract_labels:
            abstract_div = soup.find("div", class_=cls)
            if abstract_div:
                text = abstract_div.get_text(" ", strip=True)
                if len(text) > 40:
                    return text, "abstract_div"

        # Generic "abstract" tag name
        abs_tag = soup.find("abstract")
        if abs_tag:
            t = abs_tag.get_text(" ", strip=True)
            if len(t) > 40:
                return t, "abstract_tag"

        # --------------------------
        # 5️⃣ Extract paragraphs normally
        # --------------------------
        paragraphs = soup.find_all("p")
        extracted = [
            p.get_text(" ", strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 20
        ]

        if extracted:
            text = " ".join(extracted)
            if len(text) > 200:
                return text[:8000], "html_paragraphs"

        # --------------------------
        # 6️⃣ DOI → Fetch PDF or abstract automatically
        # --------------------------
        doi_meta = soup.find("meta", attrs={"name": "citation_doi"})
        if doi_meta:
            doi = doi_meta.get("content", "").strip()
            if doi:
                pdf_link = f"https://doi.org/{doi}"
                try:
                    doi_res = requests.get(pdf_link, headers=headers, timeout=10)
                    if doi_res.status_code == 200:
                        # try to detect text inside the redirect page
                        doi_soup = BeautifulSoup(doi_res.text, "html.parser")
                        abstract = doi_soup.find("section", {"id": "Abs1-content"})
                        if abstract:
                            t = abstract.get_text(" ", strip=True)
                            if len(t) > 40:
                                return t, "doi_resolved_abstract"
                except:
                    pass

        # --------------------------
        # 7️⃣ Last fallback – extract large text blocks
        # --------------------------
        blocks = soup.find_all("div")
        text_chunks = [
            d.get_text(" ", strip=True)
            for d in blocks
            if len(d.get_text(strip=True)) > 50
        ]

        if text_chunks:
            combined = " ".join(text_chunks)
            if len(combined) > 200:
                return combined[:8000], "large_blocks"

        # --------------------------
        # 8️⃣ If still empty
        # --------------------------
        return "", "insufficient"

    except Exception as e:
        print("SCRAPER ERROR:", e)
        return "", "error"


def get_content_for_summary(content, content_source, link, article_id):
    if content and len(content.strip())>500 and content_source!="title_only": return content, "dataset", len(content)
    if article_id in st.session_state.fetched_content:
        cached_text, cached_status = st.session_state.fetched_content[article_id]
        if cached_text and len(cached_text)>100: return cached_text, cached_status, len(cached_text)
    if link:
        fetched_text,status=fetch_article_text(link)
        st.session_state.fetched_content[article_id]=(fetched_text,status)
        if fetched_text and len(fetched_text)>100: return fetched_text,status,len(fetched_text)
    return content, content_source, len(content) if content else 0

def generate_summary_cached(article_text, article_id, api_key):
    if article_id in st.session_state.summaries: return st.session_state.summaries[article_id], True
    summary = summarize_text(article_text, api_key)
    st.session_state.summaries[article_id] = summary
    return summary, False

# Search bar
query = st.text_input("Search NASA Space Biology Studies", placeholder="e.g., microgravity, radiation, plants...", value=st.session_state.query, key="search_input")
if query != st.session_state.query:
    st.session_state.query = query
    st.session_state.summarizing = {}

# Perform search
if st.session_state.query:
    try:
        with st.spinner("Searching NASA database..."):
            results = search_publications(st.session_state.query, df)
        if results.empty: st.warning("No results found.")
        else:
            st.success(f"Found {len(results)} studies for '{st.session_state.query}'")
            st.markdown("---")
            for i, row in enumerate(results.itertuples(), start=1):
                title=row.title
                link=getattr(row,"link","")
                content=getattr(row,"content","")
                content_source=getattr(row,"content_source","")
                article_id=f"{st.session_state.query}_{i}_{hashlib.md5(title.encode()).hexdigest()[:8]}"
                st.markdown(f"""
                    <div class="result-card">
                        <h4>{i}. {title}</h4>
                        {"<a href='" + link + "' target='_blank' class='link-button'>🔗 View Publication</a>" if link else ""}
                    </div>
                """, unsafe_allow_html=True)
                summarize_button = st.button(f"✨ Summarize Article {i}", key=f"summarize_{i}")
                if summarize_button: st.session_state.summarizing[i]=True
                if st.session_state.summarizing.get(i, False):
                    if not api_key:
                        st.markdown("""<div class="warning-box">⚠️ <strong>API Key Required</strong><br>Please provide your GROQ API key in the .env file.</div>""", unsafe_allow_html=True)
                    else:
                        if article_id in st.session_state.summaries:
                            summary=st.session_state.summaries[article_id]
                            st.markdown(f"<div style='background-color:#1A1A1A;padding:15px;border-radius:8px;border-left:4px solid #6BE6C1;margin-bottom:15px;'><h5 style='color:#6BE6C1;'>📝 AI Summary <span style='font-size:0.8em;color:#999;'>(cached)</span></h5><p style='color:#FFFFFF;line-height:1.6;'>{summary}</p></div>", unsafe_allow_html=True)
                        else:
                            summary_placeholder=st.empty()
                            with summary_placeholder.container():
                                st.markdown("""<div class="loading-shimmer"><p style="color:#999;">⏳ Generating summary...</p></div>""", unsafe_allow_html=True)
                            article_text, source_status, char_count = get_content_for_summary(content, content_source, link, article_id)
                            if char_count>=100:
                                try:
                                    optimized_text = article_text[:6000]
                                    summary, _ = generate_summary_cached(optimized_text, article_id, api_key)
                                    with summary_placeholder.container():
                                        st.markdown(f"<div style='background-color:#1A1A1A;padding:15px;border-radius:8px;border-left:4px solid #6BE6C1;margin-bottom:15px;'><h5 style='color:#6BE6C1;'>📝 AI Summary <span style='font-size:0.75em;color:#999;'>({char_count} chars)</span></h5><p style='color:#FFFFFF;line-height:1.6;'>{summary}</p></div>", unsafe_allow_html=True)
                                except Exception as e:
                                    with summary_placeholder.container():
                                        st.markdown(f"<div class='warning-box'>❌ Summary Generation Failed<br>Error: {str(e)}</div>", unsafe_allow_html=True)
                            else:
                                with summary_placeholder.container():
                                    st.markdown(f"<div style='background-color:#1E2128;padding:15px;border-radius:8px;border-left:4px solid #FFA500;margin-bottom:15px;'><h5 style='color:#FFA500;'>📄 Basic Information</h5><p style='color:#CCC;'><strong>Title:</strong> {title}</p>{f'<p style=color:#CCC;><strong>Available text:</strong> {article_text[:200]}</p>' if article_text else ''}<p style='color:#999;font-size:0.9em;margin-top:10px;'>⚠️ Limited content ({char_count} characters). Visit the link for full details.</p></div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Search Error: {e}")

# Footer
st.markdown("---")
st.caption("Built with ❤️ for Space Biology Research | Dataset: NASA Space Biology Studies")
