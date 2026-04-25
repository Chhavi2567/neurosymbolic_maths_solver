from .engines import algebra, plotter, prover, numerical

PLOT_OPS = {"plot"}

PROOF_OPS = {"prove"}

NUMERICAL_OPS = {"numerical_solve", "eigenvalue", "determinant", "matrix_multiply"}

NUMERICAL_TYPES = {"linear_algebra", "numerical"}

SYMBOLIC_OPS = {
    "solve", "differentiate", "integrate", "limit",
    "simplify", "factor", "expand", "series", "sum",
}


def route(parsed: dict) -> dict:
    op        = parsed.get("operation", "simplify")
    ptype     = parsed.get("problem_type", "algebra")
    is_proof  = parsed.get("is_proof", False)

    if is_proof or op in PROOF_OPS or ptype == "proof":
        return prover.run(parsed)

    if op in PLOT_OPS or ptype == "graphing":
        return plotter.run(parsed)

    if op in NUMERICAL_OPS or ptype in NUMERICAL_TYPES:
        return numerical.run(parsed)

    return algebra.run(parsed)
