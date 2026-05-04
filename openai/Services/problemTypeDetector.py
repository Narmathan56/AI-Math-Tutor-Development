import re

def detect_problem_type(question: str) -> str:
    """
    Returns:
        - "equation"
        - "arithmetic"
        - "algebra"
        - "trigonometry"
        - "calculus"
        - "concept"
    """

    if not question:
        return "concept"

    q = question.strip().lower()

    # =========================
    # 1. EQUATION CHECK (highest priority)
    # =========================
    if "=" in q:
        return "equation"

    # =========================
    # 2. CALCULUS DETECTION
    # =========================
    calculus_keywords = [
        "derivative", "differentiate", "integrate",
        "integration", "limit", "dy/dx", "d/dx"
    ]

    if any(word in q for word in calculus_keywords):
        return "calculus"

    # =========================
    # 3. TRIGONOMETRY DETECTION
    # =========================
    trig_keywords = [
        "sin", "cos", "tan", "cot", "sec", "csc",
        "trig", "trigonometry"
    ]

    if any(word in q for word in trig_keywords):
        return "trigonometry"

    # =========================
    # 4. PURE ARITHMETIC CHECK
    # =========================
    arithmetic_pattern = r"^[0-9\s+\-*/().^]+$"

    if re.search(arithmetic_pattern, q):
        return "arithmetic"

    # =========================
    # 5. ALGEBRA DETECTION
    # =========================
    algebra_patterns = [
        r"[a-zA-Z].*\d",   # x2, a3 etc
        r"\bsolve\b",
        r"\bfactor\b",
        r"\bsimplify\b"
    ]

    if any(re.search(p, q) for p in algebra_patterns):
        return "algebra"

    # =========================
    # 6. DEFAULT
    # =========================
    return "concept"