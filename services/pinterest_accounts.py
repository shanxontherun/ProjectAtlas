"""
Pinterest Accounts data access layer.

Handles all database operations for pinterest_accounts.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from services.database import get_connection


def create_pinterest_account(
    account_name: str,
    username: str,
    niche_slug: str,
    daily_limit: int = 15,
) -> int:
    """
    Create a Pinterest account.
    """

    query = """
    INSERT INTO pinterest_accounts (
        account_name,
        username,
        niche_slug,
        daily_limit
    )
    VALUES (?, ?, ?, ?)
    """

    with get_connection() as connection:

        cursor = connection.execute(
            query,
            (
                account_name,
                username,
                niche_slug,
                daily_limit,
            ),
        )

        connection.commit()

        if cursor.lastrowid is None:
            raise sqlite3.Error("Failed to create Pinterest account.")

        return int(cursor.lastrowid)


def fetch_active_accounts() -> list[dict[str, Any]]:
    """
    Return all active Pinterest accounts.
    """

    query = """
    SELECT *
    FROM pinterest_accounts
    WHERE status='ACTIVE'
    ORDER BY account_name
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]


def fetch_account(
    account_id: int,
) -> dict[str, Any] | None:
    """
    Fetch a Pinterest account by ID.
    """

    query = """
    SELECT *
    FROM pinterest_accounts
    WHERE account_id=?
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (account_id,),
        ).fetchone()

    return dict(row) if row else None