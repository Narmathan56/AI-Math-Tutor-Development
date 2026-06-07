from operator import truth

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import time

from dotenv import load_dotenv
from google import genai
from Services.ValidationChecker import validate_solution,normalize_math_input,solve,compute_ground_truth,compare_answers, parse_answers, validate_transition
from Services.problemTypeDetector import classify
from Services.prompt_router import get_system_prompt
from Services.Load_Model import call_llama
from functools import lru_cache
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("OPEN_API_KEY"))

app = FastAPI()

# =========================
# LIVE ACCURACY STATS
# =========================

TOTAL_REQUESTS = 0
CORRECT_ANSWERS = 0
FAILED_ANSWERS = 0

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

def parse_step_output(text):

    lines = text.strip().splitlines()

    steps = []
    final_answer = ""

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Step detection
        if line.lower().startswith("step"):

            steps.append({
                "text": line
            })

        # Final answer detection
        if "final step" in line.lower():
            final_answer = line

    # fallback
    if not final_answer and steps:
        final_answer = steps[-1]["text"]

    return {
        "steps": steps,
        "final_answer": final_answer
    }
@lru_cache(maxsize=1000)
def cached_ground_truth(question: str):
    return compute_ground_truth(question)

def extract_final_line(text):

    lines = text.strip().splitlines()

    # check from bottom upwards
    for line in reversed(lines):

        if "x =" in line.lower():
            return line

    return text
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

    global TOTAL_REQUESTS
    global CORRECT_ANSWERS
    global FAILED_ANSWERS

    model_used = "unknown"

    try:
        start_time = time.time()

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
        problem_type = classify(q.question.lower())
        clean_question = normalize_math_input(q.question)
        print("Normalized Question:", clean_question)

        truth = cached_ground_truth(clean_question)

        if truth is None:
            return wrap_response("error", "system", {"reason": "Cannot compute truth"})

        route = get_system_prompt(problem_type, q.question, truth)

        TOTAL_REQUESTS += 1

        llama_output = call_llama(route["prompt"])
        if not llama_output or llama_output.strip() == "":
          return wrap_response(
        "error",
        model_used,
        {"reason": "LLM returned empty response"}
    )
        model_used = "llama"

        print("\n=== NEW REQUEST ===")
        print("Question:", q.question)
        print("Truth:", truth)
        print("RAW OUTPUT:", llama_output)

        parsed_output = parse_step_output(llama_output)

        # fallback answer extraction
        if not parsed_output["final_answer"]:
            final_line = extract_final_line(llama_output)

            extracted_answers = parse_answers(final_line)

            parsed_output["final_answer"] = list(extracted_answers)

        ## safty fall back
        if not parsed_output["steps"] and not parsed_output["final_answer"]:
           parsed_output = {
            "steps": [],
            "final_answer": llama_output
         }

# =========================
# ACCURACY CHECK (IMPORTANT FIX)
# =========================


        validation_result = validate_solution(
        problem=q.question,
        data=parsed_output,
        truth=truth
        )

        is_correct = validation_result["valid"]
        if not validation_result["valid"]:
            return wrap_response(
            "error",
            model_used,
           {
            "reason": validation_result["reason"],
            "expected": truth["answer"],
            "got": parsed_output.get("final_answer")
           }
         )

        response_time = round(time.time() - start_time, 2)

        if is_correct:
            CORRECT_ANSWERS += 1
        else:
            FAILED_ANSWERS += 1

        accuracy = round((CORRECT_ANSWERS / TOTAL_REQUESTS) * 100, 2)

        print("\n===== VALIDATION RESULT =====")
        print("STATUS:", "CORRECT" if is_correct else "FAILED")
        print("TOTAL REQUESTS:", TOTAL_REQUESTS)
        print("CORRECT:", CORRECT_ANSWERS)
        print("FAILED:", FAILED_ANSWERS)
        print("ACCURACY:", f"{accuracy}%")
        print("RESPONSE TIME:", f"{response_time}s")
        print("=============================\n")

        if not is_correct:
            return wrap_response(
            "error",
            model_used,
           {
            "reason": validation_result["reason"],
            "expected": truth["answer"],
            "got": parsed_output.get("final_answer")
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