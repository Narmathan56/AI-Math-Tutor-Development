import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

import sys

sys.stdout.reconfigure(encoding="utf-8")

# Load .env beside this file.
load_dotenv(Path(__file__).with_name(".env"))

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is missing")

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    messages=[
        {
            "role": "user",
            "content": "Solve 2*x + 3 = 7. Give two short steps."
        }
    ],
)

print(response.choices[0].message.content)