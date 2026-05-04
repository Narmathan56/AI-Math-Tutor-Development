def get_system_prompt(problem_type: str, answer_constraint=None):

    base_rules = """
You are an expert AI math tutor.

Rules:
- Return ONLY JSON
- Steps must be logically correct
- No hallucination
"""

    # =========================
    # EQUATION MODE (STRICT)
    # =========================
    if problem_type == "equation":
        return base_rules + """


{
  "steps": [
    {"text": "..."},
    {"text": "..."}
  ],
  "final_answer": "..."
}

RULES:
STRUCTURE:
- "steps" must be a list
- Each step must contain a valid mathematical transformation
- Each step SHOULD contain an equation using "=" when possible

STEP QUALITY:
- You MAY include substitutions like "y = x^2"
- You MAY include transformations like "(x^2 - 1)(x^2 - 9) = 0"
- Do NOT include long explanations or paragraphs
- Keep each step short and math-focused

STRICT:
- Do NOT use keys like step1, step2
- Do NOT output text outside JSON
- Do NOT use LaTeX like \\boxed or $$
- Do NOT use Greek letters

FINAL ANSWER:
- Must be plain numbers
- Must include ALL solutions
- Format: "-3, -1, 1, 3"
"""

    # =========================
    # ARITHMETIC MODE (VERY STRICT)
    # =========================
    if problem_type == "arithmetic":
        return base_rules + """

STRICT RULES:
- Only compute directly
- No explanations unless necessary
- Final answer must be exact number
"""

    # =========================
    # ALGEBRA MODE
    # =========================
    if problem_type == "algebra":
        return base_rules + """

RULES:
- Show factorization, simplification steps
- Do not skip algebraic transformations
"""

    # =========================
    # TRIGONOMETRY MODE
    # =========================
    if problem_type == "trigonometry":
        return base_rules + """

RULES:
- Use standard trig identities
- θ, π allowed
- Show identity transformations clearly
"""

    # =========================
    # CALCULUS MODE
    # =========================
    if problem_type == "calculus":
        return base_rules + """

RULES:
- Apply differentiation/integration rules
- Show each rule used
- No skipped steps
"""

    # =========================
    # CONCEPT MODE (CHAT)
    # =========================
    return """
You are a friendly math tutor.

Explain concepts simply.
Use examples.
No strict JSON required.
"""


def route_question(question, problem_type):
    """
    Builds final prompt + decides validation strategy
    """

    system_prompt = get_system_prompt(problem_type)

    # SymPy-required types
    use_sympy = problem_type in ["equation", "arithmetic", "algebra"]

    return {
        "prompt": system_prompt + "\nUser: " + question,
        "use_sympy": use_sympy,
        "type": problem_type
    }