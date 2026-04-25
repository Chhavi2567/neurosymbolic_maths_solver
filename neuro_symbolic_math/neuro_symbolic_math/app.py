import os
from pathlib import Path

_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.is_file():
    try:
        from dotenv import load_dotenv

        load_dotenv(_env_path, override=True)
    except ImportError:
        pass

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import base64
import html
import gradio as gr
from solver.parser import parse_problem
from solver.router import route
from solver.verifier import verify
from solver.explainer import narrate


def _resolve_gemini_api_key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()


def _explanation_panel_html(text: str, *, is_error: bool = False) -> str:
    if is_error:
        safe = html.escape(text)
        return (
            "<div class='explanation-panel' style='padding:12px 16px;border-radius:12px;"
            "background:var(--error-light);border:1px solid #f0c4c4;color:#6b1d1d;font-size:14px;'>"
            f"{safe}</div>"
        )
    body = html.escape(text).replace("\n", "<br>\n")
    return (
        "<div class='explanation-panel' style='padding:12px 16px;border-radius:12px;"
        "background:white;border:1px solid var(--border);color:var(--text-primary);"
        "font-size:15px;line-height:1.65;'>"
        f"{body}</div>"
    )


EXAMPLES = [
    ["Solve x^3 - 6x^2 + 11x - 6 = 0"],
    ["Integrate x^2 * sin(x) dx"],
    ["Differentiate x^3 * ln(x) with respect to x"],
    ["Find the limit of sin(x)/x as x approaches 0"],
    ["Find the limit of (1 + 1/n)^n as n approaches infinity"],
    ["Factor x^4 - 16"],
    ["Simplify (sin^2(x) + cos^2(x)) / cos(x)"],
    ["Plot sin(x) + cos(2x) from -2pi to 2pi"],
    ["Plot x^3 - 3x from -3 to 3"],
    ["Prove that (a+b)^2 = a^2 + 2ab + b^2"],
    ["Prove sin^2(x) + cos^2(x) = 1"],
    ["Expand (x + y)^5"],
    ["Find the Taylor series of e^x"],
    ["Solve x^2 + 5x + 6 = 0"],
    ["Integrate e^x * cos(x) dx"],
]

CUSTOM_CSS = """
:root {
    --primary: #534AB7;
    --primary-light: #EEEDFE;
    --success: #1D9E75;
    --success-light: #E1F5EE;
    --warning: #BA7517;
    --warning-light: #FAEEDA;
    --error: #A32D2D;
    --error-light: #FCEBEB;
    --text-primary: #1a1a2e;
    --text-secondary: #555;
    --border: #e0dff7;
    --bg: #f8f7ff;
}

body { background: var(--bg) !important; }

.gradio-container {
    max-width: 1100px !important;
    margin: 0 auto !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}

.header-box {
    background: linear-gradient(135deg, #534AB7 0%, #3B8BD4 100%);
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 24px;
    color: white;
}

.header-box h1 { color: white !important; margin: 0 0 8px 0; font-size: 28px; font-weight: 700; }
.header-box p  { color: rgba(255,255,255,0.85) !important; margin: 0; font-size: 15px; }

.section-heading {
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    background: linear-gradient(135deg, #534AB7 0%, #3B8BD4 100%) !important;
    margin: 1.5rem 0 0.75rem 0 !important;
    padding: 12px 18px !important;
    border-radius: 10px !important;
    border-bottom: none !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 2px 8px rgba(83, 74, 183, 0.25) !important;
}

.pipeline-box {
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.8;
}

.result-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
}

.verified-badge {
    display: inline-block;
    background: var(--success-light);
    color: var(--success);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 600;
}

.error-badge {
    display: inline-block;
    background: var(--error-light);
    color: var(--error);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 13px;
}

button.primary-btn {
    background: var(--primary) !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    padding: 14px 32px !important;
    border: none !important;
    transition: all 0.2s !important;
}

button.primary-btn:hover { background: #3d35a8 !important; transform: translateY(-1px); }

.status-step {
    background: var(--primary-light);
    border-left: 3px solid var(--primary);
    border-radius: 0 8px 8px 0;
    padding: 8px 14px;
    margin: 6px 0;
    font-size: 13px;
    color: var(--text-primary);
}

.tab-nav button { font-weight: 500 !important; }
"""

