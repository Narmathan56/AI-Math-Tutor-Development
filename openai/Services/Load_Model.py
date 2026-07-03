import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def get_client():
    api_key = os.getenv("OPEN_API_KEY")

    if not api_key:
        raise ValueError("OPEN_API_KEY missing")

    return genai.Client(api_key=api_key)


def stream_gemini(prompt: str):
    client = get_client()

    response = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=prompt
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text