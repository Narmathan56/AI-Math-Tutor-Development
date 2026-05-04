import requests

def call_llama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "num_predict": 200,
            "temperature": 0.0
        }
    )

    data = response.json()
    raw = data.get("response", "")

    # 🔥 HARD CLEAN
    raw = raw.strip()

    # remove accidental debug artifacts
    raw = raw.replace("LLaMA executed", "")
    raw = raw.replace("```json", "").replace("```", "")

    return raw.strip()


# test
if __name__ == "__main__":
    print(call_llama("Solve x^2 + 5x + 6 = 0 step by step"))