def make_status_html(step: int, parsed: dict = None, verif: dict = None) -> str:
    steps_info = [
        ("1", "Parser", "Read and structure the problem"),
        ("2", "Engine", "Compute the result"),
        ("3", "Verifier", "Cross-check the output"),
        ("4", "Explanation", "Generate a clear walkthrough"),
        ("5", "Complete", "Result ready"),
    ]

    html = "<div style='font-size:13px;'>"
    for i, (icon, name, desc) in enumerate(steps_info):
        if i < step:
            color = "#1D9E75"; bg = "#E1F5EE"; status = "✓"
        elif i == step:
            color = "#534AB7"; bg = "#EEEDFE"; status = "⟳"
        else:
            color = "#aaa"; bg = "#f5f5f5"; status = "○"

        html += f"""
        <div style='display:flex;align-items:center;gap:10px;margin:8px 0;
                    background:{bg};border-radius:8px;padding:8px 14px;
                    border-left:3px solid {color};'>
            <span style='font-size:18px;'>{icon}</span>
            <div>
                <div style='font-weight:600;color:{color};'>{status} {name}</div>
                <div style='color:#666;font-size:12px;'>{desc}</div>
            </div>
        </div>"""

    if parsed and step >= 1:
        pt = parsed.get("problem_type", "?").title()
        op = parsed.get("operation", "?").title()
        html += f"""<div style='margin-top:12px;padding:10px 14px;background:#f0eeff;
                                border-radius:8px;font-size:12px;color:#534AB7;'>
            <b>Detected:</b> {pt} problem · Operation: {op}
            </div>"""

    if verif and step >= 3:
        ok = verif.get("verified", False)
        badge_bg  = "#E1F5EE" if ok else "#FCEBEB"
        badge_col = "#1D9E75" if ok else "#A32D2D"
        label     = "✓ Verified" if ok else "⚠ Unverified"
        html += f"""<div style='margin-top:8px;padding:10px 14px;background:{badge_bg};
                                border-radius:8px;font-size:12px;color:{badge_col};'>
            <b>{label}</b> — {verif.get('method','')}<br>
            <span style='opacity:0.8;'>{verif.get('detail','')}</span>
            </div>"""

    html += "</div>"
    return html


def make_analysis_html(parsed: dict) -> str:
    if not parsed:
        return ""
    fields = [
        ("Problem type",  parsed.get("problem_type", "—").replace("_", " ").title()),
        ("Operation",     parsed.get("operation", "—").replace("_", " ").title()),
        ("Variables",     ", ".join(parsed.get("variables", ["x"]))),
        ("Domain",        parsed.get("domain") or "real"),
        ("Is proof",      "Yes" if parsed.get("is_proof") else "No"),
        ("Limit point",   parsed.get("limit_point") or "—"),
        ("Extra context", parsed.get("extra_context") or "—"),
    ]
    rows = "".join(
        f"<tr><td style='padding:6px 12px;color:#888;font-size:13px;white-space:nowrap;'>{k}</td>"
        f"<td style='padding:6px 12px;font-size:13px;font-weight:500;color:#222;'>{v}</td></tr>"
        for k, v in fields
    )
    return f"""
    <div style='background:white;border:1px solid #e0dff7;border-radius:12px;overflow:hidden;'>
        <div style='background:#534AB7;color:white;padding:10px 16px;font-weight:600;font-size:14px;'>
            🔬 Problem Analysis
        </div>
        <table style='width:100%;border-collapse:collapse;'>{rows}</table>
    </div>"""


def make_latex_html(result_latex: str, engine: str, verified: bool) -> str:
    badge_bg  = "#E1F5EE" if verified else "#FFF3CD"
    badge_col = "#1D9E75" if verified else "#856404"
    badge_txt = "Exact symbolic result" if verified else "Approximate result"
    return f"""
    <div style='background:white;border:1px solid #e0dff7;border-radius:12px;overflow:hidden;margin-top:12px;'>
        <div style='background:#534AB7;color:white;padding:10px 16px;font-weight:600;font-size:14px;'>
            🎯 Result
        </div>
        <div style='padding:20px 24px;'>
            <div style='font-size:22px;font-family:monospace;color:#222;background:#f8f7ff;
                        padding:16px;border-radius:8px;word-break:break-all;margin-bottom:12px;'>
                {result_latex}
            </div>
            <div style='font-size:12px;color:#888;'>
                Engine: <b style='color:#534AB7;'>{engine}</b>
                &nbsp;·&nbsp;
                <span style='background:{badge_bg};color:{badge_col};padding:2px 10px;
                             border-radius:12px;font-weight:600;'>{badge_txt}</span>
            </div>
        </div>
    </div>"""


def make_steps_html(steps: list) -> str:
    if not steps:
        return ""
    items = "".join(
        f"""<div style='display:flex;gap:12px;align-items:flex-start;margin:8px 0;'>
                <div style='min-width:26px;height:26px;background:#534AB7;color:white;
                            border-radius:50%;display:flex;align-items:center;justify-content:center;
                            font-size:12px;font-weight:700;flex-shrink:0;'>{i}</div>
                <div style='font-size:14px;color:#333;padding-top:3px;font-family:monospace;
                            background:#f8f7ff;padding:8px 12px;border-radius:8px;width:100%;'>{s}</div>
            </div>"""
        for i, s in enumerate(steps, 1)
    )
    return f"""
    <div style='background:white;border:1px solid #e0dff7;border-radius:12px;overflow:hidden;margin-top:12px;'>
        <div style='background:#1D9E75;color:white;padding:10px 16px;font-weight:600;font-size:14px;'>
            📐 Engine Steps (Symbolic)
        </div>
        <div style='padding:16px 20px;'>{items}</div>
    </div>"""


