from sympy import sympify, Eq, solve, simplify, Symbol
import re

x = Symbol("x")

# =========================
# STEP EXTRACTION
# =========================
def get_step_text(step):
    if isinstance(step, dict):
        text = step.get("text", "")
        eq = step.get("eq", "")
        return f"{text} {eq}".strip()
    return str(step)


# =========================
# CLEAN FINAL ANSWER
# =========================
def clean_final_answer(ans):
    ans = str(ans)

    # remove latex + formatting
    ans = re.sub(r"\$|\\boxed|{|}", "", ans)

    # normalize separators
    ans = ans.replace("or", ",").replace("and", ",")
    ans = ans.replace("=", " ")

    return ans.strip()


# =========================
# NORMALIZE INPUT
# =========================
def normalize_math_input(expr: str) -> str:
    if not expr:
        return expr

    expr = re.sub(r'[\u200b-\u200f\uFEFF]', '', expr)
    expr = expr.replace("−", "-")
    expr = expr.replace("𝑥", "x").replace("𝑋", "x")

    expr = re.sub(r"\s+", "", expr)

    expr = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", expr)
    expr = re.sub(r"([a-zA-Z])(\d)", r"\1*\2", expr)
    expr = re.sub(r"(\))(\()", r"\1*\2", expr)
    expr = re.sub(r"(\d)(\()", r"\1*\2", expr)
    expr = re.sub(r"([a-zA-Z])(\()", r"\1*\2", expr)

    expr = expr.replace("^", "**")
    return expr


# =========================
# ANSWER PARSER (STRONG)
# =========================
def parse_answers(text):
    if not text:
        return set()

    text = clean_final_answer(text)

    # -------------------------
    # HANDLE ±
    # -------------------------
    if "±" in text:
        nums = re.findall(r"\d+\.?\d*", text)
        result = set()

        for n in nums:
            val = float(n)
            result.add(val)
            result.add(-val)

        return result

    # -------------------------
    # NORMAL EXTRACTION
    # -------------------------
    nums = re.findall(r"-?\d+\.?\d*", text)

    return set(float(n) for n in nums)


# =========================
# SUBSTITUTION VALIDATION
# =========================
def verify_by_substitution(problem, user_answers):
    try:
        clean_problem = normalize_math_input(problem)

        if "=" not in clean_problem:
            return False

        lhs, rhs = clean_problem.split("=")

        lhs_expr = sympify(lhs)
        rhs_expr = sympify(rhs)

        for val in user_answers:
            try:
                diff = lhs_expr.subs(x, val) - rhs_expr.subs(x, val)

                if abs(float(diff)) > 1e-5:
                    return False
            except:
                return False

        return True

    except:
        return False


# =========================
# STEP VALIDATION (OPTIONAL)
# =========================
def validate_steps(steps):
    for i in range(len(steps) - 1):

        prev = get_step_text(steps[i])
        curr = get_step_text(steps[i + 1])

        if "=" not in prev or "=" not in curr:
            continue

        if prev.count("=") != 1 or curr.count("=") != 1:
            continue

        try:
            p_lhs, p_rhs = prev.split("=")
            c_lhs, c_rhs = curr.split("=")

            p = sympify(normalize_math_input(p_lhs)) - sympify(normalize_math_input(p_rhs))
            c = sympify(normalize_math_input(c_lhs)) - sympify(normalize_math_input(c_rhs))

            if simplify(p - c).is_zero:
                continue

            try:
                if set(solve(p)) == set(solve(c)):
                    continue
            except:
                pass

            return False

        except:
            continue

    return True


# =========================
# MAIN VALIDATOR
# =========================
def validate_solution(problem: str, data: dict):

    try:
        if not data:
            return {"valid": False, "reason": "Empty response"}

        steps = data.get("steps", [])
        final_answer = data.get("final_answer")

        clean_problem = normalize_math_input(problem)

        # -------------------------
        # SAFE STEPS (NON-BLOCKING)
        # -------------------------
        if not isinstance(steps, list):
            steps = []

        validate_steps(steps)  # optional only

        # -------------------------
        # PARSE ANSWERS
        # -------------------------
        user_answers = parse_answers(final_answer)

        if not user_answers:
            return {"valid": False, "reason": "Cannot parse final answer"}

        # -------------------------
        # EQUATION CASE
        # -------------------------
        if "=" in clean_problem:
            is_valid = verify_by_substitution(problem, user_answers)

            return {
                "valid": is_valid,
                "reason": "ok" if is_valid else "Incorrect final answer"
            }

        # -------------------------
        # ARITHMETIC CASE
        # -------------------------
        else:
            correct_val = float(sympify(clean_problem))
            user_val = list(user_answers)[0]

            return {
                "valid": abs(user_val - correct_val) < 1e-6,
                "reason": "ok" if abs(user_val - correct_val) < 1e-6 else "Incorrect final answer"
            }

    except Exception as e:
        return {
            "valid": False,
            "reason": f"Validation error: {str(e)}"
        }