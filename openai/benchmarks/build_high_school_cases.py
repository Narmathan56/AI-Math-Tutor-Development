"""Build original cases with answers derived independently of the tutor solver."""
import json
from fractions import Fraction
from pathlib import Path

cases = []

def add(topic, question, answers):
    index = sum(case['topic'] == topic for case in cases) + 1
    cases.append({
        'id': f'hs_{topic}_{index:02d}', 'topic': topic,
        'question': question, 'expected': sorted(set(float(a) for a in answers)),
    })

for i in range(1, 11):
    add('order_of_operations', f'({i + 3} - {2*i}) * ({i} + 4) + {i}^2',
        [(3-i)*(i+4)+i*i])
    add('fractions', f'{i}/4 + {i+1}/2 - {i+2}/8',
        [Fraction(i, 4)+Fraction(i+1, 2)-Fraction(i+2, 8)])
    add('powers', f'(-{i})^2 - 2^{i} + ({i+2})^0', [i*i-2**i+1])
    root = i-6
    add('linear', f'{i+1}*x + {i+3} = {(i+1)*root+i+3}', [root])
    add('linear_brackets', f'{i+2}*(x - {i}) = {(i+2)*(root-i)}', [root])
    add('linear_both_sides', f'{i+3}*x + {i} = 2*x + {(i+1)*root+i}', [root])
    half = Fraction(2*i-11, 2)
    add('fractional_linear', f'(x + {i})/3 = (2*x - {i})/5 + {Fraction(-half+8*i, 15)}', [half])
    a, b = -i, i+1
    add('quadratic', f'x^2 - x - {i*(i+1)} = 0', [a, b])
    add('repeated_root', f'x^2 - {2*i}*x + {i*i} = 0', [i])
    add('cubic', f'x^3 - {i}*x^2 - {i*i}*x + {i**3} = 0', [-i, i])

assert len(cases) == 100
assert len({c['question'] for c in cases}) == 100
destination = Path(__file__).with_name('high_school_100.json')
destination.write_text(json.dumps(cases, indent=2) + '\n', encoding='utf-8')
print(f'Wrote {len(cases)} original questions to {destination.name}')
