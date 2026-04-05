"""
integrations/chatgpt.py
───────────────────────
Sends a question to the OpenAI Chat API and returns the first 2 sentences
of the answer, formatted for TTS (no markdown, no asterisks).
"""

import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def _first_n_sentences(text: str, n: int = 2) -> str:
    """Split on sentence-ending punctuation and return the first n sentences."""
    # Split on . ! ? followed by whitespace or end-of-string
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    selected = sentences[:n]
    result = " ".join(selected)
    # Strip markdown artifacts
    result = re.sub(r"[*_`#]", "", result)
    return result.strip()


def ask(question: str) -> str | None:
    """
    Ask ChatGPT and return a 2-sentence answer string,
    or None if the API call fails.
    """
    prompt = f"In three sentences answer: {question}"
    try:
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.5,
        )
        full_text = response.choices[0].message.content or ""
        answer = _first_n_sentences(full_text, n=2)
        print(f"[ChatGPT] {answer}")
        return answer
    except Exception as exc:
        print(f"[ChatGPT] Error: {exc}")
        return None
