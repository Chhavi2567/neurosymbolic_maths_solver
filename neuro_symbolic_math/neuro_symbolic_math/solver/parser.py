"""
parser.py  —  Neural layer
Uses Google Gemini (free tier) to parse any math problem
into a structured dict that the symbolic engines can consume.
No math is computed here — only intent extraction.
"""

import json
import re

import google.generativeai as genai

from solver.gemini_model import DEFAULT_GEMINI_MODEL, generate_content_with_retry


SYSTEM_INSTRUCTION = """You are a precise mathematical problem analyzer.
Your ONLY job is to read a math problem and return a JSON object describing it.
You do NOT solve the problem. You only classify and extract structure.

Return ONLY a raw JSON object — no markdown, no backticks, no explanation.

In JSON string values, backslashes must be escaped: use two backslashes before every LaTeX command (e.g. \\\\frac and \\\\sin in the JSON text so the value contains valid LaTeX).

JSON schema:
{
  "problem_type": one of ["algebra", "calculus", "linear_algebra", "proof", "graphing", "numerical", "statistics", "trigonometry", "number_theory"],
  "operation": one of ["solve", "differentiate", "integrate", "limit", "plot", "simplify", "factor", "expand", "prove", "eigenvalue", "determinant", "matrix_multiply", "numerical_solve", "series", "sum"],
  "latex_expression": "the core mathematical expression in LaTeX notation",
  "variables": ["list of variable names as strings, e.g. x, y, n"],
  "domain": "expression domain hint e.g. real, complex, integer — or null",
  "limit_point": "for limits: the point approached e.g. 'oo' for infinity, '0', 'pi' — or null",
  "limit_variable": "for limits: which variable approaches the point — or null",
  "is_proof": true or false,
  "plot_range": {"xmin": number, "xmax": number} or null,
  "extra_context": "any additional info needed to solve — or null"
}

Examples:

Input: "integrate x^2 * sin(x) dx"
Output: {"problem_type":"calculus","operation":"integrate","latex_expression":"x^2 \\sin(x)","variables":["x"],"domain":"real","limit_point":null,"limit_variable":null,"is_proof":false,"plot_range":null,"extra_context":null}

Input: "plot sin(x)/x from -4pi to 4pi"
Output: {"problem_type":"graphing","operation":"plot","latex_expression":"\\frac{\\sin(x)}{x}","variables":["x"],"domain":"real","limit_point":null,"limit_variable":null,"is_proof":false,"plot_range":{"xmin":-12.566,"xmax":12.566},"extra_context":null}

Input: "find limit of (1+1/n)^n as n approaches infinity"
Output: {"problem_type":"calculus","operation":"limit","latex_expression":"\\left(1+\\frac{1}{n}\\right)^n","variables":["n"],"domain":"real","limit_point":"oo","limit_variable":"n","is_proof":false,"plot_range":null,"extra_context":null}

Input: "prove that (a+b)^2 = a^2 + 2ab + b^2"
Output: {"problem_type":"proof","operation":"prove","latex_expression":"(a+b)^2 = a^2 + 2ab + b^2","variables":["a","b"],"domain":"real","limit_point":null,"limit_variable":null,"is_proof":true,"plot_range":null,"extra_context":null}
"""


def _repair_latex_json_escapes(text: str) -> str:
    """
    Gemini often emits LaTeX like \\sin(x) with a single backslash before a letter.
    In JSON, \\sin is invalid (only \\\", \\\\, \\/, \\b, \\f, \\n, \\r, \\t, \\uXXXX are valid).
    Double any \\ that starts a LaTeX command letter but is not already doubled.
    """
    # Not preceded by \\ — then \\ + letter → \\\\ + letter (two chars backslash in JSON → one in string)
    return re.sub(r"(?<!\\)\\([a-zA-Z])", r"\\\\\1", text)


def _parse_response_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        repaired = _repair_latex_json_escapes(raw)
        return json.loads(repaired)


def parse_problem(user_query: str, api_key: str) -> dict:
    """
    Send user query to Gemini and get structured JSON back.
    Returns a dict with problem metadata — never a solution.
    """
    raw = ""
    try:
        genai.configure(api_key=api_key)
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.2,
        )
        model = genai.GenerativeModel(
            model_name=DEFAULT_GEMINI_MODEL,
            system_instruction=SYSTEM_INSTRUCTION,
            generation_config=generation_config,
        )

        response = generate_content_with_retry(model, user_query)
        raw = response.text.strip()
        parsed = _parse_response_json(raw)

        # Ensure required keys exist with safe defaults
        parsed.setdefault("problem_type", "algebra")
        parsed.setdefault("operation", "solve")
        parsed.setdefault("latex_expression", user_query)
        parsed.setdefault("variables", ["x"])
        parsed.setdefault("domain", "real")
        parsed.setdefault("limit_point", None)
        parsed.setdefault("limit_variable", None)
        parsed.setdefault("is_proof", False)
        parsed.setdefault("plot_range", None)
        parsed.setdefault("extra_context", None)

        return {"success": True, "data": parsed}

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Gemini returned non-JSON output: {str(e)}",
            "raw": raw if "raw" in dir() else "",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
