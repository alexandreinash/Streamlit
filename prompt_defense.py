"""
Input validation and light prompt-injection guards for user-facing chat.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Tuple

# Keep prompts bounded (DoS / token stuffing)
MAX_USER_MESSAGE_CHARS = 2_000

# Common jailbreak / instruction-override patterns (case-insensitive)
_BLOCKED_SUBSTRINGS = (
    "ignore previous",
    "ignore all previous",
    "disregard previous",
    "forget previous",
    "you are now",
    "new instructions:",
    "system prompt",
    "reveal your prompt",
    "show your instructions",
    "api key",
    "openai_api",
    "sk-",
    "execute code",
    "run this code",
    "sudo ",
    "<script",
    "javascript:",
)

_REFUSAL = (
    "I can only help with movie picks and questions about your film library. "
    "Please rephrase as a normal movie question (no special instructions or system requests)."
)


def normalize_user_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\x00", "").strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def validate_chat_input(text: str) -> Tuple[str | None, str | None]:
    """
    Returns (sanitized_message, None) if OK, or (None, refusal_message) if blocked.
    """
    if not text or not text.strip():
        return None, "Please enter a question about movies."

    raw = normalize_user_text(text)
    if not raw:
        return None, "Please enter a question about movies."

    if len(raw) > MAX_USER_MESSAGE_CHARS:
        return None, f"Message too long (max {MAX_USER_MESSAGE_CHARS} characters). Shorten your question."

    lower = raw.lower()
    for bad in _BLOCKED_SUBSTRINGS:
        if bad in lower:
            return None, _REFUSAL

    # Repeated override attempts (e.g. many "ignore")
    if lower.count("ignore") > 2 or lower.count("instruction") > 4:
        return None, _REFUSAL

    return raw, None
