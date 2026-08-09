from __future__ import annotations

import os
from typing import Any, Dict

from dotenv import load_dotenv

from gemini_client import GeminiClientError, analyze_lead_with_gemini
from ollama_client import OllamaClientError, analyze_lead_with_ollama

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").strip().lower()


class AIClientError(RuntimeError):
    """Raised when the configured AI provider fails."""


def analyze_lead_with_ai(
    form_data: Dict[str, Any],
) -> Dict[str, str]:
    """Analyze a lead using the configured AI provider."""

    if AI_PROVIDER == "ollama":
        try:
            return analyze_lead_with_ollama(form_data)
        except OllamaClientError as exc:
            raise AIClientError(str(exc)) from exc

    if AI_PROVIDER == "gemini":
        try:
            return analyze_lead_with_gemini(form_data)
        except GeminiClientError as exc:
            raise AIClientError(str(exc)) from exc

    raise AIClientError(
        f"Unsupported AI_PROVIDER: {AI_PROVIDER}. "
        "Use 'ollama' or 'gemini'."
    )