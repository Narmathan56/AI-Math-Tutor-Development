BASE_SYSTEM_PROMPT = """
You are a deterministic math engine.

You will receive:
- problem_type
- question
- verified_answer

RULES:
- Always output ONLY valid JSON
- No explanations
- No code
- No markdown
- No extra keys

IMPORTANT:
You MUST return this EXACT JSON structure.

DO NOT change key names.

DO NOT omit steps.

VALID FORMAT:

{
"steps": [
{
"text": "Factor equation",
"expression": "(x^2-1)(x^2-9)=0"
},
{
"text": "Solve factors",
"expression": "x=±1, ±3"
}
],
"final_answer": [-3, -1, 1, 3]
}

INVALID:
{
"solution": "...",
"algorithm": "..."
}

INVALID:
{
"answer": ...
}

The response MUST contain:

- steps
- final_answer

No other schema allowed.
"""
def build_prompt(problem_type: str, question:str, truth:str) -> str:
    if not isinstance(truth, dict):
        truth = {"answer": []}

    verified = truth.get("answer", [])

    return f"""
{BASE_SYSTEM_PROMPT}

problem_type: {problem_type}
question: {question}
verified_answer: {verified}

Return ONLY JSON.
"""