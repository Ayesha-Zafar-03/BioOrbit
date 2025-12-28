import requests
def summarize_text(text):
    """
    Generate an AI summary of the given NASA abstract using Groq API.

    - Requires GROQ_API_KEY in Streamlit Secrets.
    - Truncates text if too long for API.
    - Returns either the summary or a clear error message.
    """
    if not GROQ_API_KEY:
        return "❌ GROQ API key missing. Please add it in Streamlit Secrets."

    # Limit text to 6000 chars to avoid API errors
    truncated_text = text[:6000]

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "Summarize this NASA space biology research in clear academic language."},
            {"role": "user", "content": truncated_text}
        ],
        "temperature": 0.3,
        "max_tokens": 200
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)

        # If API fails, show **full error** for debugging
        if r.status_code != 200:
            return f"❌ Groq API Error {r.status_code}: {r.text}"

        response_json = r.json()

        # Check if choices exist
        choices = response_json.get("choices", [])
        if not choices:
            return "❌ Groq API Error: No choices returned."

        return choices[0]["message"]["content"]

    except requests.exceptions.RequestException as e:
        return f"❌ Groq Request Exception: {str(e)}"
    except Exception as e:
        return f"❌ Groq Unknown Error: {str(e)}"
