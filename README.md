# BioOrbit — AI-Powered NASA Research Explorer 🧬🌌

**BioOrbit** is a web app that allows users to **search, explore, and summarize NASA Space Biology research articles**. By combining **AI summarization** and a **clean Streamlit interface**, it converts complex scientific papers into **short, digestible insights**, making research accessible and actionable.

This project showcases skills in **Python, AI/ML, web app development, API integration, and UX design**.

---

## 🚀 Key Features

- 🔍 **Search NASA Space Biology Articles**  
  Find research on microgravity, radiation, stem cells, plant biology, and more via **NASA ADS API**.  

- 🤖 **AI-Powered Summaries**  
  Summarizes scientific abstracts using **HuggingFace BART model**, generating **4-bullet concise summaries** for easy reading.  

- 📊 **Interactive Dashboard**  
  Designed with **Streamlit**, featuring a sleek **dark-mode UI** and **interactive buttons** for summaries and article links.  

- ☁️ **Live Demo**  
  Hosted on Streamlit Cloud for easy demonstration and sharing.  

---

## 💻 Tech Stack

- **Language:** Python  
- **Web Framework:** Streamlit  
- **AI/ML:** HuggingFace Transformers (BART-large-cnn)  
- **Data Handling:** pandas, JSON  
- **APIs:** NASA ADS API, HuggingFace Inference API  
- **UI/UX:** Custom CSS for interactive dark-themed dashboard  

---

## 🌟 Live Demo

🔗 [BioOrbit App](https://bioorbit.streamlit.app/)  

---

## 📂 Project Structure (Highlights)

```plaintext
BioOrbit/
├─ app.py                  # Main Streamlit app
├─ utils/
│   └─ ai_summarizer.py    # AI summarization logic
├─ data/                   # (Optional) cached data
├─ summary_cache.json       # Local cache for generated summaries
├─ requirements.txt         # Python dependencies
└─ README.md
````

---

## 🎯 Skills Demonstrated

* **AI & NLP Integration:** Summarizing scientific text with HuggingFace.
* **Full-Stack Python Development:** Streamlit dashboard with interactive UI.
* **API Integration:** NASA ADS and HuggingFace APIs with proper error handling.
* **Data Management:** Local caching, session state, JSON handling for efficient performance.
* **UX/UI Design:** Dark mode dashboard with styled cards, buttons, and summaries.

---

## ▶️ How to Run Locally

1. Clone the repo:

```bash
git clone https://github.com/Ayesha-Zafar-03/BioOrbit.git
cd BioOrbit
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add your API keys in Streamlit secrets:

```
[NASA_ADS_API_KEY]
[HF_API_KEY]
```

4. Run the app:

```bash
streamlit run app.py
```

---

## 🌱 Future Enhancements

* Integrate **real-time NASA research datasets**.
* Add **visual analytics** and trends for research topics.
* Expand summaries to **full papers and experiments**.
* Implement **knowledge graphs** for advanced research navigation.

---

## 📬 Contact

Created by **Ayesha Zafar** — [GitHub Profile](https://github.com/Ayesha-Zafar-03)

✨ *BioOrbit transforms complex space biology research into actionable insights, empowering scientists, students, and AI enthusiasts.*

```

---

