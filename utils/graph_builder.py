"""
Graph Builder for NASA Space Biology Explorer
Save this as: utils/graph_builder.py
"""

import pandas as pd
import networkx as nx
from pyvis.network import Network
import os
from collections import Counter


def build_graph(df, query, max_nodes=20):
    """
    Build an interactive network graph showing relationships between papers

    Args:
        df: Full dataset DataFrame
        query: Search query string
        max_nodes: Maximum number of nodes to display (default: 20)

    Returns:
        str: Path to the generated HTML file
    """

    # Filter relevant papers based on query
    query_lower = query.lower()

    # Search in title, abstract, and keywords
    mask = df['title'].str.lower().str.contains(query_lower, na=False)
    if 'abstract' in df.columns:
        mask = mask | df['abstract'].str.lower().str.contains(query_lower, na=False)
    if 'keywords' in df.columns:
        mask = mask | df['keywords'].str.lower().str.contains(query_lower, na=False)

    relevant_papers = df[mask].head(max_nodes)

    if relevant_papers.empty:
        # Create empty graph with message
        net = Network(height="600px", width="100%", bgcolor="#F8F9FA", font_color="#333")
        net.add_node(0, label="No papers found for this query", color="#FF6B6B", size=30)

        output_path = "temp_graph.html"
        net.save_graph(output_path)
        return output_path

    # Create NetworkX graph
    G = nx.Graph()

    # Add paper nodes
    for idx, row in relevant_papers.iterrows():
        paper_id = f"paper_{idx}"
        title = row.get('title', 'Unknown')[:60]
        year = row.get('year', 'N/A')
        citations = row.get('citations', 0)
        authors = row.get('authors', 'Unknown')

        # Node properties
        node_label = f"{title}\n({year})"
        node_size = 15 + min(int(citations) / 10, 30) if pd.notna(citations) else 15

        G.add_node(paper_id,
                   label=node_label,
                   title=f"<b>{row.get('title', 'Unknown')}</b><br>Year: {year}<br>Citations: {citations}<br>Authors: {authors[:100]}",
                   size=node_size,
                   color='#FF6B6B')

    # Extract and add author nodes
    author_papers = {}

    for idx, row in relevant_papers.iterrows():
        paper_id = f"paper_{idx}"
        authors = row.get('authors', '')

        if pd.notna(authors) and authors:
            # Parse authors
            author_list = []
            for sep in [',', ';', '|']:
                if sep in str(authors):
                    author_list = [a.strip() for a in str(authors).split(sep)]
                    break
            if not author_list:
                author_list = [str(authors).strip()]

            # Take first 3 authors to avoid clutter
            for author in author_list[:3]:
                if author:
                    author_clean = author[:30]  # Truncate long names

                    if author_clean not in author_papers:
                        author_papers[author_clean] = []
                    author_papers[author_clean].append(paper_id)

    # Add author nodes and edges
    for author, papers in author_papers.items():
        if len(papers) >= 1:  # Only add authors with at least 1 paper
            author_id = f"author_{author}"

            # Calculate author node size based on number of papers
            author_size = 12 + len(papers) * 5

            G.add_node(author_id,
                       label=author,
                       title=f"<b>Author:</b> {author}<br><b>Papers:</b> {len(papers)}",
                       size=author_size,
                       color='#4ECDC4')

            # Connect author to papers
            for paper in papers:
                G.add_edge(author_id, paper, color='#CCCCCC')

    # Add co-authorship edges between papers
    paper_nodes = [n for n in G.nodes() if n.startswith('paper_')]
    for i, paper1 in enumerate(paper_nodes):
        for paper2 in paper_nodes[i + 1:]:
            # Check if papers share authors
            authors1 = set([a for a, papers in author_papers.items() if paper1 in papers])
            authors2 = set([a for a, papers in author_papers.items() if paper2 in papers])

            shared_authors = authors1.intersection(authors2)
            if shared_authors:
                G.add_edge(paper1, paper2, color='#E8E8E8', width=0.5)

    # Create PyVis network
    net = Network(height="600px",
                  width="100%",
                  bgcolor="#F8F9FA",
                  font_color="#333",
                  notebook=False)

    # Configure physics
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 150,
                "springConstant": 0.04,
                "damping": 0.09,
                "avoidOverlap": 0.1
            },
            "minVelocity": 0.75,
            "stabilization": {
                "enabled": true,
                "iterations": 200
            }
        },
        "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true
        },
        "nodes": {
            "font": {
                "size": 12
            }
        },
        "edges": {
            "smooth": {
                "type": "continuous"
            }
        }
    }
    """)

    # Convert NetworkX graph to PyVis
    net.from_nx(G)

    # Save graph
    output_path = "temp_graph.html"
    net.save_graph(output_path)

    # Add custom styling to the HTML
    with open(output_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Add title and styling
    custom_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Knowledge Graph: {query}</title>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                background-color: #F8F9FA;
            }}
            .header {{
                text-align: center;
                margin-bottom: 20px;
                padding: 15px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header h2 {{
                margin: 0;
                color: #333;
                font-size: 22px;
            }}
            .legend {{
                display: flex;
                justify-content: center;
                gap: 30px;
                margin-top: 10px;
                font-size: 14px;
                color: #666;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .legend-dot {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
            }}
            #mynetwork {{
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                background: white;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>📊 Knowledge Graph: {query.title()}</h2>
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-dot" style="background-color: #FF6B6B;"></div>
                    <span>Research Papers</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot" style="background-color: #4ECDC4;"></div>
                    <span>Authors</span>
                </div>
            </div>
        </div>
        {html_content.split('<body>')[1]}
    </body>
    </html>
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(custom_html)

    return output_path


def build_simple_graph(df, query):
    """
    Simpler version without author nodes - just paper relationships
    """
    query_lower = query.lower()

    # Filter papers
    mask = df['title'].str.lower().str.contains(query_lower, na=False)
    if 'abstract' in df.columns:
        mask = mask | df['abstract'].str.lower().str.contains(query_lower, na=False)

    relevant_papers = df[mask].head(15)

    if relevant_papers.empty:
        return build_graph(df, query)  # Fallback to main function

    # Create network
    net = Network(height="600px", width="100%", bgcolor="#F8F9FA", font_color="#333")

    # Add nodes
    for idx, row in relevant_papers.iterrows():
        title = row.get('title', 'Unknown')[:50]
        year = row.get('year', 'N/A')
        citations = int(row.get('citations', 0)) if pd.notna(row.get('citations')) else 0

        node_size = 15 + min(citations / 10, 25)

        net.add_node(idx,
                     label=f"{title}\n({year})",
                     title=f"<b>{row.get('title', 'Unknown')}</b><br>Citations: {citations}",
                     size=node_size,
                     color='#FF6B6B')

    # Add edges between papers with similar keywords/topics
    papers_list = relevant_papers.to_dict('records')
    for i, paper1 in enumerate(papers_list):
        for j, paper2 in enumerate(papers_list[i + 1:], start=i + 1):
            # Simple similarity check
            title1 = str(paper1.get('title', '')).lower()
            title2 = str(paper2.get('title', '')).lower()

            # Count common words
            words1 = set(title1.split())
            words2 = set(title2.split())
            common = words1.intersection(words2)

            if len(common) >= 2:  # At least 2 common words
                net.add_edge(relevant_papers.index[i],
                             relevant_papers.index[j],
                             color='#DDDDDD')

    output_path = "temp_graph.html"
    net.save_graph(output_path)

    return output_path