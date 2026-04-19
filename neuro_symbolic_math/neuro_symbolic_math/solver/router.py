"""
router.py  —  Symbolic dispatcher
Reads the parsed problem dict from the neural layer
and routes it to the correct symbolic engine.
No LLM involved here — pure rule-based dispatch.
"""

from .engines import algebra, plotter, prover, numerical

# Operations that always go to the plotter
PLOT_OPS = {"plot"}

# Operations that always go to the proof engine
PROOF_OPS = {"prove"}

# Operations that prefer numerical engine
NUMERICAL_OPS = {"numerical_solve", "eigenvalue", "determinant", "matrix_multiply"}

# Problem types that prefer numerical engine
NUMERICAL_TYPES = {"linear_algebra", "numerical"}

# Operations handled by algebra/calculus engine
SYMBOLIC_OPS = {
    "solve", "differentiate", "integrate", "limit",
    "simplify", "factor", "expand", "series", "sum",
}


def route(parsed: dict) -> dict:
    """
    Route a parsed problem to the right engine.
    Returns the engine's result dict.
    """
    op        = parsed.get("operation", "simplify")
    ptype     = parsed.get("problem_type", "algebra")
    is_proof  = parsed.get("is_proof", False)

    # ── Proof ──────────────────────────────────────────────────────
    if is_proof or op in PROOF_OPS or ptype == "proof":
        return prover.run(parsed)

    # ── Graphing ───────────────────────────────────────────────────
    if op in PLOT_OPS or ptype == "graphing":
        return plotter.run(parsed)

    # ── Numerical / Linear Algebra ─────────────────────────────────
    if op in NUMERICAL_OPS or ptype in NUMERICAL_TYPES:
        return numerical.run(parsed)

    # ── Symbolic algebra / calculus (default) ─────────────────────
    return algebra.run(parsed)
