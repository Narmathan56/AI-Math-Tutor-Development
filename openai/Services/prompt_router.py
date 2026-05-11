def get_system_prompt(problem_type: str, answer_constraint=None):

    # =========================
    # GLOBAL BASE RULES (ALL MODES)
    # =========================
    base_rules = """
You are an expert AI math tutor.

GLOBAL RULES:
- Solve step by step
- Each step must contain ONLY ONE mathematical operation
- No paragraphs
- No explanations
- No JSON
- Be mathematically correct
- Do NOT skip steps
- Do NOT combine multiple transformations in one step
"""

    # =========================
    # EQUATION MODE
    # =========================
    if problem_type == "equation":
        return base_rules + """

EQUATION MODE RULES:
- Preserve original equation exactly
- Do NOT rewrite or simplify before solving
- Use standard algebraic transformations step by step
- Each step must change only one side or apply one rule
- Final step must clearly show solution set

FORMAT:
Step 1: original equation
Step 2: transformation
Step 3: simplification
...
Final Step: answer
"""

    # =========================
    # ARITHMETIC MODE
    # =========================
    if problem_type == "arithmetic":
        return base_rules + """

ARITHMETIC MODE RULES:
- Direct computation only
- Break into small steps if needed
- No algebraic manipulation rules
- Final step = exact answer
"""

    # =========================
    # ALGEBRA MODE
    # =========================
    if problem_type == "algebra":
        return base_rules + """

ALGEBRA MODE RULES:
- Factorisation and simplification allowed
- Do not skip intermediate steps
- One transformation per line
- Maintain equation balance
"""

    # =========================
    # TRIGONOMETRY MODE
    # =========================
    if problem_type == "trigonometry":
        return base_rules + """

TRIGONOMETRY MODE RULES:
- Use standard trig identities only
- Apply one identity per step
- Keep θ and π notation allowed
- No skipping identity transformations
"""

    # =========================
    # CALCULUS MODE (FIXED + SAFE)
    # =========================
    if problem_type == "calculus":
        return base_rules + """

CALCULUS MODE RULES:

CORE PRINCIPLE:
- The original function must remain unchanged before differentiation

STRICT RULES:
- Do NOT rewrite or modify the original expression
- Do NOT change signs or structure before differentiation
- Do NOT perform algebraic simplification before applying calculus rules
- Each term must be differentiated exactly once
- Do NOT re-differentiate or reuse processed terms
- No algebra operations during differentiation process

STEP STRUCTURE:
Step 1: Write original function
Step 2: Differentiate first term only
Step 3: Differentiate remaining terms separately
Step 4: Combine results

EXECUTION RULE:
- Exactly ONE mathematical operation per step
- No mixed operations
- No hidden simplification inside steps

FINAL STEP:
- Provide final simplified derivative only
"""

    # =========================
    # CONCEPT / CHAT MODE
    # =========================
    return """
You are a friendly math tutor.

Explain concepts simply using examples.
No strict formatting required.
"""


def route_question(question, problem_type):

    system_prompt = get_system_prompt(problem_type)

    # SymPy-safe categories only
    use_sympy = problem_type in ["equation", "arithmetic", "algebra"]

    return {
        "prompt": system_prompt + "\nQuestion: " + question,
        "use_sympy": use_sympy,
        "type": problem_type
    }