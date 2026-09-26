# AI Math Tutor

> **An AI-powered mathematics tutor designed to solve, verify, explain, and eventually visually teach mathematical problems — not simply generate an answer.**

## Overview

AI Math Tutor is an ongoing project focused on building a more reliable and educational mathematics tutoring system around large language models.

The central idea is simple: **an LLM should not be trusted as the only source of mathematical truth.**

A language model can produce fluent explanations while still making mathematical, structural, or formatting mistakes. This project therefore combines LLM-generated explanations with deterministic mathematical computation, structured-output handling, validation, and conversation context.

The long-term goal is to create a tutor that can:

1. Understand a student's mathematical question.
2. Compute an independent ground-truth answer where possible.
3. Generate a clear step-by-step explanation.
4. Validate the generated result and mathematical transitions.
5. Remember the previous problem so students can ask follow-up questions.
6. Send normalized mathematical steps to the frontend.
7. Visually teach those validated steps through an interactive whiteboard.

---

## Why I Built This

Many AI systems can answer mathematics questions, but a correct final answer alone does not make a good tutor.

For example, returning:

```text
x = ±1, ±3
```

may be correct, but a student needs to understand **why** those values are the solutions.

The engineering challenge is therefore not just:

```text
Question → LLM → Answer
```

Instead, I am building toward:

```text
Question
   ↓
Input Processing
   ↓
Problem Classification
   ↓
Deterministic Ground Truth
   ↓
Prompt Routing
   ↓
LLM Step Generation
   ↓
Structured Output Parsing
   ↓
Schema Validation
   ↓
Mathematical Validation
   ↓
Conversation Memory
   ↓
Normalized API Response
   ↓
Frontend
   ↓
Interactive Whiteboard
```

The product is being designed around four principles:

**Correctness + Explainability + Reliability + Visual Learning**

---

## Core Architecture

### 1. Mathematical Input Processing

User input is cleaned and normalized before mathematical processing.

The preprocessing layer distinguishes between natural-language phrases and mathematical expressions so that transformations do not accidentally corrupt the original question.

### 2. Problem Classification & Prompt Routing

Questions are classified so the system can choose an appropriate solving/explanation strategy instead of sending every problem through one generic prompt.

The routing architecture is intended to support different mathematical categories such as equations, arithmetic, polynomial problems, calculus, logarithms, trigonometry, and conceptual follow-up questions.

### 3. Deterministic Ground Truth

Where possible, the system calculates an independent mathematical result using deterministic tools such as **SymPy**.

This gives the application a reference answer that is independent of the LLM.

```text
Student Question
      ↓
Deterministic Solver
      ↓
Ground Truth
```

The LLM is then used primarily for explanation and tutoring rather than being blindly trusted for correctness.

### 4. Structured LLM Step Generation

The model is instructed to return predictable structured data containing mathematical steps and a final answer.

Example:

```json
{
  "steps": [
    {
      "text": "Factor the equation",
      "expression": "(x^2-1)(x^2-9)=0"
    },
    {
      "text": "Solve each factor",
      "expression": "x=±1, ±3"
    }
  ],
  "final_answer": [-3, -1, 1, 3]
}
```

Structured steps are important because the output is consumed by validation logic and will ultimately drive the visual whiteboard.

### 5. JSON Extraction & Recovery

LLMs do not always produce perfectly valid structured output.

The pipeline therefore treats model output as **untrusted data**.

```text
LLM Output
    ↓
JSON Extraction
    ↓
Repair / Recovery
    ↓
Schema Validation
    ↓
Mathematical Validation
```

This prevents malformed model responses from being passed directly into downstream components.

### 6. Mathematical Validation

Generated answers are compared against independently computed results where possible.

The validation work includes mechanisms such as:

- ground-truth comparison
- answer normalization
- substitution-based verification
- algebraic transition validation
- structured step validation

The aim is to separate **generation** from **verification**.

```text
LLM → Candidate Explanation
              ↓
      Mathematical Validator
              ↓
       Verified Response
```

### 7. Conversation Memory

The tutor supports contextual follow-up questions.

For example:

```text
Student: What is 2 + 2?
Tutor: 4

Student: Why 4?
```

The second question cannot be understood properly in isolation.

The system therefore stores validated information such as:

```python
{
    "previous_question": "...",
    "previous_answer": "...",
    "previous_steps": [...]
}
```

