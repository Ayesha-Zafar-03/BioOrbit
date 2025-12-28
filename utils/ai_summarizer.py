import requests

def summarize_text(text):
    if not GROQ_API_KEY:
        return "❌ GROQ API key missing."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "Summarize this NASA space biology research in clear academic language."},
            {"role": "user", "content": text}
        ],
        "temperature": 0.3,
        "max_tokens": 200   # 🔥 REQUIRED
    }

    r = requests.post(url, headers=headers, json=payload, timeout=30)

    # 🔍 SHOW REAL ERROR
    if r.status_code != 200:
        return f"❌ Groq API Error {r.status_code}: {r.text}"

    return r.json()["choices"][0]["message"]["content"]
