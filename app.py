import streamlit as st
import pandas as pd
from utils.search_engine import load_dataset, search_publications
from utils.ai_summarizer import summarize_text
from dotenv import load_dotenv
import os, requests, json
from bs4 import BeautifulSoup
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY", "")

# 🌑 Page settings
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

# Hide the sidebar (settings)
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True
)

# 🌌 Custom CSS
st.markdown("""
<style>
body, [data-testid="stAppViewContainer"] {
    background-color: #000000;
    color: #FFFFFF;
}
input, textarea, select {
    background-color: #2C2F36 !important;
    color: white !important;
    border-radius: 8px;
    border: 1px solid #444;
}
.stButton>button {
    background-color: #3A3F47;
    color: white;
    border-radius: 10px;
    border: 1px solid #666;
    transition: all 0.3s ease;
}
.stButton>button:hover {
    background-color: #6BE6C1;
    color: black;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(107, 230, 193, 0.3);
}
.link-button {
    display: inline-block;
    padding: 4px 10px;
    margin-left: 10px;
    background-color: #6BE6C1;
    color: black !important;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
}
.link-button:hover {
    background-color: #4ad1a5;
    transform: translateY(-1px);
}
.result-card {
    background-color: #1A1A1A;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 15px;
    border-left: 4px solid #6BE6C1;
    transition: all 0.3s ease;
}
.result-card:hover {
    background-color: #222222;
    box-shadow: 0 4px 12px rgba(107, 230, 193, 0.2);
}
.warning-box {
    background-color: #2C2F36;
    padding: 10px;
    border-radius: 6px;
    border-left: 3px solid #FFA500;
    margin: 10px 0;
}
.info-box {
    background-color: #1A1A1A;
    padding: 8px 12px;
    border-radius: 6px;
    border-left: 3px solid #6BE6C1;
    margin: 8px 0;
    font-size: 0.9em;
}
.loading-shimmer {
    background: linear-gradient(90deg, #1A1A1A 25%, #2C2F36 50%, #1A1A1A 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
</style>
""", unsafe_allow_html=True)

# 🌍 App title
st.title("🧬 BioOrbit")
st.caption("Explore NASA's 608 space biology studies — online or offline!")


# Load dataset
@st.cache_data
def load_data():
    return load_dataset("nasa_space_biology_608.csv")


df = load_data()


# Optimized article fetching with shorter timeout
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_article_text(url):
    """
    Fast article text extraction with aggressive optimization
    """
    if not url:
        return "", "no_url"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        # Reduced timeout for faster failure
        response = requests.get(url, headers=headers, timeout=8, allow_redirects=True)

        if response.status_code != 200:
            return "", f"http_error_{response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")

        # Quick removal of unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            element.decompose()

        text_content = []

        # Strategy 1: Quick check for article containers
        article_selectors = ['article', 'main', 'div[class*="content"]', 'div[class*="article"]']

        for selector in article_selectors:
            containers = soup.select(selector, limit=3)  # Limit search
            for container in containers:
                paragraphs = container.find_all('p', limit=20)  # Limit paragraphs
                if len(paragraphs) > 3:
                    text_content.extend(
                        [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])
                    if len(' '.join(text_content)) > 500:
                        break
            if len(' '.join(text_content)) > 500:
                break

        # Strategy 2: Quick fallback to all paragraphs
        if not text_content or len(' '.join(text_content)) < 300:
            paragraphs = soup.find_all('p', limit=30)
            text_content = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]

        # Join and clean
        full_text = ' '.join(text_content)
        full_text = ' '.join(full_text.split())

        # Limit to 8000 characters for faster processing
        if len(full_text) > 8000:
            full_text = full_text[:8000]
            status = "success_truncated"
        elif len(full_text) > 300:
            status = "success"
        elif len(full_text) > 100:
            status = "partial"
        else:
            status = "insufficient"

        return full_text, status

    except requests.exceptions.Timeout:
        return "", "timeout"
    except:
        return "", "error"


def get_content_for_summary(content, content_source, link, article_id):
    """
    Fast content retrieval with immediate fallback to dataset
    """
    # Priority 1: Use dataset content if good enough
    if content and len(content.strip()) > 500 and content_source != "title_only":
        return content, "dataset", len(content)

    # Priority 2: Check cache
    if article_id in st.session_state.fetched_content:
        cached_text, cached_status = st.session_state.fetched_content[article_id]
        if cached_text and len(cached_text) > 100:
            return cached_text, cached_status, len(cached_text)

    # Priority 3: Quick fetch attempt
    if link:
        fetched_text, status = fetch_article_text(link)
        st.session_state.fetched_content[article_id] = (fetched_text, status)

        if fetched_text and len(fetched_text) > 100:
            return fetched_text, status, len(fetched_text)

    # Priority 4: Use any available content
    return content, content_source, len(content) if content else 0


def generate_summary_cached(article_text, article_id, api_key):
    """
    Generate or retrieve cached summary
    """
    # Check if summary already exists
    if article_id in st.session_state.summaries:
        return st.session_state.summaries[article_id], True

    # Generate new summary
    summary = summarize_text(article_text, api_key)
    st.session_state.summaries[article_id] = summary
    return summary, False


# 🔎 Search bar
query = st.text_input("Search NASA Space Biology Studies",
                      placeholder="e.g., microgravity, radiation, plants...",
                      value=st.session_state.query,
                      key="search_input")

# Update session state when query changes
if query != st.session_state.query:
    st.session_state.query = query
    st.session_state.summarizing = {}

# Example queries
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🌱 Plant Biology"):
        st.session_state.query = "plant"
        st.session_state.summarizing = {}
        st.rerun()
