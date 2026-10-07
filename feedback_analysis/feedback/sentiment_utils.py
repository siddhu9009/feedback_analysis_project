import os
import json
import re
from textblob import TextBlob
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)



def analyze_sentiment(text: str) -> str:
    if not text or not text.strip():
        return 'neutral'

    polarity = TextBlob(text).sentiment.polarity

    if polarity > 0.1:
        return 'positive'
    elif polarity < -0.1:
        return 'negative'
    return 'neutral'



def get_sentiment_summary(answers_qs) -> dict:
    counts = {'positive': 0, 'neutral': 0, 'negative': 0}

    for answer in answers_qs:
        s = answer.sentiment or 'neutral'
        if s in counts:
            counts[s] += 1

    total = sum(counts.values())

    def pct(n):
        return round((n / total) * 100, 1) if total else 0.0

    return {
        **counts,
        'positive_pct': pct(counts['positive']),
        'neutral_pct': pct(counts['neutral']),
        'negative_pct': pct(counts['negative']),
        'total': total,
    }



def extract_json(text: str):
    """
    Fixes Groq markdown JSON issues
    """
    try:
        cleaned = re.sub(r"```json|```", "", text).strip()
        return json.loads(cleaned)
    except:
        return {
            "issues": [],
            "positives": [],
            "suggestions": []
        }


def analyze_feedback_insights(text: str) -> dict:

    if not text or not text.strip():
        return {
            'sentiment': 'neutral',
            'ai_issues': '',
            'positives': '',
            'ai_suggestions': ''
        }

    sentiment = analyze_sentiment(text)

    prompt = f"""
You are a feedback analyzer.

Return ONLY valid JSON:
{{
  "issues": ["..."],
  "positives": ["..."],
  "suggestions": ["..."]
}}

Rules:
- Works for ANY domain (school, highway, product)
- Keep points short
- No explanations

Feedback:
{text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content

        data = extract_json(content)

        return {
            'sentiment': sentiment,
            'ai_issues': "\n".join(data.get("issues", [])),
            'positives': "\n".join(data.get("positives", [])),
            'ai_suggestions': "\n".join(data.get("suggestions", [])),
        }

    except Exception as e:
        print("🔥 GROQ ERROR:", str(e)) 

        return {
            'sentiment': sentiment,
            'ai_issues': f"AI error: {str(e)}",
            'positives': '',
            'ai_suggestions': ''
        }