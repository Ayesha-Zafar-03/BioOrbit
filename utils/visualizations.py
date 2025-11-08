"""
Visualization utilities for NASA Space Biology Explorer
Save this as: utils/visualizations.py
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
import networkx as nx
from collections import Counter


def generate_topic_network(df, query, results):
    """
    Generate an interactive author-paper network visualization

    Args:
        df: Full dataset DataFrame
        query: Search query string
        results: Filtered search results DataFrame

    Returns:
        Plotly Figure object
    """

    # Extract relevant data from results
    authors_list = []
    papers_data = []

    for idx, row in results.head(15).iterrows():  # Limit to top 15 papers
        title = row.get('title', 'Unknown')
        authors = row.get('authors', '')
        citations = row.get('citations', 0)
        year = row.get('year', 2020)

        # Parse authors (assuming comma-separated or semicolon-separated)
        if pd.notna(authors) and authors:
            # Split by common separators
            author_names = []
            for sep in [',', ';', '|']:
                if sep in str(authors):
                    author_names = [a.strip() for a in str(authors).split(sep)]
                    break
            if not author_names:
                author_names = [str(authors).strip()]

            authors_list.extend(author_names)

            papers_data.append({
                'title': title,
                'authors': author_names[:5],  # Max 5 authors per paper
                'citations': int(citations) if pd.notna(citations) else 0,
                'year': int(year) if pd.notna(year) else 2020
            })

    if not papers_data:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for network visualization",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig

    # Create network graph
    G = nx.Graph()

    # Add nodes for papers and authors
    for i, paper in enumerate(papers_data):
        paper_node = f"📄_{i}"
        G.add_node(paper_node,
                   type='paper',
                   label=paper['title'][:40] + '...' if len(paper['title']) > 40 else paper['title'],
                   full_title=paper['title'],
                   citations=paper['citations'],
                   year=paper['year'])

        # Connect authors to papers
        for author in paper['authors']:
            if author:  # Skip empty authors
                author_clean = author[:30]  # Truncate long names
                G.add_node(author_clean, type='author', label=author_clean)
                G.add_edge(author_clean, paper_node)

    # Generate layout
    try:
        pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
    except:
        pos = nx.random_layout(G, seed=42)

    # Separate nodes by type
    paper_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'paper']
    author_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'author']

    # Create edge trace
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.8, color='#DDD'),
        hoverinfo='none',
        mode='lines',
        showlegend=False)

    # Create author nodes trace
    author_x = [pos[node][0] for node in author_nodes]
    author_y = [pos[node][1] for node in author_nodes]
    author_text = [G.nodes[node]['label'] for node in author_nodes]

    # Count collaborations per author
    author_connections = [G.degree(node) for node in author_nodes]
    author_sizes = [10 + conn * 3 for conn in author_connections]

    author_trace = go.Scatter(
        x=author_x, y=author_y,
        mode='markers+text',
        marker=dict(
            size=author_sizes,
            color='#4ECDC4',
            line=dict(width=2, color='white'),
            opacity=0.8
        ),
        text=author_text,
        textposition="top center",
        textfont=dict(size=9, color='#333'),
        hoverinfo='text',
        hovertext=[f"<b>Author:</b> {name}<br><b>Collaborations:</b> {conn}"
                   for name, conn in zip(author_text, author_connections)],
        name='Authors'
    )

    # Create paper nodes trace
    paper_x = [pos[node][0] for node in paper_nodes]
    paper_y = [pos[node][1] for node in paper_nodes]
    paper_labels = [G.nodes[node]['label'] for node in paper_nodes]
    paper_titles = [G.nodes[node]['full_title'] for node in paper_nodes]
    paper_citations = [G.nodes[node].get('citations', 0) for node in paper_nodes]
    paper_years = [G.nodes[node].get('year', 'N/A') for node in paper_nodes]

    # Normalize citation sizes
    max_citations = max(paper_citations) if max(paper_citations) > 0 else 1
    paper_sizes = [25 + (c / max_citations) * 40 for c in paper_citations]

    paper_trace = go.Scatter(
        x=paper_x, y=paper_y,
        mode='markers',
        marker=dict(
            size=paper_sizes,
            color='#FF6B6B',
            line=dict(width=2, color='white'),
            opacity=0.7
        ),
        hoverinfo='text',
        hovertext=[f"<b>{title}</b><br>Year: {year}<br>Citations: {cit}"
                   for title, year, cit in zip(paper_titles, paper_years, paper_citations)],
        name='Papers'
    )

    # Create figure
    fig = go.Figure(data=[edge_trace, author_trace, paper_trace],
                    layout=go.Layout(
                        title=dict(
                            text=f'Author-Paper Network: {query.title()} Studies',
                            font=dict(size=18, color='#333'),
                            x=0.5,
                            xanchor='center'
                        ),
                        showlegend=True,
                        hovermode='closest',
                        margin=dict(b=40, l=40, r=40, t=80),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        plot_bgcolor='#F8F9FA',
                        paper_bgcolor='white',
                        legend=dict(
                            x=0.02,
                            y=0.98,
                            bgcolor='rgba(255,255,255,0.9)',
                            bordercolor='#DDD',
                            borderwidth=1,
                            font=dict(size=11)
                        ),
                        height=600
                    ))

    return fig


def generate_citation_impact_scatter(df, query, results):
    """
    Generate a scatter plot showing research focus vs impact
    """

    if results.empty or len(results) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for impact analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig

    # Extract data
    papers = []
    for idx, row in results.head(20).iterrows():
        title = row.get('title', 'Unknown')
        citations = row.get('citations', 0)
        year = row.get('year', 2020)
        authors = row.get('authors', '')
        abstract = row.get('abstract', '')

        # Calculate a "research focus" score based on abstract relevance
        # This uses query term frequency as a proxy for focus
        focus_score = 1.0
        if pd.notna(abstract) and abstract:
            query_terms = query.lower().split()
            abstract_lower = abstract.lower()
            matches = sum(abstract_lower.count(term) for term in query_terms)
            focus_score = min(1 + matches * 0.5, 5)  # Scale 1-5
        else:
            focus_score = np.random.uniform(1.5, 4)  # Random if no abstract

        num_authors = 1
        if pd.notna(authors) and authors:
            num_authors = len([a for a in str(authors).replace(';', ',').split(',') if a.strip()])

        papers.append({
            'title': title[:60] + '...' if len(title) > 60 else title,
            'citations': int(citations) if pd.notna(citations) else 0,
            'focus': focus_score,
            'year': int(year) if pd.notna(year) else 2020,
            'num_authors': num_authors
        })

    df_plot = pd.DataFrame(papers)

    # Determine cluster (high vs low impact)
    median_citations = df_plot['citations'].median()
    df_plot['cluster'] = df_plot['citations'].apply(
        lambda x: f'High Impact ({query.title()})' if x >= median_citations else 'Collaborators/Emerging'
    )

    # Create scatter plot
    fig = go.Figure()

    # High impact cluster
    high_impact = df_plot[df_plot['cluster'] == f'High Impact ({query.title()})']
    if not high_impact.empty:
        fig.add_trace(go.Scatter(
            x=high_impact['focus'],
            y=high_impact['citations'],
            mode='markers',
            marker=dict(
                size=high_impact['num_authors'] * 8 + 15,
                color='#FF6B6B',
                opacity=0.65,
                line=dict(width=2, color='white')
            ),
            text=high_impact['title'],
            customdata=high_impact[['year', 'num_authors']],
            hovertemplate='<b>%{text}</b><br>Citations: %{y}<br>Focus Score: %{x:.1f}<br>Year: %{customdata[0]}<br>Authors: %{customdata[1]}<extra></extra>',
            name=f'High Impact Cluster'
        ))

    # Collaborators/Lower impact
    low_impact = df_plot[df_plot['cluster'] == 'Collaborators/Emerging']
    if not low_impact.empty:
        fig.add_trace(go.Scatter(
            x=low_impact['focus'],
            y=low_impact['citations'],
            mode='markers',
            marker=dict(
                size=low_impact['num_authors'] * 8 + 15,
                color='#4ECDC4',
                opacity=0.65,
                line=dict(width=2, color='white')
            ),
            text=low_impact['title'],
            customdata=low_impact[['year', 'num_authors']],
            hovertemplate='<b>%{text}</b><br>Citations: %{y}<br>Focus Score: %{x:.1f}<br>Year: %{customdata[0]}<br>Authors: %{customdata[1]}<extra></extra>',
            name='Emerging Research'
        ))

    fig.update_layout(
        title=dict(
            text=f'Research Impact Analysis: {query.title()} Studies',
            font=dict(size=18, color='#333'),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title='Research Focus Score (Query Relevance)',
        yaxis_title='Impact (Citations)',
        plot_bgcolor='#F8F9FA',
        paper_bgcolor='white',
        hovermode='closest',
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#DDD',
            borderwidth=1,
            font=dict(size=11)
        ),
        font=dict(size=12, color='#666'),
        height=550,
        margin=dict(b=60, l=60, r=40, t=80)
    )

    fig.add_annotation(
        text="Bubble size = Number of authors",
        xref="paper", yref="paper",
        x=0.98, y=-0.12, showarrow=False,
        font=dict(size=10, color="gray"),
        xanchor='right'
    )

    return fig


def generate_timeline_visualization(df, query, results):
    """
    Generate a timeline showing publications over years
    """

    if results.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No timeline data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig

    # Filter valid years
    results_with_year = results[results['year'].notna()].copy()
    results_with_year['year'] = results_with_year['year'].astype(int)

    # Group by year
    year_counts = results_with_year.groupby('year').size().reset_index(name='count')
    year_counts = year_counts.sort_values('year')

    # Calculate cumulative
    year_counts['cumulative'] = year_counts['count'].cumsum()

    fig = go.Figure()

    # Publications per year (bars)
    fig.add_trace(go.Bar(
        x=year_counts['year'],
        y=year_counts['count'],
        name='Publications per Year',
        marker=dict(color='#6BE6C1', opacity=0.7),
        hovertemplate='Year: %{x}<br>Publications: %{y}<extra></extra>'
    ))

    # Cumulative line
    fig.add_trace(go.Scatter(
        x=year_counts['year'],
        y=year_counts['cumulative'],
        name='Cumulative Publications',
        mode='lines+markers',
        line=dict(color='#FF6B6B', width=3),
        marker=dict(size=8, color='#FF6B6B', line=dict(width=2, color='white')),
        yaxis='y2',
        hovertemplate='Year: %{x}<br>Total: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(
            text=f'Publication Timeline: {query.title()} Research',
            font=dict(size=18, color='#333'),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title='Year',
        yaxis_title='Publications per Year',
        yaxis2=dict(
            title='Cumulative Publications',
            overlaying='y',
            side='right'
        ),
        plot_bgcolor='#F8F9FA',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#DDD',
            borderwidth=1,
            font=dict(size=11)
        ),
        font=dict(size=12, color='#666'),
        height=500,
        margin=dict(b=60, l=60, r=60, t=80)
    )

    return fig