

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

def compute_ground_truth(question: str):
    try:
        question = normalize_math_input(question)

        # EQUATION CASE
        if "=" in question:
            lhs, rhs = question.split("=")

            lhs_expr = sympify(lhs)
            rhs_expr = sympify(rhs)

            sol = solve(Eq(lhs_expr, rhs_expr), x)

            cleaned = []
            for s in sol:
              try:
                cleaned.append(float(s.evalf()))
              except:
                cleaned.append(str(s))  # keep symbolic fallback

            return {
             "type": "equation",
             "answer": cleaned
       }

            

        # ARITHMETIC CASE
        expr = sympify(question)
        return {
            "type": "arithmetic",
            "answer": float(expr)
        }

    except Exception as e:
        print("SYMPY ERROR:", e)
        return None
    
def normalize_answer(ans):
    if isinstance(ans, list):
        return sorted([float(x) for x in ans])

    if isinstance(ans, str):
        import re
        nums = re.findall(r"-?\d+\.?\d*", ans)
        return sorted([float(n) for n in nums])

    return []    

def compare_answers(user, truth):
    user_norm = normalize_answer(user)
    truth_norm = normalize_answer(truth)
    return set(user_norm) == set(truth_norm)

def validate_transition(before_eq, after_eq):
    try:
        if "=" not in before_eq or "=" not in after_eq:
            return False

        b_lhs, b_rhs = before_eq.split("=")
        a_lhs, a_rhs = after_eq.split("=")

        before_expr = (
            sympify(normalize_math_input(b_lhs))
            - sympify(normalize_math_input(b_rhs))
        )

        after_expr = (
            sympify(normalize_math_input(a_lhs))
            - sympify(normalize_math_input(a_rhs))
        )

        # EXACT algebra equivalence
        if simplify(before_expr - after_expr).is_zero:
            return True

        # SAME SOLUTION SET
        try:
            if set(solve(before_expr)) == set(solve(after_expr)):
                return True
        except:
            pass

        return False

    except:
        return False    


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
import re

SAFE_FUNCS = ["log", "sin", "cos", "tan", "ln", "sqrt"]

def normalize_math_input(expr: str) -> str:
    if not expr:
        return expr

    # -------------------------
    # CLEAN UNICODE ISSUES
    # -------------------------
    expr = re.sub(r'[\u200b-\u200f\uFEFF]', '', expr)
    expr = expr.replace("−", "-")
    expr = expr.replace("𝑥", "x").replace("𝑋", "x")

   

    # -------------------------
    # HANDLE log base notation
    # log3(x) -> log(x,3)
    # -------------------------
    expr = re.sub(
        r'log(\d+)\((.*?)\)',
        r'log(\2,\1)',
        expr
    )

    # -------------------------
    # PROTECT FUNCTIONS (VERY IMPORTANT)
    # prevents log( becoming log*(
    # -------------------------
    for f in SAFE_FUNCS:
        expr = expr.replace(f, f"__{f}__")

    # -------------------------
    # IMPLICIT MULTIPLICATION RULES
    # -------------------------
    # convert x3, x2, x10 → x^3, x^2, x^10
    expr = re.sub(r"\b([a-zA-Z])(\d+)\b", r"\1^\2", expr)

    # 2x -> 2*x
    expr = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", expr)

    

    # )( -> )*(
    expr = re.sub(r"(\))(\()", r"\1*\2", expr)

    # 2( -> 2*(
    expr = re.sub(r"(\d)(\()", r"\1*\2", expr)

    # -------------------------
    # RESTORE FUNCTIONS
    # -------------------------
    for f in SAFE_FUNCS:
        expr = expr.replace(f"__{f}__", f)

    # -------------------------
    # EXPONENT FIX
    # -------------------------
    expr = expr.replace("^", "**")


    # for the text questions

    expr = expr.lower()

    expr = expr.replace("what is", "")
    expr = expr.replace("plus", "+")
    expr = expr.replace("minus", "-")
    expr = expr.replace("times", "*")
    expr = expr.replace("multiplied by", "*")
    expr = expr.replace("divided by", "/")

    expr = expr.replace("zero", "0")
    expr = expr.replace("one", "1")
    expr = expr.replace("two", "2")
    expr = expr.replace("three", "3")
    expr = expr.replace("four", "4")
    expr = expr.replace("five", "5")
    expr = expr.replace("six", "6")
    expr = expr.replace("seven", "7")
    expr = expr.replace("eight", "8")
    expr = expr.replace("nine", "9")
    expr = expr.replace("ten", "10")

    expr = expr.strip()
     # remove spaces
    expr = re.sub(r"\s+", "", expr)
    


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

    results = []

    for step in steps:

        before_eq = step.get("before", "")
        after_eq = step.get("after", "")

        valid = validate_transition(before_eq, after_eq)

        results.append({
            "step_id": step.get("id"),
            "valid": valid
        })

    return results
# =========================
# MAIN VALIDATOR
# =========================
def validate_solution(problem: str, data: dict, truth: dict):
    try:
        if not data:
            return {"valid": False, "reason": "Empty response"}

        steps = data.get("steps") or data.get("result", {}).get("steps", [])
        if not isinstance(steps, list):
          steps = []
        final_answer = data.get("final_answer")

        if not isinstance(steps, list):
            steps = []

        step_results=validate_steps(steps)
        print("STEP VALIDATION:", step_results)

        clean_problem = normalize_math_input(problem)

        user_answers = normalize_answer(final_answer)
        truth_answers = normalize_answer(truth["answer"])

        # -------------------------
        # EQUATION CASE
        # -------------------------
        if "=" in clean_problem:
            return {
                "valid": set(user_answers) == set(truth_answers),
                "reason": "ok"
            }

        # -------------------------
        # ARITHMETIC CASE
        # -------------------------
        if not user_answers:
            return {"valid": False, "reason": "Cannot parse final answer"}

        expr = sympify(clean_problem)

        if expr.free_symbols:
            return {"valid": False, "reason": "Not arithmetic"}

        correct_val = float(expr.evalf())
        user_val = list(user_answers)[0]

        return {
            "valid": abs(user_val - correct_val) < 1e-6,
            "reason": "ok"
        }

    except Exception as e:
        return {
            "valid": False,
            "reason": f"Validation error: {str(e)}"
        }