import requests

def call_llama(prompt: str) -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False,
                "keep_alive": "10m",
                "num_predict": 120,
                "temperature": 0.0,
                "top_p": 1.0,
                "repeat_penalty": 1.0
            },
            timeout=240
        )

        # -------------------
        # HTTP CHECK
        # -------------------
        if response.status_code != 200:
            print("❌ HTTP ERROR:", response.status_code)
            print(response.text)
            return ""

        # -------------------
        # JSON PARSE SAFE
        # -------------------
        try:
            data = response.json()
        except Exception as e:
            print("❌ JSON ERROR:", e)
            print(response.text)
            return ""

        # -------------------
        # EXTRACT RESPONSE
        # -------------------
        raw = data.get("response", "")

        if not isinstance(raw, str):
            raw = str(raw)

        if not raw.strip():
            print("❌ EMPTY RESPONSE FROM MODEL")
            print("FULL DATA:", data)
            return ""

        # -------------------
        # CLEAN OUTPUT
        # -------------------
        raw = raw.strip()
        raw = raw.replace("```json", "").replace("```", "")
        raw = raw.replace("LLaMA executed", "")

        return raw.strip()

    except Exception as e:
        print("🔥 REQUEST FAILED:", str(e))
        return ""