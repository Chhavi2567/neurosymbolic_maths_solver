import google.generativeai as genai

from solver.gemini_model import DEFAULT_GEMINI_MODEL, generate_content_with_retry

EXPLAINER_SYSTEM = """You are a brilliant and patient math tutor.
You are given:
1. A student's original math problem
2. The exact steps computed by a symbolic math engine (SymPy/Z3)
3. The final verified answer

Your job: explain the solution clearly for a student.
- Use simple, encouraging language
- Walk through each step and explain WHY it works mathematically
- Reference the actual step values provided — do not invent new calculations
- Use proper math notation where helpful (you can use LaTeX between $ signs)
- Keep explanations educational, not just mechanical
- End with a brief summary of the key concept demonstrated
- Do NOT say 'as the symbolic engine computed' — speak directly to the student
"""


def narrate(user_query: str, parsed: dict, result: dict, verification: dict, api_key: str) -> str:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=DEFAULT_GEMINI_MODEL,
            system_instruction=EXPLAINER_SYSTEM,
        )

        steps_text = "\n".join([f"  Step {i+1}: {s}" for i, s in enumerate(result.get("steps", []))])
        op = parsed.get("operation", "solve")
        ptype = parsed.get("problem_type", "algebra")

        prompt = f"""Student's question: "{user_query}"

Problem type: {ptype}
Operation: {op}

Exact steps from the symbolic engine:
{steps_text}

Final answer: {result.get("result_str", "See graph/proof")}
Verification: {verification.get("method", "")} — {verification.get("detail", "")}

Please explain this solution clearly and educationally to the student."""

        response = generate_content_with_retry(model, prompt)
        return response.text.strip()

    except Exception as e:
        steps = result.get("steps", [])
        fallback = f"**Solution Steps:**\n\n"
        for i, step in enumerate(steps, 1):
            fallback += f"{i}. {step}\n"
        fallback += f"\n**Final Answer:** {result.get('result_str', 'N/A')}"
        fallback += f"\n\n*(Gemini explanation unavailable: {str(e)})*"
        return fallback
