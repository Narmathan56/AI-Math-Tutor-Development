import re
def classify(q: str) -> str:

    # 1. CALCULUS (highest complexity priority)
    if any(k in q for k in [
        "derivative", "differentiate", "integrate",
        "integration", "limit", "d/dx", "dy/dx"
    ]):
        return "calculus"

    # 2. LOGARITHMS
    if "log" in q:
        return "log"

    # 3. TRIGONOMETRY
    if any(k in q for k in ["sin", "cos", "tan", "cot", "sec", "csc"]):
        return "trigonometry"

    # 4. EQUATION / POLYNOMIAL (structure-based detection > symbols)
    if "=" in q:
        if any(c.isalpha() for c in q):
            return "polynomial"
        return "arithmetic"

    # 5. ALGEBRA keywords
    if any(k in q for k in ["solve", "factor", "simplify"]):
        return "polynomial"

    # 6. PURE ARITHMETIC
    if re.fullmatch(r"[0-9\s+\-*/().^]+", q):
        return "arithmetic"

    return "concept"