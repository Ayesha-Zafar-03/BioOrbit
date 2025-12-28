import requests

def generate_summary(text):
    if not GROQ_API_KEY:
        return "❌ GROQ API key missing."

    try:
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Summarize scientific text clearly."},
                {"role": "user", "content": text}
            ],
            temperature=0.4,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"❌ AI Error: {str(e)}"

