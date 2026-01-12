import requests

HF_MODEL = "facebook/bart-large-cnn"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

def summarize_text(text):
    """
    Generate AI summary using HuggingFace Inference API
    and show full error if it fails.
    """
    if not HF_API_KEY:
        return "❌ HuggingFace API key missing."

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": text[:3000],  # HF input limit
        "parameters": {
            "max_length": 150,
            "min_length": 60,
            "do_sample": False
        }
    }

    try:
        r = requests.post(
            HF_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if r.status_code != 200:
            return f"❌ HF API Error {r.status_code}: {r.text}"

        result = r.json()

        if isinstance(result, dict) and result.get("error"):
            return f"❌ HF Model Error: {result['error']}"

        return result[0]["summary_text"]

    except requests.exceptions.RequestException as e:
        return f"❌ HF Request Exception: {str(e)}"
    except Exception as e:
        return f"❌ HF Unknown Error: {str(e)}"