with col2:
    if st.button("🧫 Microgravity"):
        st.session_state.query = "microgravity"
        st.session_state.summarizing = {}
        st.rerun()
with col3:
    if st.button("🧬 Stem Cells"):
        st.session_state.query = "stem cells"
        st.session_state.summarizing = {}
        st.rerun()


# 🔍 Perform search
if st.session_state.query:
    try:
        with st.spinner("Searching NASA database..."):
            results = search_publications(st.session_state.query, df)

        if results.empty:
            st.warning("No results found.")
        else:
            st.success(f"Found {len(results)} studies for '{st.session_state.query}'")
            st.markdown("---")

            for i, row in enumerate(results.itertuples(), start=1):
                title = row.title
                link = getattr(row, "link", "")
                content = getattr(row, "content", "")
                content_source = getattr(row, "content_source", "")

                # Create unique article ID
                article_id = f"{st.session_state.query}_{i}_{hashlib.md5(title.encode()).hexdigest()[:8]}"

                st.markdown(f"""
                    <div class="result-card">
                        <h4>{i}. {title}</h4>
                        {"<a href='" + link + "' target='_blank' class='link-button'>🔗 View Publication</a>" if link else ""}
                    </div>
                """, unsafe_allow_html=True)

                # Summarize button
                summarize_button = st.button(f"✨ Summarize Article {i}", key=f"summarize_{i}")

                if summarize_button:
                    st.session_state.summarizing[i] = True

                if st.session_state.summarizing.get(i, False):
                    if not api_key:
                        st.markdown("""
                            <div class="warning-box">
                                ⚠️ <strong>API Key Required</strong><br>
                                Please provide your GROQ API key in the .env file to generate summaries.
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Check if summary already cached
                        if article_id in st.session_state.summaries:
                            # Display cached summary immediately
                            summary = st.session_state.summaries[article_id]
                            st.markdown(f"""
                                <div style="background-color:#1A1A1A;padding:15px;border-radius:8px;
                                    border-left:4px solid #6BE6C1;margin-bottom:15px;">
                                    <h5 style="color:#6BE6C1;">📝 AI Summary <span style="font-size:0.8em;color:#999;">(cached)</span></h5>
                                    <p style="color:#FFFFFF;line-height:1.6;">{summary}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Create placeholder for loading
                            summary_placeholder = st.empty()

                            with summary_placeholder.container():
                                st.markdown("""
                                    <div class="loading-shimmer" style="padding:15px;border-radius:8px;height:100px;margin-bottom:15px;">
                                        <p style="color:#999;">⏳ Generating summary...</p>
                                    </div>
                                """, unsafe_allow_html=True)

                            # Get content quickly
                            article_text, source_status, char_count = get_content_for_summary(
                                content, content_source, link, article_id
                            )

                            should_summarize = char_count >= 100

                            if should_summarize:
                                try:
                                    # Generate summary
                                    start_time = time.time()

                                    # Optimize text for faster processing
                                    optimized_text = article_text[:6000]  # Shorter for speed

                                    summary, was_cached = generate_summary_cached(optimized_text, article_id, api_key)

                                    elapsed = time.time() - start_time

                                    # Update placeholder with actual summary
                                    with summary_placeholder.container():
                                        st.markdown(f"""
                                            <div style="background-color:#1A1A1A;padding:15px;border-radius:8px;
                                                border-left:4px solid #6BE6C1;margin-bottom:15px;">
                                                <h5 style="color:#6BE6C1;">📝 AI Summary 
                                                    <span style="font-size:0.75em;color:#999;">
                                                        ({char_count} chars • {elapsed:.1f}s)
                                                    </span>
                                                </h5>
                                                <p style="color:#FFFFFF;line-height:1.6;">{summary}</p>
                                            </div>
                                        """, unsafe_allow_html=True)

                                except Exception as e:
                                    with summary_placeholder.container():
                                        st.markdown(f"""
                                            <div class="warning-box">
                                                ❌ <strong>Summary Generation Failed</strong><br>
                                                Error: {str(e)}
                                            </div>
                                        """, unsafe_allow_html=True)
                            else:
                                # Not enough content
                                with summary_placeholder.container():
                                    st.markdown(f"""
                                        <div style="background-color:#1E2128;padding:15px;border-radius:8px;
                                            border-left:4px solid #FFA500;margin-bottom:15px;">
                                            <h5 style="color:#FFA500;">📄 Basic Information</h5>
                                            <p style="color:#CCC;"><strong>Title:</strong> {title}</p>
                                            {f'                                            <p style="color:#CCC;"><strong>Available text:</strong> {article_text[:200]}</p>' if article_text else ''}
                                            <p style="color:#999;font-size:0.9em;margin-top:10px;">
                                                ⚠️ Limited content available ({char_count} characters). Visit the publication link for full details.
                                            </p>
                                        </div>
                                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Search Error: {e}")

# Footer
st.markdown("---")
st.caption("Built with ❤️ for Space Biology Research | Dataset: NASA Space Biology Studies")

# Performance tip in sidebar (if enabled)
with st.expander("⚡ Performance Tips"):
    st.markdown("""
    **Speed Optimizations:**
    - ✅ Summaries are cached - click again for instant results
    - ✅ Reduced fetch timeout (8s vs 15s)
    - ✅ Text limited to 6000 chars for faster AI processing
    - ✅ Dataset content prioritized over web fetching

    **For best speed:**
    - Articles with dataset content are fastest
    - Cached summaries load instantly
    - Use example query buttons for quick searches
    """)
