import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

CSV_PATH = "nasa_space_biology_608.csv"
VECTORSTORE_PATH = "nasa_bioscience_vectorstore"

# Entrez API base
ENTREZ_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def fetch_abstract(pmc_id: str) -> str:
    """Fetch abstract text from PubMed Central using NCBI efetch API."""
    try:
        params = {
            "db": "pmc",
            "id": pmc_id,
            "retmode": "text",
            "rettype": "abstract"
        }
        resp = requests.get(ENTREZ_FETCH_URL, params=params, timeout=20)
        resp.raise_for_status()
        return resp.text.strip()
    except Exception as e:
        print(f"❌ Could not fetch abstract for {pmc_id}: {e}")
        return ""

def build():
    print(f"📂 Loading data from: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    # Use lowercase column names to match your file
    if "title" not in df.columns or "link" not in df.columns:
        raise ValueError("CSV must contain 'title' and 'link' columns")

    docs = []
    for _, row in df.iterrows():
        title = str(row["title"])
        link = str(row["link"])

        # Extract PMC ID if available
        pmc_id = link.split("PMC")[-1].strip("/") if "PMC" in link else None
        abstract = fetch_abstract(pmc_id) if pmc_id else ""

        # Combine title + abstract (fallback: only title)
        content = f"{title}\n\n{abstract}" if abstract else title

        docs.append(Document(
            page_content=content,
            metadata={"title": title, "link": link}
        ))

    print(f"🔢 Total docs created: {len(docs)}")

    # Embeddings with sentence-transformers
    model = SentenceTransformer("all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(
        docs,
        embedding=lambda x: model.encode(x, show_progress_bar=True)
    )

    vectorstore.save_local(VECTORSTORE_PATH)
    print(f"✅ Vectorstore saved at {VECTORSTORE_PATH}")

if __name__ == "__main__":
    build()
