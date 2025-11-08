# BioOrbit — NASA Space Biology Studies

> **Explore NASA’s 608 Space Biology studies online with AI-powered summarization (Streamlit)**  
>
> * Data: NASA Space Biology Publication Dataset (608 studies)  
> * Features: AI-generated summaries, quick search, article-level insights  
> * Infra: Streamlit Cloud (serverless)  
> * CI/CD: GitHub Actions for deployment

---

## ✨ Features

* 🔎 **Search NASA studies** by keyword: microgravity, plant biology, stem cells, etc.  
* 📝 **AI summaries** of full articles with character count and source info  
* 📊 **Dataset prioritization**: cached summaries load instantly for repeated queries  
* 💅 **Custom UI**: responsive cards, hover effects, and modern styling  
* ☁️ **Serverless app**: fully hosted on Streamlit Cloud  
* 🛰️ **Demo online**: [BioOrbit Demo](https://bioorbit.streamlit.app/)

---

## 🗂️ Project structure (suggested)
```
BioOrbit/
├─ app.py                      # Main Streamlit app
├─ utils/
│  ├─ ai_summarizer.py         # AI summarization logic
│  └─ search_engine.py         # Dataset search and retrieval
├─ data/
│  └─ nasa_space_biology_608.csv  # NASA dataset
├─ .github/workflows/
│  └─ ci-cd.yml                # Build, test, deploy
├─ requirements.txt
├─ .env.example
└─ README.md
```
---

## 🧰 Requirements

* Python 3.10+  
* Streamlit  
* pandas, numpy, requests, beautifulsoup4, transformers, dotenv  
* Optional: ThreadPoolExecutor for faster parallel fetching

Install dependencies:

```bash
pip install -r requirements.txt
````

---

## 🔐 Environment variables

Copy `.env.example` → `.env` and fill in:

```
GROQ_API_KEY=your_api_key_here
```

> Keep your API key secret. Don’t commit `.env`.

---

## 📥 Dataset

**NASA Space Biology Dataset (608 studies):**

* Experiments aboard the ISS & other missions
* Enriched with AI-extracted key findings, biological impacts, and research insights
* Stored as `data/nasa_space_biology_608.csv`

---

## 🧪 Usage

1. Activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Run the app:

```bash
streamlit run app.py
```

3. Use the search bar or example query buttons (Plant Biology, Microgravity, Stem Cells) to explore studies.
4. Click **Summarize Article** for AI-generated summaries.

---

## 👩‍🚀 Future Directions

* 🌐 Integrate real-time NASA APIs
* 🧠 Expand knowledge graph capabilities
* 📈 Add more visualization layers
* 🧪 Enable experiment-level drilldowns

---

## ☁️ Live Demo

Access the app online: [https://bioorbit.streamlit.app/](https://bioorbit.streamlit.app/)

---

## 🚀 CI/CD with GitHub Actions

* Automatically build, test, and deploy app on commit
* Streamlit Cloud deployment configured

---

## 📬 Contact

Created by **[@Ayesha-Zafar-03](https://github.com/Ayesha-Zafar-03)**

For questions or collaboration, open an issue or reach out via GitHub.

---

## 📝 License

Choose a license (e.g., MIT) and place it in `LICENSE`.

---

## 🙌 Acknowledgements

* NASA HackHers Challenge
* Open-source maintainers of Streamlit, pandas, transformers, BeautifulSoup


