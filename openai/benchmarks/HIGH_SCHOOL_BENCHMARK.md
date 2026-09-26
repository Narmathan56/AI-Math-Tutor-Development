# High-school algebra benchmark

`high_school_100.json` is an original, synthetic practice dataset, not a downloaded
exam dataset or a representative measure of the full high-school curriculum.
It contains ten questions per topic: order of operations, fractions, powers,
linear equations, bracketed linear equations, equations with x on both sides,
fractional linear equations, quadratics, repeated roots, and cubics.
Questions within a topic share construction patterns. Geometry, statistics,
proofs, word problems, and complex solutions are outside this version's scope.

`build_high_school_cases.py` derives keys using integer/rational arithmetic and
chosen roots, independently of the model and production solver. Keys were also
cross-checked against the production solver. That cross-check is not evidence
of model accuracy.

From C:\openai:

```powershell
python openai/benchmarks/run_benchMarks.py --cases high_school_100.json
python openai/benchmarks/score_high_school.py
```

Generation sends only questions and output instructions, saves each response,
and skips saved IDs on reruns. Do not mix model or prompt changes in the same
response file; start a new results file when generation settings change.
The original eight-case artifacts are separate.

Scoring uses independent dataset keys, unordered distinct numeric answers, and
absolute tolerance 1e-6. Strict JSON/schema failures count as raw failures and
are reported separately; they are passed to validation as an empty response.
These counts therefore measure the full response contract, not only math skill.
The existing validator has its own comparison rules and is not modified.

Outputs: `high_school_100_metrics.json` (totals, missing cases, topics) and
`high_school_100_scores.json` (per-case decisions and parsing errors).
An incorrect-rejection rate of null means there were no incorrect responses;
it is not evidence of perfect rejection. API errors stop generation and are
not counted as incorrect answers; completed records remain available to resume.