def solve_problem(query: str):
    if not query.strip():
        return (
            make_status_html(0),
            "",
            "",
            None,
            _explanation_panel_html("❌ Please enter a math problem.", is_error=True),
        )

    api_key = _resolve_gemini_api_key()
    if not api_key:
        return (
            make_status_html(0),
            "",
            "",
            None,
            _explanation_panel_html(
                "❌ Add GEMINI_API_KEY to a .env file in the app folder (see .env.example), "
                "or export GEMINI_API_KEY, then restart.",
                is_error=True,
            ),
        )

    parse_result = parse_problem(query, api_key)

    if not parse_result.get("success"):
        err = parse_result.get("error", "Unknown error")
        return (
            make_status_html(0),
            "",
            "",
            None,
            _explanation_panel_html(f"❌ Parsing failed: {err}", is_error=True),
        )

    parsed = parse_result["data"]
    analysis_html = make_analysis_html(parsed)

    result = route(parsed)

    if not result.get("success"):
        err = result.get("error", "Unknown error")
        return (
            make_status_html(1, parsed=parsed),
            analysis_html,
            "",
            None,
            _explanation_panel_html(f"❌ Symbolic engine error: {err}", is_error=True),
        )

    graph_img = None
    if "image_base64" in result:
        img_bytes = base64.b64decode(result["image_base64"])
        import tempfile

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(img_bytes)
        tmp.close()
        graph_img = tmp.name

    steps_html = make_steps_html(result.get("steps", []))
    result_html = make_latex_html(
        result.get("result_latex", result.get("result_str", "See graph")),
        result.get("engine", "SymPy"),
        result.get("verified", True),
    )
    combined_result_html = result_html + steps_html

    verif = verify(parsed, result)
    explanation = narrate(query, parsed, result, verif, api_key)

    return (
        make_status_html(4, parsed=parsed, verif=verif),
        analysis_html,
        combined_result_html,
        graph_img,
        _explanation_panel_html(explanation, is_error=False),
    )


def build_ui():
    with gr.Blocks(title="NeuroSymbolic Math Solver", analytics_enabled=False) as demo:

        gr.HTML("""
        <div class='header-box'>
            <h1>Math Solver</h1>
            <p>Structured parsing, symbolic computation, and verification.</p>
        </div>
        """)

        gr.HTML("""
        <div class='pipeline-box'>
            <b>How it works:</b> &nbsp;
            Parse problem &nbsp;→&nbsp;
            Compute result &nbsp;→&nbsp;
            Verify output &nbsp;→&nbsp;
            Explain steps
        </div>
        """)

        with gr.Row():
            with gr.Column(scale=2):
                query_input = gr.Textbox(
                    label="Your Math Problem",
                    placeholder=(
                        "Type any math problem, e.g.:\n"
                        "• Integrate x² sin(x) dx\n"
                        "• Prove (a+b)² = a² + 2ab + b²\n"
                        "• Plot sin(x)/x from -4π to 4π\n"
                        "• Find limit of (1+1/n)^n as n→∞"
                    ),
                    lines=4,
                )

                solve_btn = gr.Button("Solve", variant="primary", size="lg")

                gr.HTML("<p style='font-size:13px;color:#888;margin:8px 0 4px;'>Quick examples:</p>")

                gr.Examples(
                    examples=EXAMPLES,
                    inputs=[query_input],
                    label=None,
                    cache_examples=False,
                )

            with gr.Column(scale=1):
                status_display = gr.HTML(make_status_html(-1), label="Pipeline Status")

        gr.HTML("<div class='section-heading'>Answer &amp; Steps</div>")

        with gr.Row():
            with gr.Column(scale=1):
                analysis_display = gr.HTML(label="Problem Analysis")
            with gr.Column(scale=2):
                result_display = gr.HTML(label="Result")

        graph_display = gr.Image(
            label="Graph",
            visible=True,
            show_label=True,
            height=420,
        )

        gr.HTML("<div class='section-heading'>Explanation</div>")
        explanation_display = gr.HTML(
            value=_explanation_panel_html(
                "Run the solver to see a step-by-step explanation here.",
                is_error=False,
            ),
            label="Step-by-step explanation",
            container=True,
            js_on_load=None,
        )

        _outputs = [
            status_display,
            analysis_display,
            result_display,
            graph_display,
            explanation_display,
        ]

        solve_btn.click(fn=solve_problem, inputs=[query_input], outputs=_outputs)

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        share=True,
        server_name="0.0.0.0",
        server_port=7860,
        footer_links=["gradio", "settings"],
        inbrowser=True,
        theme=gr.themes.Soft(),
        css=CUSTOM_CSS,
    )
