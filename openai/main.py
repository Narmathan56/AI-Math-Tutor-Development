from operator import truth

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import time

from dotenv import load_dotenv
from google import genai
from torch import full
from Services.ValidationChecker import validate_solution,normalize_math_input,solve,compute_ground_truth,compare_answers, parse_answers, validate_transition
from Services.problemTypeDetector import classify
from Services.prompt_router import build_prompt
from Services.Load_Model import stream_gemini, get_client
from functools import lru_cache
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("OPEN_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# =========================
# LIVE ACCURACY STATS
# =========================

TOTAL_REQUESTS = 0
CORRECT_ANSWERS = 0
FAILED_ANSWERS = 0



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

    # remove markdown wrappers
    text = text.replace("```json", "").replace("```", "")

    # extract JSON block
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None

    json_str = match.group()

    # fix common LLM issues
    json_str = json_str.replace("\\(", "(").replace("\\)", ")")
    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*]", "]", json_str)

    open_braces = json_str.count("{")
    close_braces = json_str.count("}")

    if close_braces < open_braces:
        json_str += "}" * (open_braces - close_braces)
 
    try:
        return json.loads(json_str)
    except Exception as e:
        print("JSON PARSE FAILED:", e)
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

        llama_output = stream_gemini(route)
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
        print("RAW LENGTH:", len(llama_output))
        print(repr(llama_output))
       

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
    

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json



class Question(BaseModel):
    question: str


# dummy imports (replace with your real ones)
# from Services.problemTypeDetector import classify
# from Services.ValidationChecker import cached_ground_truth
# from Services.prompt_router import build_prompt
# from Services.Load_Model import stream_gemini


@app.post("/solve_math_stream")
async def solve_math_stream(q: Question):

    # 1. preprocess
    problem_type = classify(q.question.lower())
    clean_question = normalize_math_input(q.question)

    truth = cached_ground_truth(clean_question)

    # safety check
    if truth is None:
        return {
            "type": "error",
            "data": {"reason": "Invalid truth"}
        }

    route = build_prompt(problem_type, q.question, truth)

    # 2. streaming generator
    def generator():
        full = ""

        try:
            # stream tokens from Gemini
            for token in stream_gemini(route):

                if not token:
                    continue

                full += token

                chunk = {
                    "type": "token",
                    "text": token
                }

                yield f"data: {json.dumps(chunk)}\n\n"

        except Exception as e:
            error_chunk = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            return

        # 3. final response AFTER streaming ends
        final_chunk = {
            "type": "done",
            "full": full
        }

        yield f"data: {json.dumps(final_chunk)}\n\n"

    return StreamingResponse(
        generator(),
        media_type="text/event-stream"
    )