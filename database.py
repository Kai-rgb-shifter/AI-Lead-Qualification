"""SQLite persistence for analyzed leads.

This module is responsible only for database creation, inserts, and lead retrieval.
It does not calculate scores or generate AI guidance.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


DATABASE_PATH = Path(__file__).with_name("leads.db")


def initialize_database() -> None:
    """Create the leads database and table if they do not already exist."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                name TEXT,
                company TEXT,
                industry TEXT,
                company_size TEXT,
                budget TEXT,
                timeline TEXT,
                requirement TEXT,
                score INTEGER,
                category TEXT,
                reason TEXT,
                next_action TEXT,
                risks TEXT
            )
            """
        )
        connection.commit()


def save_lead(lead_data: Dict[str, Any]) -> None:
    """Persist a single analyzed lead record."""
    initialize_database()

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
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

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO leads (
                created_at, name, company, industry, company_size,
                budget, timeline, requirement, score, category,
                reason, next_action, risks
            ) VALUES (
                :created_at, :name, :company, :industry, :company_size,
                :budget, :timeline, :requirement, :score, :category,
                :reason, :next_action, :risks
            )
            """,
            payload,
        )
        connection.commit()


def get_all_leads() -> List[Dict[str, Any]]:
    """Return all stored leads ordered by most recent first."""
    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM leads ORDER BY datetime(created_at) DESC, id DESC"
        ).fetchall()

    return [dict(row) for row in rows]


def get_hot_leads() -> List[Dict[str, Any]]:
    """Return only leads categorized as Hot."""
    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM leads WHERE category = ? ORDER BY datetime(created_at) DESC, id DESC",
            ("Hot",),
        ).fetchall()

    return [dict(row) for row in rows]