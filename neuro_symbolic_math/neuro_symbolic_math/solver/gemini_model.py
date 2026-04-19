"""Shared Gemini model id and helpers for google-generativeai.

Older ids like ``gemini-1.5-flash`` may 404. ``gemini-2.0-flash`` free-tier quotas
can be exhausted separately from newer models — override with env ``GEMINI_MODEL``.
"""

import os
import re
import time

# Default: 2.5 Flash (distinct free-tier pool from 2.0 Flash in many projects).
DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def generate_content_with_retry(model, content, *, max_attempts: int = 4):
    """
    Call ``model.generate_content``; on 429 / quota burst, wait and retry a few times.
    Does not fix same-day quota exhaustion — switch GEMINI_MODEL or wait / upgrade billing.
    """
    for attempt in range(max_attempts):
        try:
            return model.generate_content(content)
        except Exception as e:
            err = str(e)
            recoverable = (
                "429" in err
                or type(e).__name__ == "ResourceExhausted"
                or "quota" in err.lower()
                or "rate" in err.lower()
            )
            if not recoverable or attempt == max_attempts - 1:
                raise
            m = re.search(r"retry in ([\d.]+)\s*s", err, re.I)
            wait = float(m.group(1)) + 2.0 if m else 35.0
            time.sleep(min(max(wait, 1.0), 120.0))
