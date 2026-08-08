"""Client helpers for AI guidance only: reason, next_action, and risks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict
from urllib import error, request


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


class OllamaClientError(RuntimeError):
    """Raised when Ollama cannot be reached or returns invalid data."""


@dataclass(frozen=True)
class LeadPayload:
    """Lead data sent to Ollama for narrative guidance."""

    score: int
    category: str
    company: str
    industry: str
    company_size: str
    budget: str
    timeline: str
    requirement: str


def _normalize_text(value: Any) -> str:
    return str(value).strip()


def _build_prompt(lead: LeadPayload) -> str:
    return (
        "You are an expert B2B sales qualification assistant. "
        "Analyze the lead information provided below.\n\n"

        "The lead score and category have already been calculated by our "
        "scoring system. DO NOT change, recalculate, or question the score "
        "or category.\n\n"

        "Return ONLY valid JSON using exactly this structure:\n"
        "{\"reason\":\"\",\"next_action\":\"\",\"risks\":\"\"}\n\n"

        "IMPORTANT RULES:\n"
        "1. Make every response specific to this lead.\n"
        "2. Do not give generic advice about lead scoring.\n"
        "3. Explain WHY the existing score and category make sense.\n"
        "4. Mention both positive buying signals and any factors limiting "
        "the lead from being classified higher.\n"
        "5. Do not invent information that is not provided.\n"
        "6. Do not assume that a budget is too low unless the provided "
        "information supports that conclusion.\n"
        "7. Risks must be based on actual missing information, uncertainty, "
        "or potential obstacles in the provided lead data.\n"
        "8. If there is no obvious major risk, say: "
        "\"No major risk identified; confirm requirements during discovery.\"\n"
        "9. Give ONE clear and practical next sales action.\n"
        "10. Do not mention that you are an AI.\n"
        "11. Do not use markdown or code fences.\n\n"

        f"Score: {lead.score}\n"
        f"Category: {lead.category}\n"
        f"Company: {lead.company or 'Not provided'}\n"
        f"Industry: {lead.industry or 'Not provided'}\n"
        f"Company Size: {lead.company_size or 'Not provided'}\n"
        f"Budget: {lead.budget or 'Not provided'}\n"
        f"Timeline: {lead.timeline or 'Not provided'}\n"
        f"Requirement: {lead.requirement or 'Not provided'}\n\n"

        "FIELD REQUIREMENTS:\n"
        "- reason: In 1-3 sentences, explain the strongest buying "
        "signals and the main reason the lead is in its current category.\n"
        "- next_action: Give one specific action the salesperson should "
        "take next, based on the lead's timeline and requirement.\n"
        "- risks: Identify the most important supported uncertainty or "
        "obstacle. Never invent a risk."
    )

def _extract_json_object(text: str) -> Dict[str, Any]:
    candidate = text.strip()

    if candidate.startswith("```"):
        candidate = candidate.replace("```json", "", 1).replace("```", "", 1).strip()

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as first_error:
        start_index = candidate.find("{")
        end_index = candidate.rfind("}")
        if start_index == -1 or end_index == -1 or end_index <= start_index:
            raise OllamaClientError("Ollama returned text that could not be parsed as JSON.") from first_error

        try:
            data = json.loads(candidate[start_index : end_index + 1])
        except json.JSONDecodeError as second_error:
            raise OllamaClientError("Ollama returned invalid JSON.") from second_error

    if not isinstance(data, dict):
        raise OllamaClientError("Ollama response must be a JSON object.")

    return data


def _validate_response(data: Dict[str, Any]) -> Dict[str, Any]:
    reason = str(data.get("reason", "")).strip()
    next_action = str(data.get("next_action", "")).strip()
    risks = str(data.get("risks", "")).strip()

    if not reason:
        raise OllamaClientError("The model returned an empty reason.")
    if not next_action:
        raise OllamaClientError("The model returned an empty next_action.")
    if not risks:
        raise OllamaClientError("The model returned an empty risks field.")

    return {
        "reason": reason,
        "next_action": next_action,
        "risks": risks,
    }


def analyze_lead_with_ollama(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send deterministic lead scores to Ollama and return AI guidance."""
    lead = LeadPayload(
        score=int(form_data.get("score", 0)),
        category=_normalize_text(form_data.get("category", "")),
        company=_normalize_text(form_data.get("company", "")),
        industry=_normalize_text(form_data.get("industry", "")),
        company_size=_normalize_text(form_data.get("company_size", "")),
        budget=_normalize_text(form_data.get("budget", "")),
        timeline=_normalize_text(form_data.get("timeline", "")),
        requirement=_normalize_text(form_data.get("requirement", "")),
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": _build_prompt(lead),
        "stream": False,
        "format": "json",
    }

    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            response_text = response.read().decode("utf-8")
    except error.URLError as exc:
        raise OllamaClientError(
            "Could not connect to Ollama at http://localhost:11434."
        ) from exc

    try:
        response_data = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise OllamaClientError("Ollama returned an unreadable response.") from exc

    model_text = str(response_data.get("response", ""))
    parsed = _extract_json_object(model_text)
    return _validate_response(parsed)