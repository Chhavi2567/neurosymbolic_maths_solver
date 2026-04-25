import google.generativeai as genai

from solver.gemini_model import DEFAULT_GEMINI_MODEL, generate_content_with_retry

EXPLAINER_SYSTEM = """Explain the provided solution steps clearly.
Use concise language and correct math notation.
Do not invent new calculations.
Base the explanation only on the given steps and final answer.
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
        fallback = "**Solution Steps:**\n\n"
        for i, step in enumerate(steps, 1):
            fallback += f"{i}. {step}\n"
        fallback += f"\n**Final Answer:** {result.get('result_str', 'N/A')}"
        fallback += f"\n\n*(Explanation unavailable: {str(e)})*"
        return fallback
