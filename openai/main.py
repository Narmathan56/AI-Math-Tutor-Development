from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import re

from dotenv import load_dotenv
from google import genai
from Services.ValidationChecker import validate_solution,normalize_math_input,solve
from Services.problemTypeDetector import detect_problem_type
from Services.prompt_router import route_question
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
You are a math solver.

Return JSON with:
- steps
- final_answer

Rules:
- Keep steps simple
- Be mathematically correct
- Include ALL solutions
- JSON only

case1: algebra / equations
  - Use only algebraic transformations
  - No new equations
  - Final answer must match SymPy
  - Do NOT use Greek letters

case2: statistics / probability
  - You may use standard statistical symbols (σ, μ, θ, π)
  - Use correct mathematical notation
  - Do not invent symbols not defined in problem
  - Final answer must match SymPy
case3: geometry / trig  
  - θ, π allowed
  - Use standard math notation
  - Keep steps logically consistent


Example:
{
  "steps": [{"text": "x^2 = 9"}, {"text": "x = ±3"}],
  "final_answer": "-3, 3"
}
"""
def normalize_llm_output(data):
    if not isinstance(data, dict):
        return {
            "steps": [],
            "final_answer": ""
        }

    # case 1: step1/step2 format
    if "step1" in data:
        steps = []
        i = 1

        while f"step{i}" in data:
            step = data[f"step{i}"]
            steps.append({"text": step.get("solution", "")})
            i += 1

        return {
            "steps": steps,
            "final_answer": data.get("answer", "")
        }

    return data
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
    if not text:
        return None

    text = text.strip()

    # remove markdown
    text = text.replace("```json", "").replace("```", "").strip()

    # try direct parse
    try:
        return json.loads(text)
    except:
        pass

    # try to FIX common LLM issues
    try:
        # remove trailing commas
        text = re.sub(r",\s*}", "}", text)
        text = re.sub(r",\s*]", "]", text)

        return json.loads(text)
    except:
        pass

    # fallback: extract first JSON block
    match = re.search(r"\{[\s\S]*\}", text)

    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        # last resort cleanup
        cleaned = match.group()
        cleaned = re.sub(r",\s*}", "}", cleaned)
        cleaned = re.sub(r",\s*]", "]", cleaned)

        try:
            return json.loads(cleaned)
        except:
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
        route = route_question(q.question, problem_type)

        print("\n=== NEW REQUEST ===")
        print("Question:", q.question)
        print("Type:", problem_type)

       
    
       
        llama_output = call_llama(route["prompt"])
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
                    parsed_output = {
                    "steps": [],
                    "final_answer": llama_output.strip()
                   }

                parsed_output = normalize_llm_output(parsed_output)
                
                if parsed_output is None:
                  parsed_output = {
                  "steps": [{"text": "Solution generated"}],
                  "final_answer": llama_output.strip()
    }
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