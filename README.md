
# 🚀 BioOrbit: Space Biology Knowledge Engine

**BioOrbit** is an AI-powered dashboard built for NASA’s HackHers challenge: _“Enable a new era of human space exploration!”_ Our mission was to create a dynamic knowledge engine that helps users explore decades of NASA’s space biology research—making it accessible, insightful, and actionable as humanity prepares to revisit the Moon and venture to Mars.

## 🌌 Challenge Overview

NASA has conducted thousands of biology experiments in space, generating a vast trove of bioscience publications. While this data is publicly available, it’s often difficult to navigate and extract relevant insights. Our challenge was to:

> 🔬 **Build a dynamic dashboard** using AI, knowledge graphs, and other tools to summarize NASA bioscience publications and help users explore the impacts and results of space biology experiments.

This project was developed under NASA’s **Earth Science Division** during the HackHers hackathon.

## 🧠 What BioOrbit Does

- 📚 **Summarizes NASA bioscience publications** using NLP and vector embeddings.
- 🔍 **Enables semantic search** so users can find research relevant to their interests.
- 📊 **Visualizes biological trends and experiment outcomes** through interactive graphs.
- ⚡ **Accelerates discovery** with a caching system for enriched summaries.

## 🧬 Key Features

- **Abstract Fetching**: Pulls data from NASA’s space biology dataset.
- **AI Enrichment**: Uses NLP to summarize and enhance publication abstracts.
- **Knowledge Graph Integration** *(planned)*: Maps relationships between experiments, organisms, and outcomes.
- **Interactive Dashboard**: Presents insights in a clean, intuitive interface.
- **Smart Caching**: Stores enriched summaries for faster access.

## 📁 Project Structure

```
BioOrbit-HackHers/
├── app.py                   # Main dashboard logic
├── fetch_abstract.py        # NASA abstract retrieval
├── enrich_for_grok.py       # NLP enrichment pipeline
├── vectorestore.py          # Vector search and storage
├── nasa_space_biology_608.csv          # Raw dataset
├── nasa_space_biology_608_enriched.csv # Enriched dataset
├── summary_cache.json       # Cached summaries
├── temp_graph.html          # Graph visualization
├── requirements.txt         # Dependencies
├── lib/                     # Supporting libraries
├── utils/                   # Utility functions
└── venv/                    # Virtual environment
```

## ⚙️ Getting Started

1. **Clone the repo**:
   ```bash
   git clone https://github.com/Ayesha-Zafar-03/BioOrbit-HackHers.git
   cd BioOrbit-HackHers
   ```

2. **Set up environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**:
   ```bash
   python app.py
   ```

## 🛰️ Dataset

We used NASA’s publicly available **Space Biology Publication Dataset**, which includes hundreds of experiments conducted aboard the ISS and other missions. The dataset was enriched using AI to extract key findings and biological impacts.

## 🛠️ Tech Stack

- Python
- Flask
- Pandas
- spaCy / Transformers
- HTML/CSS
- Vector embeddings

## 🏆 Hackathon

Built for the **NASA HackHers Challenge** under the theme:  
> _“Build a Space Biology Knowledge Engine”_

## 👩‍🚀 Future Directions

- 🌐 Integrate real-time NASA APIs
- 🧠 Expand knowledge graph capabilities
- 📈 Add more visualization layers
- 🧪 Enable experiment-level drilldowns

## 📬 Contact

Created by [Ayesha-Zafar-03](https://github.com/Ayesha-Zafar-03).  
For questions or collaboration, feel free to open an issue or reach out via GitHub.
