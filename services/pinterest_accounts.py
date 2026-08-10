"""
Pinterest Accounts data access layer.

Handles all database operations for pinterest_accounts.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from services.database import get_connection

# Default niche for real (OAuth-connected) Pinterest accounts. The niche
# slug is part of the legacy publishing model; a real account has no
# curated niche until a later sprint assigns one.
_REAL_ACCOUNT_NICHE_SLUG = "uncategorized"

_SEED_CONVERSION_ERROR = (
    "Refusing to convert a sample account into a real Pinterest account."
)


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


def upsert_real_pinterest_account(
    user: dict[str, Any],
) -> int:
    """
    Create or update a real (non-seed) Pinterest account from OAuth data.

    Reconnection reuses the existing account by the real Pinterest user ID
    (falling back to the unique username) so repeated connects never
    create duplicate accounts. The account is always ``is_seed = 0`` and
    ACTIVE.

    Seed/dev accounts are never converted into real accounts: if a match
    resolves to a seed account, this raises ``sqlite3.Error`` instead of
    mutating it.

    Args:
        user: safe Pinterest user identity (``id``, ``username``).

    Returns:
        The ``account_id`` of the created/updated real account.

    Raises:
        sqlite3.Error: If the account cannot be created/updated, or a seed
            account would be converted.
    """

    user_id = str(user.get("id") or "").strip()
    username = str(user.get("username") or "").strip()
    account_name = str(user.get("display_name") or username or "").strip()

    if not user_id or not username:
        raise sqlite3.Error("Pinterest returned an incomplete account.")

    connection = get_connection()
    try:
        row = None

        if user_id:
            row = connection.execute(
                "SELECT account_id, is_seed FROM pinterest_accounts"
                " WHERE pinterest_user_id = ?",
                (user_id,),
            ).fetchone()

        if row is None:
            row = connection.execute(
                "SELECT account_id, is_seed FROM pinterest_accounts"
                " WHERE username = ?",
                (username,),
            ).fetchone()

        if row is not None and int(row["is_seed"]) == 1:
            raise sqlite3.Error(_SEED_CONVERSION_ERROR)

        if row is not None:
            account_id = int(row["account_id"])
            connection.execute(
                "UPDATE pinterest_accounts"
                " SET account_name = ?, username = ?, pinterest_user_id = ?,"
                " status = 'ACTIVE'"
                " WHERE account_id = ?",
                (account_name, username, user_id, account_id),
            )
        else:
            cursor = connection.execute(
                "INSERT INTO pinterest_accounts ("
                " account_name, username, niche_slug, daily_limit,"
                " status, is_seed, pinterest_user_id"
                " ) VALUES (?, ?, ?, 15, 'ACTIVE', 0, ?)",
                (
                    account_name,
                    username,
                    _REAL_ACCOUNT_NICHE_SLUG,
                    user_id,
                ),
            )
            account_id = int(cursor.lastrowid)

        connection.commit()
    finally:
        connection.close()

    return account_id