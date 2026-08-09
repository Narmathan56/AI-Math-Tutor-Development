BASE_SYSTEM_PROMPT = """
You are a deterministic math engine.
A student with no prior knowledge should understand how Step N becomes Step N+1.

You will receive:
- problem_type
- question
- verified_answer

Return ONLY JSON.

Schema:

{
  "steps":[
    {
      "text":"string",
      "expression":"string"
    }
  ],
  "final_answer":[]
}

No markdown.
No explanation outside JSON.
"""
def build_prompt(problem_type: str, question:str, truth:str, memory:dict) -> str:
    if not isinstance(truth, dict):
        truth = {"answer": []}

    verified = truth.get("answer", [])

    previous_question = memory.get("previous_question")
    previous_answer = memory.get("previous_answer")
    previous_steps = memory.get("previous_steps", [])

    return f"""
{BASE_SYSTEM_PROMPT}

problem_type: {problem_type}
previous_question:{previous_question}

previous_answer:
{previous_answer}

previous_steps:
{previous_steps}

question: {question}
verified_answer: {verified}

Return ONLY JSON.
"""