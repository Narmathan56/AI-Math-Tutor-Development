from Services.Load_Model import get_client
import json
import re

#Prompt Zone..........................................................



BASE_SYSTEM_PROMPT = """
You are a deterministic math engine.
A student with no prior knowledge should understand how Step N becomes Step N+1.

First determine whether a visual illustration would significantly help the student understand the concept.

Set:
needIllustration = true

only when:
- Geometry
- Graphs
- Fractions
- Counting objects
- Coordinate systems
- Shapes
- Visual reasoning

Otherwise:
needIllustration = false

Return JSON only.

You will receive:
- problem_type
- question
- verified_answer

If the current question refers to the previous question or previous answer,
use the previous memory to understand the context.

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



CONCEPT_BREAK_PROMPT = """
Convert the student's concept problem into structured mathematics.

Return ONLY JSON.

Schema:

{
    "concept":"string",
    "given":{},
    "formula":"string"
}

Example:

Question:
Each side of a square measures 5.6 cm.
Find the perimeter.

Output:
{
    "concept":"square_perimeter",
    "given":{
        "side":5.6
    },
    "formula":"4*side"
}
"""
#Prompt Zone Ending............................................................................
def build_prompt(problem_type: str, question: str, truth: dict, memory: dict) -> str:

    verified = truth.get("answer", []) if isinstance(truth, dict) else []

    previous_question = memory.get("previous_question")
    previous_answer = memory.get("previous_answer")
    previous_steps = memory.get("previous_steps", [])

    return f"""
{BASE_SYSTEM_PROMPT}

Previous question:
{previous_question}

Previous answer:
{previous_answer}

Previous steps:
{previous_steps}

Current question:
{question}

Verified answer for the current question:
{verified}

Important:
- If the current question is a follow-up such as "why 4?", "how?",
  "why is that the answer?", or "explain that", use the previous question,
  previous answer, and previous steps.
- Do not treat the follow-up as an unrelated new math problem.
- Explain the relationship clearly.

Return ONLY JSON.
"""





def conceptBreak(question, client):

    prompt = f"""
{CONCEPT_BREAK_PROMPT}

Question:
{question}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text.strip()

    print("===== CONCEPT RAW RESPONSE =====")
    print(repr(raw))
    print("================================")

    # Remove markdown
    raw = raw.replace("```json", "").replace("```", "").strip()

    # Extract JSON object
    match = re.search(r"\{[\s\S]*\}", raw)

    if not match:
        raise ValueError(
            f"Concept model did not return JSON: {raw}"
        )

    return json.loads(match.group())