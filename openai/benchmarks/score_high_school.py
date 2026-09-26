"""Score saved responses without model calls or the validator's answer comparator."""
import contextlib
import io
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Services.ValidationChecker import compute_ground_truth, validate_solution
from Services.problemTypeDetector import classify

folder = Path(__file__).resolve().parent
cases = json.loads((folder / 'high_school_100.json').read_text(encoding='utf-8'))
by_id = {case['id']: case for case in cases}
keys = ['correct_accepted', 'correct_rejected', 'incorrect_accepted', 'incorrect_rejected']
counts = dict.fromkeys(keys, 0)
topics = {}
details = []
seen = set()

def numeric_answers(value):
    if not isinstance(value, list) or not value:
        raise ValueError('final_answer must be a nonempty list of finite JSON numbers')
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in value):
        raise ValueError('final_answer must contain finite JSON numbers')
    return sorted(set(value))

for line in (folder / 'high_school_100_responses.jsonl').read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    record = json.loads(line)
    case = by_id[record['id']]
    if case['id'] in seen:
        raise ValueError(f"Duplicate response: {case['id']}")
    if record['question'] != case['question']:
        raise ValueError(f"Question changed: {case['id']}")
    seen.add(case['id'])
    parse_error = None
    parsed = {}
    try:
        parsed = json.loads(record['raw_response'])
        answers = numeric_answers(parsed['final_answer'])
        expected = numeric_answers(case['expected'])
        correct = len(answers) == len(expected) and all(
            math.isclose(a, b, rel_tol=0, abs_tol=1e-6) for a, b in zip(answers, expected))
    except (ValueError, TypeError, KeyError) as error:
        parse_error = str(error)
        correct = False
        parsed = {}
    with contextlib.redirect_stdout(io.StringIO()):
        validation = validate_solution(case['question'], parsed,
            compute_ground_truth(question=case['question']), classify(case['question']))
    accepted = validation['valid']
    outcome = ('correct' if correct else 'incorrect') + ('_accepted' if accepted else '_rejected')
    counts[outcome] += 1
    topic = topics.setdefault(case['topic'], dict.fromkeys(keys, 0))
    topic[outcome] += 1
    details.append({'id': case['id'], 'expected': case['expected'],
                    'model_answer': parsed.get('final_answer'), 'outcome': outcome,
                    'parse_error': parse_error, 'validation_reason': validation['reason']})

total = len(details)
correct_count = counts['correct_accepted'] + counts['correct_rejected']
wrong_count = total - correct_count
metrics = {
    'dataset_size': len(cases), 'total_scored': total,
    'missing_ids': sorted(set(by_id) - seen),
    'raw_accuracy': correct_count / total if total else None,
    'validation_accepted': counts['correct_accepted'] + counts['incorrect_accepted'],
    **counts,
    'parse_errors': sum(row['parse_error'] is not None for row in details),
    'incorrect_rejection_rate': counts['incorrect_rejected'] / wrong_count if wrong_count else None,
    'by_topic': topics,
}
(folder / 'high_school_100_metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
(folder / 'high_school_100_scores.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
print(json.dumps(metrics, indent=2))
