import requests

def summarize_text(text, api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {
                "role": "system",
                "content": "Summarize the following NASA space biology research abstract in clear academic language."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "temperature": 0.3
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
