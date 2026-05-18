import requests

def call_llama(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False,
                "keep_alive": "10m",
                "num_predict": 300,
                "temperature": 0.0,
                "top_p": 1.0,
                "repeat_penalty": 1.0
            },
            timeout=180
        )

        # ❌ HTTP check
        if response.status_code != 200:
            print("❌ HTTP ERROR:", response.status_code)
            print(response.text)
            return None

        # ❌ JSON safe parse
        try:
            data = response.json()
        except Exception as e:
            print("❌ JSON ERROR:", e)
            print(response.text)
            return None

        raw = data.get("response", "")

        # ❌ empty check
        if not raw or not raw.strip():
            print("❌ EMPTY RESPONSE FROM MODEL")
            print("FULL DATA:", data)
            return None

        # 🔥 CLEANING
        raw = raw.strip()
        raw = raw.replace("LLaMA executed", "")
        raw = raw.replace("```json", "").replace("```", "")

        return raw.strip()

    except Exception as e:
        print("🔥 REQUEST FAILED:", str(e))
        return None