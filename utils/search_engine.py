import pandas as pd

def load_dataset(path="nasa_space_biology_608.csv"):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df

def search_publications(query, df):
    results = df[df['title'].str.contains(query, case=False, na=False)]
    return results[['title', 'link']].head(10)
