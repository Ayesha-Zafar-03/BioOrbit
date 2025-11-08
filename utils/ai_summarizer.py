import os
import requests

def summarize_online_groq(text, api_key):
    """Summarize text using Groq API with simpler approach."""
    if not api_key:
        return None

    try:
        url = 'https://api.groq.com/openai/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': 'llama-3.1-8b-instant',
            'messages': [
                {
                    'role': 'user',
                    'content': f"Summarize this NASA biology paper in 4 concise bullet points:\n\n{text}"
                }
            ],
            'temperature': 0.3,
            'max_tokens': 400
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        content = data['choices'][0]['message']['content'].strip()

        # Validate: Make sure it's not echoing the prompt
        if "Summarize this NASA" in content or len(content) < 50:
            return None

        return content

    except Exception as e:
        print(f"⚠️ Groq API error: {e}")
        return None


def summarize_offline(text):
    """Fallback basic summarizer."""
    try:
        from transformers import pipeline
        summarizer = pipeline('summarization', model='t5-small')
        chunk = text[:1000]
        out = summarizer(chunk, max_length=150, min_length=40, do_sample=False)
        return out[0]['summary_text']
    except:
        # Ultra-simple fallback
        sentences = [s.strip() + '.' for s in text.split('.') if len(s.strip()) > 30]
        return ' '.join(sentences[:4]) + '...' if sentences else "Summary not available."


def summarize(text, api_key=None):
    """Main summarization function."""
    if not text or len(text.strip()) < 50:
        return "Insufficient text for summarization."

    # Try online first
    if api_key:
        result = summarize_online_groq(text, api_key)
        if result:
            return result
        print("⚠️ Online summarization failed, using fallback...")

    # Fallback to offline
    return summarize_offline(text)


# Alias for backward compatibility
summarize_text = summarize


if __name__ == "__main__":
    test = """Title: Effects of Microgravity on Bone Density

    NASA studies demonstrate that astronauts experience significant bone density loss 
    during extended spaceflight missions. The rate of loss averages 1-2% per month, 
    particularly in weight-bearing bones. Researchers found that resistance exercise 
    and vitamin D supplementation help mitigate these effects."""

    result = summarize(test, os.getenv("GROQ_API_KEY"))
    print("\n=== TEST SUMMARY ===")
    print(result)
