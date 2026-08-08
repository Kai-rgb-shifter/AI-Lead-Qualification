"""Deterministic rule-based lead scoring logic for the AI Lead Qualification System."""

from __future__ import annotations

import re
from typing import Any, Dict, List


_POSITIVE_REQUIREMENT_PATTERNS = (
    r"\bAI\b",
    r"automation",
    r"CRM",
    r"chatbot",
    r"workflow",
    r"integration",
)

_EARLY_REQUIREMENT_PATTERNS = (
    r"exploring",
    r"planning",
    r"considering",
)


def _parse_budget(value: Any) -> float:
    """Convert a budget string into a numeric value when possible."""
    text = str(value).strip()
    if not text:
        return 0.0

    cleaned = re.sub(r"[^0-9.]", "", text.replace(",", ""))
    if not cleaned:
        return 0.0

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _classify(score: int) -> str:
    if score >= 80:
        return "Hot"
    if score >= 50:
        return "Warm"
    return "Cold"


def _score_budget(budget_value: float) -> int:
    if budget_value > 1_000_000:
        return 30
    if 200_000 <= budget_value <= 1_000_000:
        return 20
    return 10


def _score_timeline(timeline: str) -> int:
    normalized = timeline.strip().lower()
    if not normalized:
        return 10

    if "1 month" in normalized or "within 1 month" in normalized or normalized == "asap":
        return 30
    if "3 month" in normalized or "within 3 months" in normalized or "1-3 months" in normalized:
        return 20
    return 10


def _score_requirement(requirement: str) -> int:
    normalized = requirement.strip()
    if not normalized:
        return 5

    for pattern in _POSITIVE_REQUIREMENT_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return 30

    for pattern in _EARLY_REQUIREMENT_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return 15

    return 5


def analyze_lead(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a lead using deterministic business rules."""
    budget_value = _parse_budget(form_data.get("budget", ""))
    timeline = str(form_data.get("timeline", ""))
    requirement = str(form_data.get("requirement", ""))
    company = str(form_data.get("company", "")).strip()

    budget_score = _score_budget(budget_value)
    timeline_score = _score_timeline(timeline)
    requirement_score = _score_requirement(requirement)
    company_score = 10 if company else 0

    score = budget_score + timeline_score + requirement_score + company_score
    category = _classify(score)

    reasons: List[str] = []
    reasons.append(f"Budget contribution: {budget_score}")
    reasons.append(f"Timeline contribution: {timeline_score}")
    reasons.append(f"Requirement contribution: {requirement_score}")
    reasons.append(f"Company contribution: {company_score}")

    return {
        "score": score,
        "category": category,
        "reason": " ".join(reasons),
        "next_action": (
            "Reach out immediately" if category == "Hot"
            else "Follow up and qualify further" if category == "Warm"
            else "Nurture and revisit later"
        ),
    }