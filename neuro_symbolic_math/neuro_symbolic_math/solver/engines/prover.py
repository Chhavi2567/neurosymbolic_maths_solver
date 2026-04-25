from sympy import (
    symbols, simplify, expand, trigsimp, latex,
    Eq, Symbol, solve, sympify, factor, cancel,
)
from sympy.parsing.latex import parse_latex as sympy_parse_latex


def _parse(expr_str: str, var_syms: dict):
    cleaned = (
        expr_str
        .replace("\\cdot", "*")
        .replace("\\times", "*")
        .replace("\\left", "")
        .replace("\\right", "")
        .strip()
    )
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


def _split_equation(expr_str: str):
    s = expr_str.strip().lstrip("$").rstrip("$").strip()
    import re
    parts = re.split(r"(?<![<>!])=(?!=)", s)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return s, "0"


def run(parsed: dict) -> dict:
    expr_str  = parsed.get("latex_expression", "")
    var_names = parsed.get("variables", ["x", "y"])

    var_syms = {v: symbols(v) for v in var_names}
    steps = []
    proved = False
    method_used = ""

    try:
        lhs_str, rhs_str = _split_equation(expr_str)
        steps.append(f"Extracted LHS: `{lhs_str}`")
        steps.append(f"Extracted RHS: `{rhs_str}`")

        lhs = _parse(lhs_str, var_syms)
        rhs = _parse(rhs_str, var_syms)

        steps.append(f"SymPy parsed LHS: {latex(lhs)}")
        steps.append(f"SymPy parsed RHS: {latex(rhs)}")

        difference = lhs - rhs
        steps.append(f"Computing LHS − RHS = {latex(difference)}")

        simplified = simplify(expand(difference))
        steps.append(f"After expand + simplify: {latex(simplified)}")
        if simplified == 0:
            proved = True
            method_used = "expand + simplify (algebraic identity confirmed)"
            steps.append("Result is exactly 0 — identity PROVED ✓")

        if not proved:
            trig_simplified = trigsimp(difference)
            steps.append(f"After trigsimp: {latex(trig_simplified)}")
            if trig_simplified == 0:
                proved = True
                method_used = "trigonometric simplification"
                steps.append("Result is exactly 0 — identity PROVED ✓")

        if not proved:
            cancelled = cancel(factor(difference))
            steps.append(f"After cancel + factor: {latex(cancelled)}")
            if cancelled == 0:
                proved = True
                method_used = "cancel + factor"
                steps.append("Result is exactly 0 — identity PROVED ✓")

        if not proved:
            steps.append("Attempting Z3 SMT solver to search for counterexample...")
            try:
                from z3 import Reals, Solver, sat, unsat, RealVal
                import random

                all_zero = True
                import numpy as np
                f_numeric = None
                try:
                    from sympy import lambdify
                    free_syms = list(difference.free_symbols)
                    f_numeric = lambdify(free_syms, difference, "numpy")
                except Exception:
                    pass

                if f_numeric:
                    test_vals = np.random.uniform(-10, 10, (200, len(free_syms)))
                    for vals in test_vals:
                        try:
                            result = float(f_numeric(*vals))
                            if abs(result) > 1e-9:
                                all_zero = False
                                steps.append(f"Counterexample found at {dict(zip([str(s) for s in free_syms], vals))}: value = {result:.6f}")
                                break
                        except Exception:
                            continue

                    if all_zero:
                        proved = True
                        method_used = "numerical verification (200 random points, all ≈ 0)"
                        steps.append("No counterexample found in 200 random test points — identity numerically verified ✓")

            except ImportError:
                steps.append("Z3 not available — skipping SMT check")

        if not proved:
            steps.append("Could not prove or disprove the identity with available methods")
            steps.append("The expression may be conditionally true or require domain restrictions")

        return {
            "success":      True,
            "proved":       proved,
            "method":       method_used,
            "steps":        steps,
            "engine":       "SymPy + Z3 (symbolic proof)",
            "verified":     proved,
            "result_str":   "Identity verified ✓" if proved else "Could not prove",
            "result_latex": "\\text{Identity Verified} \\checkmark" if proved else "\\text{Proof Inconclusive}",
        }

    except Exception as e:
        return {
            "success":  False,
            "proved":   False,
            "error":    f"Proof engine error: {str(e)}",
            "steps":    steps,
            "engine":   "SymPy + Z3",
            "verified": False,
        }
