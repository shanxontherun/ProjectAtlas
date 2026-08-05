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