"""
Category Routes data access layer.

Handles all database operations for the category_routes table.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from services.database import get_connection


def create_route(
    category_slug: str,
    account_id: int,
    board_id: int,
    priority: int = 1,
) -> int:
    """
    Create a category route.

    Raises:
        ValueError:
            If the same route already exists.
    """

    query = """
    INSERT INTO category_routes (
        category_slug,
        account_id,
        board_id,
        priority
    )
    VALUES (?, ?, ?, ?)
    """

    with get_connection() as connection:

        try:

            cursor = connection.execute(
                query,
                (
                    category_slug,
                    account_id,
                    board_id,
                    priority,
                ),
            )

            connection.commit()

            if cursor.lastrowid is None:
                raise sqlite3.Error(
                    "Failed to create route."
                )

            return int(cursor.lastrowid)

        except sqlite3.IntegrityError as exc:

            raise ValueError(
                "Route already exists."
            ) from exc


def fetch_routes_by_category(
    category_slug: str,
) -> list[dict[str, Any]]:
    """
    Return all active routes for a category.
    """

    query = """
    SELECT *
    FROM category_routes
    WHERE category_slug = ?
      AND status = 'ACTIVE'
    ORDER BY priority
    """

    with get_connection() as connection:

        rows = connection.execute(
            query,
            (category_slug,),
        ).fetchall()

    return [dict(row) for row in rows]


def fetch_route(
    route_id: int,
) -> dict[str, Any] | None:
    """
    Return a route by ID.
    """

    query = """
    SELECT *
    FROM category_routes
    WHERE route_id = ?
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (route_id,),
        ).fetchone()

    return dict(row) if row else None


def fetch_active_routes() -> list[dict[str, Any]]:
    """
    Return all active routes.
    """

    query = """
    SELECT *
    FROM category_routes
    WHERE status = 'ACTIVE'
    ORDER BY
        category_slug,
        priority
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]