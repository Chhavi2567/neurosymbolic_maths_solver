"""
plotter.py  —  Graphing engine
Converts LaTeX expressions to numpy functions and renders
clean, publication-quality plots. Returns base64 PNG.
"""

import io
import base64
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from sympy import symbols, latex
from sympy.parsing.latex import parse_latex as sympy_parse_latex
from sympy import lambdify, pi, E, oo

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.alpha":       0.25,
    "grid.linewidth":   0.6,
    "figure.dpi":       150,
})

COLORS = ["#534AB7", "#D85A30", "#1D9E75", "#BA7517", "#185FA5"]


def _parse_to_sympy(expr_str: str, var: str):
    """Parse LaTeX or plain string to SymPy expression."""
    from sympy.parsing.sympy_parser import (
        parse_expr,
        standard_transformations,
        implicit_multiplication_application,
        convert_xor,
    )

    from solver.engines.algebra import _latex_to_plain_math

    cleaned = (
        expr_str
        .replace("\\cdot", "*")
        .replace("\\times", "*")
        .replace("\\left", "")
        .replace("\\right", "")
        .strip()
    )
    x = symbols(var)
    local_dict = {var: x, "pi": pi, "e": E, "oo": oo}
    tf = standard_transformations + (implicit_multiplication_application, convert_xor)

    try:
        return sympy_parse_latex(cleaned)
    except Exception:
        pass
    try:
        from latex2sympy2 import latex2sympy

        return latex2sympy(cleaned)
    except Exception:
        pass
    plain = _latex_to_plain_math(cleaned)
    return parse_expr(plain, local_dict=local_dict, transformations=tf)


def run(parsed: dict) -> dict:
    expr_str  = parsed.get("latex_expression", "x")
    var_names = parsed.get("variables", ["x"])
    plot_range = parsed.get("plot_range") or {}
    main_var  = var_names[0] if var_names else "x"

    xmin = float(plot_range.get("xmin", -10))
    xmax = float(plot_range.get("xmax", 10))

    steps = []

    try:
        sym_var = symbols(main_var)
        sym_expr = _parse_to_sympy(expr_str, main_var)
        steps.append(f"Parsed expression: {latex(sym_expr)}")

        # Build numeric function
        f_numeric = lambdify(sym_var, sym_expr, modules=["numpy"])
        x_vals = np.linspace(xmin, xmax, 2000)

        with np.errstate(divide="ignore", invalid="ignore"):
            y_vals = f_numeric(x_vals)
            y_vals = np.where(np.isfinite(y_vals), y_vals, np.nan)

        steps.append(f"Evaluated over [{xmin}, {xmax}] with 2000 points")

        # Clamp extreme y values for readability
        finite_y = y_vals[np.isfinite(y_vals)]
        if len(finite_y) > 0:
            p5, p95 = np.nanpercentile(finite_y, 5), np.nanpercentile(finite_y, 95)
            margin = max(abs(p95 - p5) * 1.3, 1.0)
            ymin_plot = p5 - margin
            ymax_plot = p95 + margin
        else:
            ymin_plot, ymax_plot = -10, 10

        steps.append(f"Auto-scaled y-axis for readability")

        # ── Plot ───────────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(9, 5))

        ax.plot(x_vals, y_vals, color=COLORS[0], linewidth=2.2, label=f"f({main_var}) = {expr_str}")

        ax.axhline(0, color="#888", linewidth=0.8, zorder=1)
        ax.axvline(0, color="#888", linewidth=0.8, zorder=1)

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin_plot, ymax_plot)
        ax.set_xlabel(main_var, fontsize=13)
        ax.set_ylabel(f"f({main_var})", fontsize=13)
        ax.set_title(f"Graph of  $f({main_var}) = {latex(sym_expr)}$", fontsize=14, pad=12)
        ax.legend(fontsize=11, framealpha=0.7)
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())

        plt.tight_layout()

        # Save to base64 PNG
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode()
        plt.close(fig)

        steps.append("Graph rendered successfully")

        return {
            "success":      True,
            "image_base64": img_b64,
            "steps":        steps,
            "engine":       "Matplotlib (exact lambdify)",
            "verified":     True,
            "result_latex": latex(sym_expr),
            "result_str":   str(sym_expr),
        }

    except Exception as e:
        return {
            "success": False,
            "error":   f"Plotting engine error: {str(e)}",
            "steps":   steps,
            "engine":  "Matplotlib",
            "verified": False,
        }
