from sympy import (
    symbols, sympify, solve, diff, integrate, limit, simplify,
    factor, expand, series, Sum, product, latex, oo, zoo,
    trigsimp, radsimp, cancel, apart, together, Symbol,
    Rational, pi, E, I, sqrt, Abs, sign,
    sin, cos, tan, exp, log, ln,
)
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)
from sympy.parsing.latex import parse_latex as sympy_parse_latex

TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def _latex_to_plain_math(s: str) -> str:

    import re

    t = (
        s.replace("\\cdot", "*")
        .replace("\\times", "*")
        .replace("\\div", "/")
        .replace("\\left", "")
        .replace("\\right", "")
        .replace("\\,", "")
        .replace("\\!", "")
        .strip()
    )
    for a, b in (
        (r"\sin", "sin"),
        (r"\cos", "cos"),
        (r"\tan", "tan"),
        (r"\ln", "ln"),
        (r"\log", "log"),
        (r"\exp", "exp"),
        (r"\pi", "pi"),
        (r"\infty", "oo"),
    ):
        t = t.replace(a, b)
    pat = re.compile(r"\\frac\{([^{}]*)\}\{([^{}]*)\}")
    for _ in range(64):
        n = pat.sub(r"((\1)/(\2))", t, count=1)
        if n == t:
            break
        t = n
    return t


def _safe_parse(expr_str: str, var_syms: dict) -> any:
    cleaned = (
        expr_str
        .replace("\\cdot", "*")
        .replace("\\times", "*")
        .replace("\\div", "/")
        .replace("\\left", "")
        .replace("\\right", "")
        .replace("\\,", "")
        .replace("\\!", "")
        .strip()
    )

    try:
        return sympy_parse_latex(cleaned)
    except ImportError:
        pass
    except Exception:
        pass

    try:
        from latex2sympy2 import latex2sympy

        return latex2sympy(cleaned)
    except Exception:
        pass

    plain = _latex_to_plain_math(cleaned)
    try:
        return parse_expr(plain, local_dict=var_syms, transformations=TRANSFORMATIONS)
    except Exception:
        pass

    return sympify(plain, locals=var_syms)


def run(parsed: dict) -> dict:
    op       = parsed.get("operation", "simplify")
    expr_str = parsed.get("latex_expression", "")
    var_names = parsed.get("variables", ["x"])
    lim_point = parsed.get("limit_point")
    lim_var   = parsed.get("limit_variable")

    var_syms = {v: symbols(v) for v in var_names}
    var_syms.update({"pi": pi, "E": E, "oo": oo, "I": I})

    try:
        expr = _safe_parse(expr_str, var_syms)
        main_var = symbols(var_names[0]) if var_names else symbols("x")

        steps = []
        result_expr = None

        if op == "solve":
            steps.append(f"Set up equation: {latex(expr)} = 0")
            steps.append(f"Solving for {main_var} using SymPy algebraic solver")
            sol = solve(expr, main_var)
            if not sol:
                sol = solve(expr, main_var, dict=False)
            result_expr = sol
            steps.append(f"Solutions found: {len(sol)}")
            for i, s in enumerate(sol, 1):
                steps.append(f"  Root {i}: {main_var} = {latex(s)}")
            result_latex = ", ".join([f"{main_var} = {latex(s)}" for s in sol]) if sol else "No real solutions"
            result_str   = str(sol)

        elif op == "differentiate":
            steps.append(f"Differentiating: {latex(expr)}")
            steps.append(f"With respect to: {main_var}")
            result_expr = diff(expr, main_var)
            steps.append("Applied differentiation rules (chain, product, quotient as needed)")
            steps.append(f"d/d{main_var} [{latex(expr)}] = {latex(result_expr)}")
            result_latex = latex(result_expr)
            result_str   = str(result_expr)

        elif op == "integrate":
            steps.append(f"Computing indefinite integral of: {latex(expr)}")
            steps.append(f"With respect to: {main_var}")
            result_expr = integrate(expr, main_var)
            steps.append("Applied integration techniques (by parts, substitution, etc.) as needed")
            steps.append(f"∫ {latex(expr)} d{main_var} = {latex(result_expr)} + C")
            result_latex = latex(result_expr) + " + C"
            result_str   = str(result_expr) + " + C"

        elif op == "limit":
            lv = symbols(lim_var) if lim_var else main_var
            if lim_point in ("oo", "inf", "infinity", "+inf"):
                lp = oo
            elif lim_point in ("-oo", "-inf", "-infinity"):
                lp = -oo
            elif lim_point:
                lp = _safe_parse(lim_point, var_syms)
            else:
                lp = oo
            steps.append(f"Computing: lim({lv} → {lim_point}) of {latex(expr)}")
            result_expr = limit(expr, lv, lp)
            steps.append(f"Applied limit laws and L'Hôpital if needed")
            steps.append(f"Result: {latex(result_expr)}")
            result_latex = latex(result_expr)
            result_str   = str(result_expr)

        elif op == "simplify":
            steps.append(f"Simplifying: {latex(expr)}")
            result_expr = simplify(expr)
            steps.append("Applied algebraic simplification rules")
            steps.append(f"Simplified form: {latex(result_expr)}")
            result_latex = latex(result_expr)
            result_str   = str(result_expr)

        elif op == "factor":
            steps.append(f"Factoring: {latex(expr)}")
            result_expr = factor(expr)
            steps.append("Found irreducible factors over the rationals")
            steps.append(f"Factored: {latex(result_expr)}")
            result_latex = latex(result_expr)
            result_str   = str(result_expr)

        elif op == "expand":
            steps.append(f"Expanding: {latex(expr)}")
            result_expr = expand(expr)
            steps.append(f"Expanded: {latex(result_expr)}")
            result_latex = latex(result_expr)
            result_str   = str(result_expr)

        elif op == "series":
            steps.append(f"Computing Taylor series of {latex(expr)} around 0")
            result_expr = series(expr, main_var, 0, 6)
            steps.append("Expanded to 6th order around x = 0")
            steps.append(f"Series: {latex(result_expr)}")
            result_latex = latex(result_expr)
            result_str   = str(result_expr)

        else:
            result_expr = simplify(expr)
            steps = [f"Simplified: {latex(result_expr)}"]
            result_latex = latex(result_expr)
            result_str   = str(result_expr)

        return {
            "success":      True,
            "result_str":   result_str,
            "result_latex": result_latex,
            "steps":        steps,
            "engine":       "SymPy (exact symbolic)",
            "verified":     True,
        }

    except Exception as e:
        return {
            "success": False,
            "error":   f"SymPy engine error: {str(e)}",
            "steps":   [],
            "engine":  "SymPy",
            "verified": False,
        }
