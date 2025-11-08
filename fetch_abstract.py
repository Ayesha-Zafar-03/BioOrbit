import requests
from bs4 import BeautifulSoup

def fetch_abstract(url):
    if not url or not url.startswith("http"):
        return ""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")

        # Example: try to find abstract by common tags
        abstract = ""
        if soup.find("div", {"class": "abstract"}):
            abstract = soup.find("div", {"class": "abstract"}).get_text(" ", strip=True)
        elif soup.find("section", {"id": "abstract"}):
            abstract = soup.find("section", {"id": "abstract"}).get_text(" ", strip=True)
        elif soup.find("p"):
            # fallback: first paragraph
            abstract = soup.find("p").get_text(" ", strip=True)

        return abstract
    except Exception as e:
        return ""
