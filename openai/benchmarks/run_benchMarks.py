import json
import argparse
import hashlib
import sys
from pathlib import Path

# Direct script runs need the project folder to find the sibling Services package.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Services.Load_Model import stream_tutor

parser = argparse.ArgumentParser()
parser.add_argument('--cases', default='cases.json', help='Dataset filename in benchmarks')
args = parser.parse_args()
cases_path = Path(__file__).resolve().parent / args.cases
dataset_hash = hashlib.sha256(cases_path.read_bytes()).hexdigest()

with cases_path.open(encoding="utf-8") as file:
    cases=json.load(file)

print(f"Loaded {len(cases)} cases")  

for case in cases:
    print(f"{case['id']}: {case['question']}")


def build_benchmark_prompt(question):
    return f"""
Solve this math problem: {question}

Return only valid JSON with this structure:
{{
    "steps": [{{"text": "Explain a solution step"}}],
    "final_answer": [0]
}}
Replace the example step and answer with your solution.
List all distinct real solutions for equations. Use JSON numbers for answers,
including decimals for fractions. Do not repeat roots.
"""


   

output_path = cases_path.with_name('responses.jsonl' if cases_path.name == 'cases.json'
                                  else f'{cases_path.stem}_responses.jsonl')

completed_ids = set()

if output_path.exists():
    with output_path.open(encoding="utf-8") as file:
        for line in file:
            if line.strip():
                record = json.loads(line)
                if record.get('dataset_hash', dataset_hash) != dataset_hash:
                    raise ValueError('Dataset changed: use a new response file.')
                completed_ids.add(record["id"])

with output_path.open("a", encoding="utf-8") as file:
    for case in cases:
        if case["id"] in completed_ids:
            print(f"Skipping {case['id']} (already completed)")
            continue

        prompt = build_benchmark_prompt(case["question"])
        raw_response = "".join(stream_tutor(prompt))

        record = {
            "id": case["id"],
            "question": case["question"],
            "raw_response": raw_response,
            "dataset_hash": dataset_hash,
        }

        file.write(json.dumps(record) + "\n")
        file.flush()
        completed_ids.add(case["id"])

        print(f"Saved {case['id']}")

