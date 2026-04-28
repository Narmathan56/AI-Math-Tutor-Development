from sympy import sympify, Eq, solve, simplify
import re


# =========================
# SAFE NUMBER EXTRACTION
# =========================
def extract_number(text):
    if text is None:
        return []

    return [
        float(x)
        for x in re.findall(r"-?\d+\.?\d*", str(text))
    ]


# =========================
# SAFE STEP TEXT EXTRACTION
# =========================
def get_step_text(step):
    if isinstance(step, dict):
        return step.get("text", "")
    return str(step)


# =========================
# NORMALIZE INPUT
# =========================
def normalize_math_input(expr: str) -> str:
    if not expr:
        return expr

    expr = expr.replace("−", "-")
    expr = expr.replace("𝑥", "x").replace("𝑋", "x")

    expr = re.sub(r"\s+", "", expr)
    expr = re.sub(r"\^\s+", "^", expr)

    expr = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", expr)
    expr = re.sub(r"([a-zA-Z])(\d)", r"\1*\2", expr)
    expr = re.sub(r"(\))(\()", r"\1*\2", expr)
    expr = re.sub(r"(\d)(\()", r"\1*\2", expr)
    expr = re.sub(r"([a-zA-Z])(\()", r"\1*\2", expr)

    expr = expr.replace("^", "**")

    return expr


# =========================
# VALIDATOR
# =========================
def validate_solution(problem: str, parse_steps: dict):

    try:
        if parse_steps is None:
            return {"valid": False, "reason": "No steps is None (pipeline failure)"}

        steps = parse_steps.get("steps", [])
        final_answer = parse_steps.get("final_answer")
        problem = normalize_math_input(problem)

        # -------------------------
        # BASIC CHECKS
        # -------------------------
        if not steps:
            return {"valid": False, "reason": "No steps found"}

        if not re.search(r"[0-9+\-*/=a-zA-Z]", problem):
            return {
                "valid": False,
                "reason": "Concept question - validation skipped"
            }

        # -------------------------
        # STEP VALIDATION
        # -------------------------
        for prev_step, curr_step in zip(steps, steps[1:]):

            prev_text = get_step_text(prev_step)
            curr_text = get_step_text(curr_step)

            prev_eq = re.findall(r"[0-9a-zA-Z+\-*/=().^ ]+", prev_text)
            curr_eq = re.findall(r"[0-9a-zA-Z+\-*/=().^ ]+", curr_text)

            if not prev_eq or not curr_eq:
                continue

            prev_eq = prev_eq[0].strip()
            curr_eq = curr_eq[0].strip()

            if "=" not in prev_eq or "=" not in curr_eq:
                continue

            try:
                prev_lhs = normalize_math_input(prev_eq.split("=")[0])
                prev_rhs = normalize_math_input(prev_eq.split("=")[1])

                curr_lhs = normalize_math_input(curr_eq.split("=")[0])
                curr_rhs = normalize_math_input(curr_eq.split("=")[1])
                prev_expr = sympify(prev_lhs) - sympify(prev_rhs)
                curr_expr = sympify(curr_lhs) - sympify(curr_rhs)


                
                if not simplify(prev_expr - curr_expr).simplify().is_zero:
                  return {
                  "valid": False,
                  "reason": f"Invalid step transition: {prev_text} → {curr_text}"
                }
           

            except Exception:
                continue

        # -------------------------
        # FINAL ANSWER VALIDATION
        # -------------------------
        if final_answer is None:
            return {"valid": True, "reason": "No final answer provided"}

        user_answer = set(extract_number(final_answer))

        # -------------------------
        # EQUATION CASE (SYMPY TRUTH)
        # -------------------------
        if "=" in problem:

            lhs, rhs = problem.split("=")

            lhs = sympify(lhs)
            rhs = sympify(rhs)

            equation = Eq(lhs, rhs)
            solution = solve(equation, dict=False)

            if not solution:
                return {"valid": False, "reason": "No solution found"}

            correct_answer = set()

            for sol in solution:
                correct_answer.update(extract_number(sol))

        # -------------------------
        # ARITHMETIC CASE
        # -------------------------
        else:
            try:
                correct_answer = {float(sympify(problem))}
            except Exception:
                return {"valid": False, "reason": "Invalid arithmetic expression"}

        # -------------------------
        # COMPARE FINAL ANSWER
        # -------------------------
        if user_answer is None or correct_answer is None:
            return {"valid": False, "reason": "Could not parse final answer"}

        if "=" in problem:
            if user_answer != correct_answer:
                return {
                    "valid": False,
                    "reason": "Incorrect final answer"
                }
        else:
            user_val = list(user_answer)[0]
            correct_val = list(correct_answer)[0]

            if abs(user_val - correct_val) > 1e-6:
                return {
                    "valid": False,
                    "reason": "Incorrect final answer"
                }

        return {"valid": True, "reason": "All validations passed"}

    except Exception as e:
        return {
            "valid": False,
            "reason": f"Validation error: {str(e)}"
        }