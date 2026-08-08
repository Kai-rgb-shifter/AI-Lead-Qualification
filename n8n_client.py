"""Webhook delivery for saved leads.

This module is responsible only for sending lead payloads to n8n.
It does not calculate scores, persist data, or render UI.
"""
from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict
from urllib import error, request

from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

import json
import logging
from typing import Any, Dict

import requests


logger = logging.getLogger(__name__)



def send_lead_to_n8n(lead_data: Dict[str, Any]) -> bool:
    """Send a lead payload to the configured n8n webhook.

    Returns True when the request succeeds and False when the webhook is
    unavailable or returns an unexpected response.
    """
    payload = {
        "name": str(lead_data.get("name", "")).strip(),
        "company": str(lead_data.get("company", "")).strip(),
        "industry": str(lead_data.get("industry", "")).strip(),
        "company_size": str(lead_data.get("company_size", "")).strip(),
        "budget": str(lead_data.get("budget", "")).strip(),
        "timeline": str(lead_data.get("timeline", "")).strip(),
        "requirement": str(lead_data.get("requirement", "")).strip(),
        "score": int(lead_data.get("score", 0)),
        "category": str(lead_data.get("category", "")).strip(),
        "reason": str(lead_data.get("reason", "")).strip(),
        "next_action": str(lead_data.get("next_action", "")).strip(),
        "risks": str(lead_data.get("risks", "")).strip(),
    }

    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as exc:
        logger.error("Failed to send lead to n8n webhook: %s", exc)

    return False