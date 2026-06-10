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
from Services.prompt_router import build_prompt
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
def cached_ground_truth(question: str):
    result = compute_ground_truth(question)

    if not isinstance(result, dict):
        return None

    if "answer" not in result:
        return None

    return result
def extract_final_line(text):

    lines = text.strip().splitlines()

    # check from bottom upwards
    for line in reversed(lines):

        if "x =" in line.lower():
            return line

    return text
def normalize_llm_output(data):

    # -------------------------
    # HARD CONTRACT DEFAULT
    # -------------------------
    normalized = {
        "steps": [],
        "final_answer": []
    }

    # -------------------------
    # INVALID TYPE
    # -------------------------
    if not isinstance(data, dict):
        return normalized

    # -------------------------
    # FORMAT: {step1, step2, answer}
    # -------------------------
    if "step1" in data:

        steps = []
        i = 1

        while f"step{i}" in data:
            step = data[f"step{i}"]

            if isinstance(step, dict):
                steps.append({
                    "text": step.get("solution", "")
                })

            i += 1

        normalized["steps"] = steps
        normalized["final_answer"] = data.get("answer", [])

        return normalized

    # -------------------------
    # FORMAT: standard schema
    # -------------------------
    if "steps" in data:
        normalized["steps"] = data.get("steps", [])

    if "final_answer" in data:
        normalized["final_answer"] = data.get("final_answer", [])

    # -------------------------
    # FALLBACKS
    # -------------------------
    elif "answer" in data:
        normalized["final_answer"] = data["answer"]

    elif "verified_answer" in data:
        normalized["final_answer"] = data["verified_answer"]

    return normalized
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
        print("Classified Problem Type:", problem_type)
        clean_question = normalize_math_input(q.question)
        print("Normalized Question:", clean_question)
        print("Classified Problem Type:", problem_type)

        truth = cached_ground_truth(clean_question)
        if truth is None or not isinstance(truth, dict) or "answer" not in truth:
          return wrap_response("error", "system", {
          "reason": "Invalid truth",
          "truth": str(truth)
    })
        
        print("DEBUG truth type:", type(truth))
        print("DEBUG truth value:", truth)
        
        if not isinstance(truth, dict):
            raise ValueError(f"Invalid truth type: {type(truth)}")
        route = build_prompt(problem_type, q.question, truth)
        print("pass", flush=True)

        TOTAL_REQUESTS += 1
        print("step 2 reached", flush=True)

        llama_output = call_llama(route)
        print("step 3 reached", flush=True)
        if not llama_output or llama_output.strip() == "":
          return wrap_response(
        "error",
        model_used,
        {"reason": "LLM returned empty response"}
    )
        model_used = "llama"
        print("step reached", flush=True)
        
        print("\n=== NEW REQUEST ===")
        print("Question:", q.question)
        print("Truth:", truth)
        print("RAW OUTPUT:", llama_output, flush = True)
       

        json_data = extract_json(llama_output)
        print("DEBUG json_data type:", type(json_data))
        print("DEBUG json_data value:", json_data)

        if json_data:
          parsed_output = normalize_llm_output(json_data)
        else:
          parsed_output = parse_step_output(llama_output)

        

        # fallback answer extraction
        # fallback answer extraction
        if not parsed_output.get("final_answer"):
           final_line = extract_final_line(llama_output)
           extracted_answers = parse_answers(final_line)
           parsed_output["final_answer"] = list(extracted_answers)
        ## safty fall back
        if not parsed_output["steps"] and not parsed_output["final_answer"]:
           parsed_output = {
            "steps": [],
            "final_answer": llama_output
         }
        if truth is None or not isinstance(truth, dict) or "answer" not in truth:
          return wrap_response("error", "system", {
          "reason": "Invalid truth",
          "truth": str(truth)
    })

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