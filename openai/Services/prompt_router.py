
def get_system_prompt(problem_type: str, question: str, truth: dict):

    answer = str(truth["answer"])

    prompt = f"""
You are a math tutor.

Problem:
{question}

Verified Answer:
{answer}

Explain step-by-step like a teacher.

RULES:
- No JSON
- No code
- generate mathematical equations only
- steps must match between question and answer
- No final answer block
- Just clean step-by-step explanation
- Use simple language
- One step per line
- format:
   step 1: ...
   step 2: ...


Think like you're writing on a whiteboard for a student.
"""

    return {
        "prompt": prompt,
        "use_sympy": True,
        "type": problem_type
    }