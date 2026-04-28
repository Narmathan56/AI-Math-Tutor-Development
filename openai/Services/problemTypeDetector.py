import re


def detect_problem_type(question: str) -> str:
    """Returns:
       - "arithmetic" if contian numbers and operations
       -"equation" if contains and "="
       -"concept" if contains text"""
    




    question = question.strip().lower()


    if "=" in question:
        return "equation"
    if re.search(r"^[0-9\s+\-*/().]+$", question):
        return "arithmetic"
    return "concept"