Memory is updated **after validation**, helping prevent an incorrect generated answer from becoming trusted context for the next interaction.

### 8. Streaming API

The backend includes a streaming solution flow so explanation content can be delivered progressively rather than forcing the user to wait for the entire generation process.

A key design requirement is that memory and validation operate on the completed response rather than incomplete streaming chunks.

### 9. Frontend & Mathematical Rendering

The frontend consumes normalized backend data rather than raw LLM text.

Mathematical expressions can be rendered using LaTeX/KaTeX-compatible formatting.

This creates a stable contract between:

```text
AI Generation → Validation → API → UI
```

### 10. Interactive Whiteboard — In Development

The next major product layer is the visual teaching system.

Instead of only displaying text steps, the goal is for the tutor to progressively illustrate validated mathematical transformations on a whiteboard.

Conceptually:

```text
Validated Step 1
      ↓
Whiteboard Animation

Validated Step 2
      ↓
Whiteboard Animation

Validated Step 3
      ↓
Final Visual Solution
```

This is intended to move the product from an AI **answer generator** toward an AI **teaching experience**.

---

## Reliability Philosophy

One of the biggest lessons from developing this project is:

> **A confident LLM response is not the same as a verified mathematical response.**

The architecture therefore avoids relying on a single model call.

The current direction separates responsibilities across:

- classification
- deterministic solving
- prompt routing
- generation
- parsing
- schema validation
- mathematical verification
- memory
- rendering

This separation also makes individual failures easier to identify, test, and improve.

---

## Development Progress

### Implemented / Working

- [x] FastAPI-based math solving backend
- [x] Streaming solution endpoint
- [x] Mathematical input normalization
- [x] Problem classification and prompt routing
- [x] LLM-generated step-by-step explanations
- [x] Structured step/final-answer schema
- [x] SymPy-backed ground-truth computation
- [x] Answer comparison and validation
- [x] Substitution-based verification
- [x] Mathematical transition/step validation work
- [x] JSON extraction and malformed-output recovery
- [x] Normalized backend-to-frontend response flow
- [x] Conversation memory for contextual follow-up questions
- [x] Validation-before-memory-update logic
- [x] LaTeX/KaTeX mathematical rendering work
- [x] Experimentation with multiple LLM APIs/models

### Currently Improving

- [ ] More detailed and pedagogically useful step generation
- [ ] Stronger validation across different mathematical problem types
- [ ] More robust structured-output recovery
- [ ] Better LaTeX handling
- [ ] Error handling and fallback strategies
- [ ] Larger evaluation/test set
- [ ] Measurement of both mathematical correctness and explanation quality

### Next Major Milestone

- [ ] Connect validated solution steps to the interactive whiteboard
- [ ] Animate mathematical transformations progressively
- [ ] Improve visual explanations for different problem categories
- [ ] Build a complete end-to-end tutoring experience
- [ ] Add a public product demo

---

## Example Goal

For a problem such as:

```text
x⁴ - 10x² + 9 = 0
```

the goal is not merely to output:

```text
x = ±1, ±3
```

The tutor should progressively explain the structure of the equation, show the factorisation, apply the zero-product rule, solve the resulting factors, validate the solutions, and eventually visualize those transformations on the whiteboard.

---

## Tech Stack

- **Python**
- **FastAPI**
- **SymPy**
- **LLM APIs**
- **Server-Sent Events / Streaming**
- **JSON structured outputs**
- **LaTeX / KaTeX**
- **Frontend whiteboard / Canvas**
- **Git & GitHub**

---

## Current Project Direction

The project started as an experiment in AI-generated mathematics solutions.

It is evolving into a reliability-focused tutoring architecture where the LLM is only one component of the system.

The target is:

```text
Generate
   +
Verify
   +
Explain
   +
Remember
   +
Visualize
   =
AI Math Tutor
```

The next major focus is the **interactive whiteboard explanation layer** and systematic evaluation of the complete tutoring pipeline.

---

## Demo

> 

https://github.com/user-attachments/assets/cdd30b74-c9b4-487a-be60-186c9e4cba64



A product demonstration will be added here once the next end-to-end version of the tutor and whiteboard experience is ready.

---

## Status

🚧 **Active Development**

This repository documents the ongoing development version of AI Math Tutor. The architecture and implementation will continue to evolve as validation, explanation quality, evaluation, and visual teaching capabilities improve.
