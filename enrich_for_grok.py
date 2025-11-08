import pandas as pd
from fetch_abstract import fetch_abstract

INPUT_CSV = "sample_data/nasa_space_biology_608_sample.csv"
OUTPUT_CSV = "sample_data/nasa_space_biology_608_enriched.csv"

def enrich_csv():
    df = pd.read_csv(INPUT_CSV)

    if "Title" not in df.columns or "Link" not in df.columns:
        raise ValueError("CSV must contain 'Title' and 'Link' columns")

    abstracts = []
    for i, row in df.iterrows():
        print(f"🔎 Fetching abstract for {i+1}/{len(df)}: {row['Title']}")
        abstract = fetch_abstract(row["Link"])
        abstracts.append(abstract)

    df["Abstract"] = abstracts
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"✅ Enriched CSV saved as {OUTPUT_CSV}")

if __name__ == "__main__":
    enrich_csv()
