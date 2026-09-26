import json
from pathlib import Path

import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Services.ValidationChecker import validate_solution, compute_ground_truth
from Services.problemTypeDetector import classify

folder = Path(__file__).resolve().parent

with (folder / "cases.json").open(encoding="utf-8") as file:
    cases = json.load(file)

cases_by_id = {case["id"]: case for case in cases}
counts = {
    "correct_accepted": 0,
    "correct_rejected": 0,
    "incorrect_accepted": 0,
    "incorrect_rejected": 0,
}

with (folder / "responses.jsonl").open(encoding="utf-8") as file:
    for line in file:
        if not line.strip():
            continue

        record = json.loads(line)
        case = cases_by_id[record["id"]]
        parsed = json.loads(record["raw_response"])

        print(case["id"], parsed["final_answer"], case["expected"])

        model_answer = parsed["final_answer"]
        expected_answer = case["expected"]
        raw_correct = model_answer == expected_answer

        print("Model answer:", model_answer)
        print("Expected answer:", expected_answer)
        print("Raw correct:", raw_correct)

        question = case["question"]
        validation = validate_solution(
            problem=question,
            data=parsed,
            truth=compute_ground_truth(question=question),
            problem_type=classify(question),
        )
        accepted = validation["valid"]

        if raw_correct and accepted:
            outcome = "correct_accepted"
        elif raw_correct and not accepted:
            outcome = "correct_rejected"
        elif not raw_correct and accepted:
            outcome = "incorrect_accepted"
        else:
            outcome = "incorrect_rejected"
        counts[outcome] += 1    

        print(case["id"], outcome, validation["reason"])



total = sum(counts.values())
correct = counts["correct_accepted"] + counts["correct_rejected"]
accepted = counts["correct_accepted"] + counts["incorrect_accepted"]

metrics = {
    "total_scored": total,
    "raw_accuracy": correct / total if total else None,
    "validation_accepted": accepted,
    **counts,
}

with (folder / "metrics.json").open("w", encoding="utf-8") as file:
    json.dump(metrics, file, indent=2)

print(json.dumps(metrics, indent=2))        
