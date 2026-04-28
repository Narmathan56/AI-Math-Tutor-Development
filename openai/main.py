from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import re
from dotenv import load_dotenv
from google import genai
from Services.ValidationChecker import validate_solution,normalize_math_input
from Services.problemTypeDetector import detect_problem_type
from Services.Load_Model import call_llama
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("OPEN_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# =========================
# INPUT MODEL
# =========================
class Question(BaseModel):
    question: str


# =========================
# PROMPT
# =========================
ARITHMETIC_PROMPT = """
You are a mathematical reasoning engine that outputs STRICT JSON.

IMPORTANT:
You must follow ALL rules exactly. No extra text allowed.

-----------------------
TASK
-----------------------
Solve the given math problem and return:
1. Step-by-step reasoning
2. Final correct answer

-----------------------
RULES
-----------------------
- Do NOT include any explanation outside JSON
- Do NOT write any text before or after JSON
- Do NOT modify the original equation structure
- Do NOT skip any solutions (very important)
- If ± appears, expand into separate values
- Before moving to next step:
   - ensure expression expands back to original equation exactly
- Keep all steps logically correct and consistent

-----------------------
OUTPUT FORMAT (STRICT)
-----------------------
Return ONLY valid JSON:

{
  "steps": [
    {"text": "Step 1 explanation"},
    {"text": "Step 2 explanation"}
  ],
  "final_answer": "complete answer"
}

-----------------------
EXAMPLES
-----------------------

Arithmetic:
Input: 2 + 3
Output:
{
  "steps": [
    {"text": "Add numbers 2 and 3"}
  ],
  "final_answer": "5"
}

Equation:
Input: x^2 - 9 = 0
Output:
{
  "steps": [
    {"text": "x^2 = 9"},
    {"text": "x = ±3"},
    {"text": "Solutions: -3, 3"}
  ],
  "final_answer": "-3, 3"
}
"""


# =========================
# 🔥 RESPONSE WRAPPER (IMPORTANT FIX)
# =========================
def wrap_response(type_, model_used, data):
    return {
        "type": type_,
        "model_used": model_used,
        "data": data
    }

# here we implemented the clean json file extraction function that can handle markdown and other text around the json
def extract_json(text: str):
    try:
        text = text.strip()

        # remove markdown if any
        text = text.replace("```json", "").replace("```", "").strip()

        # try direct parse first
        return json.loads(text)

    except:
        pass

    # fallback: extract JSON block
    match = re.search(r"\{[\s\S]*\}", text)

    if match:
        try:
            return json.loads(match.group())
        except:
            return None

    return None

# =========================
# 🚀 MAIN ENDPOINT
# =========================
@app.post("/solve_math")
async def solve_math(q: Question):

    model_used = "unknown"

    try:

        question = q.question.strip().lower()

        # =====================
        # GREETING HANDLER
        # =====================
        greetings = ["hi", "hello", "hey", "good morning", "good evening"]

        if question in greetings:
            return wrap_response(
                "chat",
                "system",
                {
                    "response": "Hello! I'm your AI math tutor. Send me a math question."
                }
            )

        # =====================
        # CLASSIFY INPUT
        # =====================
        problem_type = detect_problem_type(q.question)

        print("\n=== NEW REQUEST ===")
        print("Question:", q.question)
        print("Type:", problem_type)

        # =====================
        # CASE 1: MATH
        # =====================
        if problem_type in ["arithmetic", "equation"]:

            clean_question = normalize_math_input(q.question)
            prompt = ARITHMETIC_PROMPT + clean_question

            llama_output = call_llama(prompt)
            model_used = "llama"
            print("RAW OUTPUT:\n", llama_output)
            print("LLaMA executed")
            

            # ---------------------
            # SAFE JSON PARSE
            # ---------------------
            try:
                cleaned_text = llama_output.strip()

                if cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text.replace("```json", "").replace("```", "").strip()

                parsed_output = extract_json(cleaned_text)
                if parsed_output is None:
                   return wrap_response(
                    "error",
                    model_used,
                    {"reason": "extract_json returned None (invalid model output)"}
    )         
                if not isinstance(parsed_output, dict):
                    return wrap_response(
                    "error",
                     model_used,
                    {"reason": f"Invalid parsed_output type: {type(parsed_output)}"}
        )

                print("JSON valid")

            except Exception as e:
                print("JSON invalid:", e)

                # fallback safe response (NEVER crash API)
                return wrap_response(
                    "error",
                    model_used,
                    {
                        "reason": "Model returned invalid JSON"
                    }
                )

            # ---------------------
            # VALIDATION LAYER
            # ---------------------
            validation_result = validate_solution(q.question, parsed_output)

            if not validation_result["valid"]:
                return wrap_response(
                    "error",
                    model_used,
                    {
                        "reason": validation_result["reason"]
                    }
                )

            return wrap_response(
                "solution",
                model_used,
                parsed_output
            )

        # =====================
        # CASE 2: CHAT / CONCEPT
        # =====================
        else:

            llama_prompt = f"""
Rules:
- Friendly AI tutor
- Simple explanation
- Keep answer short

User: {q.question}
"""

            llama_output = call_llama(llama_prompt)
            model_used = "llama"

            print("LLaMA executed (chat)")

            return wrap_response(
                "chat",
                model_used,
                {
                    "response": llama_output.strip()
                }
            )

    # =====================
    # GLOBAL ERROR SAFETY
    # =====================
    except Exception as e:

        print("\n🔥 SERVER CRASH:", str(e))

        return wrap_response(
            "error",
            model_used,
            {
                "reason": str(e)
            }
        )      