import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_model():
    return os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


@lru_cache(maxsize=1)
def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY missing")
    return Groq(api_key=api_key)


def stream_tutor(prompt: str):
    """Yield plain text chunks to preserve the existing SSE contract."""
    response = get_client().chat.completions.create(
        model=get_model(),
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    try:
        for chunk in response:
            if not chunk.choices:
                continue
            text = chunk.choices[0].delta.content
            if text:
                yield text
    finally:
        response.close()