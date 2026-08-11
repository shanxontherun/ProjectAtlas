"""
Pinterest Boards data access layer.

Handles all database operations for pinterest_boards.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from services.database import get_connection


def create_board(
    account_id: int,
    board_name: str,
    category_slug: str,
) -> int:
    """
    Create a Pinterest board.
    """

    query = """
    INSERT INTO pinterest_boards (
        account_id,
        board_name,
        category_slug
    )
    VALUES (?, ?, ?)
    """

    with get_connection() as connection:

        cursor = connection.execute(
            query,
            (
                account_id,
                board_name,
                category_slug,
            ),
        )

        connection.commit()

        if cursor.lastrowid is None:
            raise sqlite3.Error("Failed to create Pinterest board.")

        return int(cursor.lastrowid)


def fetch_boards_by_account(
    account_id: int,
) -> list[dict[str, Any]]:
    """
    Return all active boards for an account.
    """

    query = """
    SELECT *
    FROM pinterest_boards
    WHERE account_id=?
      AND status='ACTIVE'
    ORDER BY board_name
    """

    with get_connection() as connection:

        rows = connection.execute(
            query,
            (account_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def fetch_active_boards() -> list[dict[str, Any]]:
    """
    Return every active board across all accounts.
    """

    query = """
    SELECT *
    FROM pinterest_boards
    WHERE status='ACTIVE'
    ORDER BY account_id, board_name
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]


def fetch_active_boards_with_accounts() -> list[dict[str, Any]]:
    """
    Return every active board joined with its account's display name.

    Boards expose both the Atlas ``board_id`` and, when available, the
    real Pinterest board ID (``pinterest_board_id``) so the mapping UI
    can reference boards by their Pinterest identity.
    """

    query = """
    SELECT
        pb.*,
        pa.account_name,
        pa.username,
        pa.is_seed
    FROM pinterest_boards pb
    JOIN pinterest_accounts pa
        ON pa.account_id = pb.account_id
    WHERE pb.status = 'ACTIVE'
    ORDER BY pa.account_name, pb.board_name
    """

    with get_connection() as connection:
        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]


def fetch_board(
    board_id: int,
) -> dict[str, Any] | None:
    """
    Fetch a board by ID.
    """

    query = """
    SELECT *
    FROM pinterest_boards
    WHERE board_id=?
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (board_id,),
        ).fetchone()

    return dict(row) if row else None


def sync_real_boards(
    account_id: int,
    boards: list[dict[str, Any]],
) -> int:
    """
    Synchronize real Pinterest boards for an account (upsert, no dupes).

    Each board is matched by its real Pinterest board ID. Existing boards
    are updated in place (name, privacy, status); new boards are inserted
    as ACTIVE real boards. Boards the account no longer has on Pinterest
    are marked INACTIVE (they stay in the database for the audit trail).

    Seed/test boards (``pinterest_board_id IS NULL``) are never touched,
    and no follower/pin counts are invented — the schema defaults of 0 are
    kept for real boards.

    Args:
        account_id: The real ``pinterest_accounts`` row to attach boards to.
        boards: Safe board records (``id``, ``name``, optional ``privacy``).

    Returns:
        The number of boards upserted (one per item in ``boards``).

    Raises:
        sqlite3.Error: If a board cannot be persisted.
    """

    count = 0

    connection = get_connection()
    try:
        connection.execute(
            "UPDATE pinterest_boards"
            " SET status = 'INACTIVE'"
            " WHERE account_id = ? AND pinterest_board_id IS NOT NULL",
            (account_id,),
        )

        for board in boards:
            board_id = str(board.get("id") or "").strip()
            board_name = str(board.get("name") or "").strip()
            privacy = board.get("privacy")

            if not board_id or not board_name:
                continue

            row = connection.execute(
                "SELECT board_id FROM pinterest_boards"
                " WHERE pinterest_board_id = ?",
                (board_id,),
            ).fetchone()

            if row is not None:
                connection.execute(
                    "UPDATE pinterest_boards"
                    " SET account_id = ?, board_name = ?, status = 'ACTIVE',"
                    " category_slug = 'uncategorized', privacy = ?"
                    " WHERE board_id = ?",
                    (account_id, board_name, privacy, int(row["board_id"])),
                )
            else:
                connection.execute(
                    "INSERT INTO pinterest_boards ("
                    " account_id, board_name, category_slug, status,"
                    " privacy, pinterest_board_id"
                    " ) VALUES (?, ?, 'uncategorized', 'ACTIVE', ?, ?)",
                    (account_id, board_name, privacy, board_id),
                )

            count += 1

        connection.commit()
    finally:
        connection.close()

    return count