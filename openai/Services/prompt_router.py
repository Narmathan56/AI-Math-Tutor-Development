
from Services.problemTypeDetector import classify
def get_system_prompt(problem_type: str, question: str, truth: dict):

    if problem_type == "log":
        return log_prompt(question, truth)

    if problem_type == "trigonometry":
        return trig_prompt(question, truth)

    if problem_type == "polynomial":
        return polynomial_prompt(question, truth)


    return general_equation_prompt(question, truth)


def log_prompt(question, truth):

       return {
        "prompt": f"""
You are a logarithm equation solver.

Problem:
{question}

Verified Answer:
{truth["answer"]}

RULES:
- Convert logs → exponential form ONLY when needed
- Use correct base conversion
- Always enforce domain: argument > 0
- One transformation per step
- No explanations
- JSON only

OUTPUT FORMAT:
{{
  "steps": [{{"text": "...", "expression": "..."}}],
  "final_answer": []
}}

FINAL RULE:
final_answer must match SymPy exactly
"""
    }


def trig_prompt(question, truth):

    return {
        "prompt": f"""
You are a trigonometry equation solver.

Problem:
{question}

Verified Answer:
{truth["answer"]}

RULES:
- Use identities only if required
- Keep transformations algebraic
- No narrative text
- JSON only

Allowed identities:
- sin^2 + cos^2 = 1
- tan = sin/cos
- angle solutions in [0, 2π] if needed

OUTPUT:
{{
  "steps": [{{"text": "...", "expression": "..."}}],
  "final_answer": []
}}
"""
    }


def polynomial_prompt(question, truth):

    return {
        "prompt": f"""
You are a polynomial equation solver.

Problem:
{question}

Verified Answer:
{truth["answer"]}

RULES:
- Factorization preferred
- Substitution allowed (x^2 = y)
- One algebra step per line
- Strict JSON only

OUTPUT:
{{
  "steps": [{{"text": "...", "expression": "..."}}],
  "final_answer": []
}}
"""
    }

def general_equation_prompt(question, truth):

    return {
        "prompt": f"""
You are a general equation solver.

Problem:
{question}

Verified Answer:
{truth["answer"]}

RULES:
- strict JSON only

OUTPUT:
{{
  "steps": [{{"text": "...", "expression": "..."}}],
  "final_answer": []
}}
"""
    }
