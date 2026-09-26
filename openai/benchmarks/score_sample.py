import json
from pathlib import Path

import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Services.ValidationChecker import validate_solution, compute_ground_truth
from Services.problemTypeDetector import classify



folder = Path(__file__).resolve().parent

with (folder/"sample_response.json").open(encoding="utf-8") as file:
    record = json.load(file)

paresed=json.loads(record["raw_response"])




cases_path = Path(__file__).resolve().parent / "cases.json"

with cases_path.open(encoding="utf-8") as file:
    cases=json.load(file)


for case in cases:
    if case["id"]==record["id"]:
        model_answer = paresed["final_answer"]
        expected_answer = case["expected"]

        raw_correct = model_answer == expected_answer

        print("Model answer:", model_answer)
        print("Expected answer:", expected_answer)
        print("Raw correct:", raw_correct)


        question = case["question"]
        truth = compute_ground_truth(question)

        validation = validate_solution(
        problem=question,
        data =paresed,
        truth=truth,
        problem_type=classify(question)


        )

        accepted =validation["valid"]


        print("Validator accepted:", accepted)
        print("Validator reason:", validation["reason"])  

        if raw_correct and accepted:
            outcome = "correct_accepted"
        elif raw_correct and not accepted:
            outcome = "correct_rejected"
        elif not raw_correct and accepted:
            outcome = "incorrect_accepted"
        else:
            outcome = "incorrect_rejected"

        print("Outcome:", outcome)

        wrong_output= {"steps": [], "final_answer": [5]}

        wrong_validation = validate_solution(
            problem=question,
            data=wrong_output, 
            truth = truth, 
            problem_type = classify(question)

        )

        print("Deliberately wrong answer:", wrong_output["final_answer"])
        print("Validator accepted:", wrong_validation["valid"])
        print("Reason:", wrong_validation["reason"])

    
        


