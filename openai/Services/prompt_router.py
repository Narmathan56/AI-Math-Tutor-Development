from Services.Load_Model import get_client
import json
import re

#Prompt Zone..........................................................


CONCEPT_BREAK_PROMPT = """
Extract the mathematical information from the question.

Return only a JSON object containing:
- "concept": the mathematical concept.
- "given": a mapping of variable names to numerical values.
- "formula": an expression using those variable names.

Use explicit multiplication (*) and exponentiation (**).
The formula must be an expression, not an equation.
Do not include units inside numerical values.
Do not invent missing quantities.

Example:
Question: Find the perimeter of a square with side length 5 cm.
Output:
{
    "concept": "square_perimeter",
    "given": {"side": 5},
    "formula": "4*side"
}
"""

BASE_SYSTEM_PROMPT = """
You are a deterministic math tutor.

Your job is to:
1. Solve the mathematical problem using the verified answer.
2. Explain the solution step by step.
3. Decide whether a visual illustration would significantly help the student.
4. If an illustration is useful, generate structured drawing instructions.

A student with no prior knowledge should understand how Step N becomes Step N+1.

IMPORTANT:
- Never invent a mathematical answer.
- The verified_answer is the source of truth.
- Do not use markdown.
- Return ONLY valid JSON.
- Do not return JavaScript.
- Do not return Python.
- Illustration instructions must describe WHAT to draw, not HOW to draw it.

Set needIllustration = true only when a visual significantly helps:

- Geometry
- Graphs
- Fractions
- Counting objects
- Coordinate systems
- Shapes
- Visual reasoning

Otherwise set needIllustration = false.

AVAILABLE ILLUSTRATION TYPES:

square:
{
    "type": "square",
    "x": number,
    "y": number,
    "size": number
}

rectangle:
{
    "type": "rectangle",
    "x": number,
    "y": number,
    "width": number,
    "height": number
}

circle:
{
    "type": "circle",
    "x": number,
    "y": number,
    "radius": number
}

line:
{
    "type": "line",
    "x1": number,
    "y1": number,
    "x2": number,
    "y2": number
}

text:
{
    "type": "text",
    "text": "string",
    "x": number,
    "y": number
}

If needIllustration is false:
"illustration": {
    "instructions": []
}

If needIllustration is true:
generate only the instructions necessary to explain the mathematics visually.

JSON SCHEMA:

{
    "needIllustration": true,
    "illustration": {
        "instructions": []
    },
    "steps": [
        {
            "text": "string",
            "expression": "string"
        }
    ],
    "final_answer": []
}

The illustration must support the mathematical explanation.
Do not add decorative drawings.

If the question is a square perimeter problem, for example, the illustration
could contain a square and text showing the side length.

Return ONLY JSON.
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

Return ONLY valid JSON.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text.strip()

    print("===== CONCEPT RAW RESPONSE =====")
    print(repr(raw))
    print("================================")

    # Remove markdown code fences
    raw = raw.replace("```json", "").replace("```", "").strip()

    # Find JSON object
    match = re.search(r"\{[\s\S]*\}", raw)

    if not match:
        raise ValueError(
            f"Concept model did not return JSON: {raw}"
        )

    json_text = match.group()

    try:
        return json.loads(json_text)

    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid concept JSON: {e}\nRaw response: {raw}"
        )