from __future__ import annotations

import sqlite3

from database import DATABASE_PATH, save_lead, get_all_leads


def main() -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                created_at,
                name,
                company,
                industry,
                company_size,
                budget,
                timeline,
                requirement,
                score,
                category,
                reason,
                next_action,
                risks
            FROM leads
            ORDER BY id ASC
            """
        ).fetchall()

    print(f"Found {len(rows)} local SQLite leads.")

    for row in rows:
        save_lead(dict(row))

    print(f"Migrated {len(rows)} leads to Supabase.")

    supabase_leads = get_all_leads()
    print(f"Supabase now contains {len(supabase_leads)} leads.")


if __name__ == "__main__":
    main()
