from __future__ import annotations

import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class GeminiClientError(RuntimeError):
    """Raised when Gemini cannot be reached or returns invalid data."""


def _build_prompt(lead: Dict[str, Any]) -> str:
    return (
        "You are an expert B2B sales qualification assistant. "
        "Analyze the lead information provided below.\n\n"

        "The lead score and category have already been calculated by our "
        "scoring system. DO NOT change, recalculate, or question the score "
        "or category.\n\n"

        "Return ONLY valid JSON using exactly this structure:\n"
        '{"reason":"","next_action":"","risks":""}\n\n'

        "IMPORTANT RULES:\n"
        "1. Make every response specific to this lead.\n"
        "2. Do not give generic advice about lead scoring.\n"
        "3. Explain WHY the existing score and category make sense.\n"
        "4. Mention positive buying signals and relevant limitations.\n"
        "5. Do not invent information that is not provided.\n"
        "6. Risks must be based on actual missing information, uncertainty, "
        "or potential obstacles in the provided lead data.\n"
        "7. If there is no obvious major risk, say: "
        '"No major risk identified; confirm requirements during discovery."\n'
        "8. Give ONE clear and practical next sales action.\n"
        "9. Do not mention that you are an AI.\n"
        "10. Do not use markdown or code fences.\n\n"

        f"Score: {lead.get('score', 0)}\n"
        f"Category: {lead.get('category', '')}\n"
        f"Company: {lead.get('company', '') or 'Not provided'}\n"
        f"Industry: {lead.get('industry', '') or 'Not provided'}\n"
        f"Company Size: {lead.get('company_size', '') or 'Not provided'}\n"
        f"Budget: {lead.get('budget', '') or 'Not provided'}\n"
        f"Timeline: {lead.get('timeline', '') or 'Not provided'}\n"
        f"Requirement: {lead.get('requirement', '') or 'Not provided'}\n\n"

        "FIELD REQUIREMENTS:\n"
        "- reason: In 1-3 sentences, explain the strongest buying "
        "signals and why the lead is in its current category.\n"
        "- next_action: Give one specific action the salesperson should "
        "take next.\n"
        "- risks: Identify the most important supported uncertainty or "
        "obstacle. Never invent a risk."
    )


def analyze_lead_with_gemini(
    form_data: Dict[str, Any],
) -> Dict[str, str]:
    """Send deterministic lead scores to Gemini and return AI guidance."""

    if not GEMINI_API_KEY:
        raise GeminiClientError(
            "GEMINI_API_KEY is not configured."
        )

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=_build_prompt(form_data),
            config={
                "response_mime_type": "application/json",
            },
        )

    except Exception as exc:
        raise GeminiClientError(
            "Could not connect to Gemini."
        ) from exc

    try:
        candidate = response.text.strip()

        if candidate.startswith("```"):
            candidate = candidate.replace("```json", "", 1)
            candidate = candidate.replace("```", "", 1).strip()

        start_index = candidate.find("{")
        end_index = candidate.rfind("}")

        if start_index == -1 or end_index == -1:
            raise GeminiClientError(
                "Gemini response did not contain a JSON object."
            )

        data = json.loads(
            candidate[start_index:end_index + 1]
        )

    except (json.JSONDecodeError, TypeError) as exc:
        raise GeminiClientError(
            "Gemini returned invalid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise GeminiClientError(
            "Gemini response must be a JSON object."
        )

    reason = str(data.get("reason", "")).strip()
    next_action = str(data.get("next_action", "")).strip()
    risks = str(data.get("risks", "")).strip()

    if not reason:
        raise GeminiClientError("Gemini returned an empty reason.")

    if not next_action:
        raise GeminiClientError(
            "Gemini returned an empty next_action."
        )

    if not risks:
        raise GeminiClientError("Gemini returned an empty risks field.")

    return {
        "reason": reason,
        "next_action": next_action,
        "risks": risks,
    }