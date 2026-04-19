# 🧮 NeuroSymbolic Math Solver

**Neural understanding + Symbolic precision = Zero hallucination**

## What Is This?

A math solver that combines:
- **Google Gemini 1.5 Flash** (free API) — reads your problem, extracts intent, explains steps
- **SymPy** — exact symbolic algebra, calculus, limits, series
- **Matplotlib** — function plotting
- **SymPy + Z3** — algebraic proof verification
- **SciPy / NumPy** — numerical methods

**The LLM never computes the math.** It only understands your question and explains what the
symbolic engine computed. Results are verified before display.

---

## Prerequisites

| Requirement | Detail |
|---|---|
| **Google Colab** (recommended) | Free, no GPU needed |
| **Python 3.10+** | If running locally |
| **Gemini API Key** | Free at [aistudio.google.com](https://aistudio.google.com/app/apikey) — 1500 req/day |
| **GPU** | Not required — all heavy math runs on SymPy (CPU) |

---

## Quickest Start: Google Colab

1. Open [Google Colab](https://colab.research.google.com)
2. Upload `NeuroSymbolic_Math_Solver.ipynb`
3. Get your free Gemini API key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
4. Run all cells (Runtime → Run all)
5. Click the **public Gradio link** printed at the end

---

## Local Setup

```bash
# 1. Clone / download this project
cd neuro_symbolic_math

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python app.py
```

The app opens automatically and prints a public share link (`share=True`).

---

## Architecture

```
User Query (natural language)
        │
        ▼
  Gemini 1.5 Flash ──── Neural Parser (free API)
                         Extracts: problem_type, operation,
                         latex_expression, variables, etc.
        │
        ▼
  Symbolic Router ──── Rule-based, no LLM
        │
        ├── SymPy ────── Algebra: solve, factor, expand, simplify
        │                Calculus: diff, integrate, limit, series
        │
        ├── Matplotlib ── Function plotting (lambdify → numpy)
        │
        ├── SymPy + Z3 ── Proof: expand, trigsimp, numerical test
        │
        └── SciPy ──── Numerical root finding, eigenvalues
        │
        ▼
  Verifier ──── Back-substitution, derivative check, numerical cross-check
        │
        ▼
  Gemini 1.5 Flash ──── Step Explainer (free API)
                         Narrates symbolic steps — never recomputes
        │
        ▼
  Gradio UI ──── Answer + graph + explanation + pipeline status
```

---

## Supported Problems

| Category | Examples |
|---|---|
| Algebra | `Solve x^3 - 6x^2 + 11x - 6 = 0` |
| Calculus | `Integrate x^2 * sin(x) dx` |
| Calculus | `Differentiate x^3 * ln(x)` |
| Limits | `Find limit of sin(x)/x as x→0` |
| Limits | `Find limit of (1+1/n)^n as n→∞` |
| Graphing | `Plot sin(x) + cos(2x) from -2pi to 2pi` |
| Graphing | `Plot x^3 - 3x from -3 to 3` |
| Factoring | `Factor x^4 - 16` |
| Expansion | `Expand (x+y)^5` |
| Series | `Find Taylor series of e^x` |
| Proof | `Prove (a+b)^2 = a^2 + 2ab + b^2` |
| Proof | `Prove sin^2(x) + cos^2(x) = 1` |
| Simplify | `Simplify sin^2(x)/cos(x) + cos(x)` |

---

## File Structure

```
neuro_symbolic_math/
├── app.py                       ← Main Gradio app (run this)
├── requirements.txt
├── NeuroSymbolic_Math_Solver.ipynb  ← Google Colab notebook (all-in-one)
├── README.md
└── solver/
    ├── __init__.py
    ├── parser.py                ← Gemini neural parser
    ├── router.py                ← Rule-based engine dispatcher
    ├── verifier.py              ← Back-substitution verifier
    ├── explainer.py             ← Gemini step explainer
    └── engines/
        ├── __init__.py
        ├── algebra.py           ← SymPy algebra + calculus
        ├── plotter.py           ← Matplotlib graphs
        ├── prover.py            ← SymPy + Z3 proofs
        └── numerical.py         ← SciPy numerical methods
```

---

## Demo Script (5 examples, ~10 minutes)

Walk through these in order to show each engine:

1. **Calculus** — `Integrate x^2 * sin(x) dx`
   - Shows: integration by parts, LaTeX result, derivative verification

2. **Algebra** — `Solve x^3 - 6x^2 + 11x - 6 = 0`
   - Shows: polynomial roots, back-substitution verification

3. **Limits** — `Find the limit of (1+1/n)^n as n approaches infinity`
   - Shows: SymPy returns `e` exactly, Gemini explains Euler's number

4. **Graphing** — `Plot sin(x)/x from -4pi to 4pi`
   - Shows: sinc function, Matplotlib engine, beautiful graph

5. **Proof** — `Prove (a+b)^2 = a^2 + 2ab + b^2`
   - Shows: SymPy expand → zero, proof verified, explanation

**Key message:** Point out the pipeline status panel — the LLM fires twice (parse + explain)
but the SymPy engine does ALL the computation.

---

## Free API Limits (Gemini)

| Model | Free limit |
|---|---|
| gemini-1.5-flash | **1,500 requests/day**, 15 req/min |
| gemini-1.5-pro | 50 requests/day |

We use `gemini-1.5-flash` — more than enough for demos and student use.
Get your key at: https://aistudio.google.com/app/apikey (no credit card required)
