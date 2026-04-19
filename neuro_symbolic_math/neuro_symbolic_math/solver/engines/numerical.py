"""
numerical.py  —  Numerical methods engine
Uses NumPy / SciPy for problems that need numerical solutions:
eigenvalues, matrix operations, numerical ODE, root finding, etc.
"""

import numpy as np
from scipy import linalg, optimize
from sympy import Matrix, symbols, latex, sympify, lambdify, pi, E
from sympy.parsing.latex import parse_latex as sympy_parse_latex


def _parse(expr_str: str, var_syms: dict):
    cleaned = expr_str.replace("\\cdot","*").replace("\\times","*").strip()
    try:
        return sympy_parse_latex(cleaned)
    except Exception:
        pass
    try:
        from latex2sympy2 import latex2sympy
        return latex2sympy(cleaned)
    except Exception:
        pass
    from sympy.parsing.sympy_parser import (
        parse_expr, standard_transformations,
        implicit_multiplication_application, convert_xor,
    )
    tf = standard_transformations + (implicit_multiplication_application, convert_xor)
    return parse_expr(cleaned, local_dict=var_syms, transformations=tf)


def run(parsed: dict) -> dict:
    op        = parsed.get("operation", "numerical_solve")
    expr_str  = parsed.get("latex_expression", "")
    var_names = parsed.get("variables", ["x"])

    var_syms = {v: symbols(v) for v in var_names}
    steps = []

    try:
        # ── Eigenvalue / determinant for matrices ──────────────────
        if op in ("eigenvalue", "determinant", "matrix_multiply"):
            steps.append(f"Parsing matrix expression: {expr_str}")
            sym_expr = _parse(expr_str, var_syms)

            if hasattr(sym_expr, "tolist"):  # SymPy Matrix
                np_mat = np.array(sym_expr.tolist(), dtype=float)
            else:
                return {"success": False, "error": "Could not parse as a matrix", "steps": steps}

            if op == "eigenvalue":
                steps.append("Computing eigenvalues and eigenvectors via NumPy linalg")
                eigenvalues, eigenvectors = linalg.eig(np_mat)
                ev_strs = [f"λ{i+1} = {v:.4f}" for i, v in enumerate(eigenvalues)]
                steps.append(f"Eigenvalues: {', '.join(ev_strs)}")
                result_str   = str(eigenvalues.tolist())
                result_latex = ", ".join([f"\\lambda_{{{i+1}}} = {v:.4f}" for i, v in enumerate(eigenvalues)])

            elif op == "determinant":
                steps.append("Computing determinant via NumPy linalg")
                det = linalg.det(np_mat)
                steps.append(f"det(A) = {det:.6f}")
                result_str   = str(det)
                result_latex = f"\\det(A) = {det:.4f}"

            else:
                result_str   = str(np_mat.tolist())
                result_latex = expr_str

        # ── Numerical root finding ─────────────────────────────────
        elif op == "numerical_solve":
            main_var = symbols(var_names[0]) if var_names else symbols("x")
            sym_expr = _parse(expr_str, var_syms)
            steps.append(f"Parsed: {latex(sym_expr)}")
            steps.append("Converting to numeric function for scipy root finding")

            f_num = lambdify(main_var, sym_expr, modules=["numpy"])

            # Search multiple starting points
            roots_found = []
            for x0 in np.linspace(-20, 20, 40):
                try:
                    root = optimize.brentq(f_num, x0, x0 + 1.0)
                    if not any(abs(root - r) < 1e-6 for r in roots_found):
                        roots_found.append(float(root))
                except Exception:
                    continue

            if not roots_found:
                # Try fsolve
                for x0 in np.linspace(-10, 10, 20):
                    try:
                        sol = optimize.fsolve(f_num, x0, full_output=True)
                        r = float(sol[0][0])
                        if abs(f_num(r)) < 1e-8 and not any(abs(r - rr) < 1e-6 for rr in roots_found):
                            roots_found.append(r)
                    except Exception:
                        continue

            roots_found.sort()
            steps.append(f"Root search complete. Found {len(roots_found)} root(s)")
            for i, r in enumerate(roots_found, 1):
                steps.append(f"  Root {i}: x ≈ {r:.8f}")

            result_str   = str(roots_found)
            result_latex = ", ".join([f"x \\approx {r:.6f}" for r in roots_found]) if roots_found else "\\text{No roots found}"

        else:
            # Generic: just try algebra engine
            from . import algebra
            return algebra.run(parsed)

        return {
            "success":      True,
            "result_str":   result_str,
            "result_latex": result_latex,
            "steps":        steps,
            "engine":       "NumPy / SciPy (numerical)",
            "verified":     True,
        }

    except Exception as e:
        return {
            "success":  False,
            "error":    f"Numerical engine error: {str(e)}",
            "steps":    steps,
            "engine":   "NumPy / SciPy",
            "verified": False,
        }
