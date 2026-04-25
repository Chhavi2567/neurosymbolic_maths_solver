# NeuroSymbolic Math Solver

Math solver with structured parsing, symbolic computation, verification, and explanation.

## Requirements

| Requirement | Detail |
|---|---|
| **Python 3.10+** | Local runtime |
| **Gemini API Key** | Get at [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| **GPU** | Not required |

## Setup

```bash
cd neuro_symbolic_math
pip install -r requirements.txt
python app.py
```

The app launches locally and can generate a public share link (`share=True`).

## Architecture

```
User Query
   │
   ▼
Parser (Gemini API)
   │
   ▼
Router
   ├── SymPy (algebra, calculus, limits, series)
   ├── Matplotlib (graphing)
   ├── SymPy + Z3 (proof checks)
   └── NumPy / SciPy (numerical methods)
   │
   ▼
Verifier
   │
   ▼
Explainer (Gemini API)
   │
   ▼
Gradio UI
```

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

## File Structure

```
neuro_symbolic_math/
├── app.py
├── requirements.txt
├── README.md
└── solver/
    ├── __init__.py
    ├── parser.py
    ├── router.py
    ├── verifier.py
    ├── explainer.py
    └── engines/
        ├── __init__.py
        ├── algebra.py
        ├── plotter.py
        ├── prover.py
        └── numerical.py
```
