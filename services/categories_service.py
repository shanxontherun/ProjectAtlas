"""
Categories data access layer (ATLAS-029 NEXT PHASE, Phase 2).

Categories are frontend-managed entities. A category is linked to
Pinterest accounts and boards through ``category_routes``: one row per
(category, account, board) assignment. Relationships are database-backed
via foreign keys; boards are matched by their Atlas ``board_id`` and, when
available, expose the real Pinterest board ID (``pinterest_board_id``).

The legacy ``category_routes.category_slug`` column is kept in sync with
``categories.category_slug`` so the current publishing queue path (which
still routes by slug) continues to work unchanged.

All account / board / connection metadata surfaced here is safe: the
Pinterest connection read only exposes ``is_seed`` and ``connection_status``
from ``account_connections`` and never touches credentials.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any

from services.database import get_connection


def slugify(value: str) -> str:
    """Turn a display name into a stable lower-underscore slug."""

    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return slug.strip("_")


def _category_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "category_id": int(row["category_id"]),
        "category_name": str(row["category_name"]),
        "category_slug": row["category_slug"],
        "priority": int(row["priority"]),
        "status": str(row["status"]),
        "daily_target": int(row["daily_target"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "active_routes": int(row["active_routes"] or 0),
        "mapped_accounts": int(row["mapped_accounts"] or 0),
        "mapped_boards": int(row["mapped_boards"] or 0),
    }


# --------------------------------------------------
# Category CRUD
# --------------------------------------------------


def list_categories() -> list[dict[str, Any]]:
    """Return every category with route counts, highest priority first."""

    query = """
    SELECT
        c.category_id,
        c.category_name,
        c.category_slug,
        c.priority,
        c.status,
        c.daily_target,
        c.created_at,
        c.updated_at,
        COUNT(cr.route_id) AS active_routes,
        COUNT(DISTINCT cr.account_id) AS mapped_accounts,
        COUNT(DISTINCT cr.board_id) AS mapped_boards
    FROM categories c
    LEFT JOIN category_routes cr
        ON cr.category_id = c.category_id
       AND cr.status = 'ACTIVE'
    GROUP BY c.category_id
    ORDER BY c.priority DESC, c.category_id ASC
    """

    with get_connection() as connection:
        rows = connection.execute(query).fetchall()

    return [_category_dict(row) for row in rows]


def fetch_category(category_id: int) -> dict[str, Any] | None:
    """Return a single category with route counts, or None."""

    query = """
    SELECT
        c.category_id,
        c.category_name,
        c.category_slug,
        c.priority,
        c.status,
        c.daily_target,
        c.created_at,
        c.updated_at,
        COUNT(cr.route_id) AS active_routes,
        COUNT(DISTINCT cr.account_id) AS mapped_accounts,
        COUNT(DISTINCT cr.board_id) AS mapped_boards
    FROM categories c
    LEFT JOIN category_routes cr
        ON cr.category_id = c.category_id
       AND cr.status = 'ACTIVE'
    WHERE c.category_id = ?
    GROUP BY c.category_id
    """

    with get_connection() as connection:
        row = connection.execute(query, (category_id,)).fetchone()

    return _category_dict(row) if row else None


def _slug_exists(connection: sqlite3.Connection, slug: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM categories WHERE category_slug = ? LIMIT 1",
        (slug,),
    ).fetchone()
    return row is not None


def create_category(
    name: str,
    slug: str | None = None,
    priority: int = 5,
    daily_target: int = 5,
    status: str = "ACTIVE",
) -> int:
    """
    Create a category and return its category_id.

    A slug is derived from the name when none is supplied. Empty names and
    slugs are rejected; duplicate names and slugs raise ValueError.

    Raises:
        ValueError: If the name is empty, the slug is empty, or the name /
            slug is already taken.
    """

    clean_name = name.strip()
    clean_slug = (slug or "").strip() or slugify(clean_name)

    if not clean_name:
        raise ValueError("Category name is required.")

    if not clean_slug:
        raise ValueError("Category slug is required.")

    query = """
    INSERT INTO categories (
        category_name,
        category_slug,
        priority,
        daily_target,
        status
    )
    VALUES (?, ?, ?, ?, ?)
    """

    with get_connection() as connection:
        if _slug_exists(connection, clean_slug):
            raise ValueError(
                f"A category with slug '{clean_slug}' already exists."
            )

        try:
            cursor = connection.execute(
                query,
                (clean_name, clean_slug, priority, daily_target, status),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                f"A category named '{clean_name}' already exists."
            ) from exc

    if cursor.lastrowid is None:
        raise sqlite3.Error("Insert succeeded but no category_id was returned.")

    return int(cursor.lastrowid)


def update_category(
    category_id: int,
    name: str | None = None,
    slug: str | None = None,
    priority: int | None = None,
    daily_target: int | None = None,
    status: str | None = None,
) -> dict[str, Any] | None:
    """
    Update a category's editable fields.

    The legacy ``category_routes.category_slug`` is kept in sync whenever
    the slug changes so the existing publishing queue path stays correct.
    Duplicate names and slugs raise ValueError.

    Returns:
        The updated category, or None if the category does not exist.

    Raises:
        ValueError: If a duplicate name/slug is chosen or the slug is empty.
    """

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM categories WHERE category_id = ?",
            (category_id,),
        ).fetchone()

        if row is None:
            return None

        new_name = (name if name is not None else row["category_name"]).strip()
        new_slug = slug if slug is not None else row["category_slug"]
        if new_slug is None:
            new_slug = slugify(new_name)

        new_slug = (new_slug or "").strip()

        if not new_name:
            raise ValueError("Category name cannot be empty.")

        if not new_slug:
            raise ValueError("Category slug cannot be empty.")

        if not _slug_exists(connection, new_slug):
            pass
        else:
            taken = connection.execute(
                "SELECT category_id FROM categories WHERE category_slug = ?",
                (new_slug,),
            ).fetchone()
            if taken is not None and int(taken["category_id"]) != category_id:
                raise ValueError(
                    f"A category with slug '{new_slug}' already exists."
                )

        new_priority = (
            priority if priority is not None else int(row["priority"])
        )
        new_daily_target = (
            daily_target if daily_target is not None else int(row["daily_target"])
        )
        new_status = status if status is not None else row["status"]

        try:
            connection.execute(
                """
                UPDATE categories
                SET category_name = ?,
                    category_slug = ?,
                    priority = ?,
                    daily_target = ?,
                    status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE category_id = ?
                """,
                (
                    new_name,
                    new_slug,
                    new_priority,
                    new_daily_target,
                    new_status,
                    category_id,
                ),
            )

            connection.execute(
                "UPDATE category_routes"
                " SET category_slug = ?"
                " WHERE category_id = ?",
                (new_slug, category_id),
            )

            connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                f"A category named '{new_name}' already exists."
            ) from exc

    return fetch_category(category_id)


def set_category_status(
    category_id: int,
    status: str,
) -> dict[str, Any] | None:
    """Archive (INACTIVE) or activate (ACTIVE) a category."""

    with get_connection() as connection:
        row = connection.execute(
            "SELECT category_id FROM categories WHERE category_id = ?",
            (category_id,),
        ).fetchone()

        if row is None:
            return None

        connection.execute(
            "UPDATE categories"
            " SET status = ?, updated_at = CURRENT_TIMESTAMP"
            " WHERE category_id = ?",
            (status, category_id),
        )
        connection.commit()

    return fetch_category(category_id)


# --------------------------------------------------
# Category <-> Account <-> Board routes
# --------------------------------------------------


_ROUTES_JOIN = """
    SELECT
        cr.route_id,
        cr.category_id,
        cr.category_slug,
        cr.account_id,
        cr.board_id,
        cr.priority,
        cr.status AS route_status,
        cr.created_at AS route_created_at,
        pa.account_name,
        pa.username,
        pa.is_seed,
        ac.connection_status,
        pb.board_name,
        pb.pinterest_board_id,
        pb.privacy,
        pb.status AS board_status
    FROM category_routes cr
    LEFT JOIN pinterest_accounts pa
        ON pa.account_id = cr.account_id
    LEFT JOIN account_connections ac
        ON ac.pinterest_account_id = cr.account_id
       AND ac.provider = 'PINTEREST'
    LEFT JOIN pinterest_boards pb
        ON pb.board_id = cr.board_id
"""


def _route_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "route_id": int(row["route_id"]),
        "category_id": int(row["category_id"]),
        "category_slug": row["category_slug"],
        "account_id": int(row["account_id"]),
        "account_name": row["account_name"],
        "username": row["username"],
        "is_seed": int(row["is_seed"] or 0) == 1,
        "connection_status": row["connection_status"],
        "board_id": int(row["board_id"]),
        "board_name": row["board_name"],
        "pinterest_board_id": row["pinterest_board_id"],
        "privacy": row["privacy"],
        "board_status": row["board_status"],
        "priority": int(row["priority"]),
        "route_status": str(row["route_status"]),
        "route_created_at": row["route_created_at"],
    }


def list_category_routes(
    category_id: int,
    *,
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    """Return the routes of a category with account and board detail."""

    query = _ROUTES_JOIN + "\n WHERE cr.category_id = ?"

    if not include_inactive:
        query += "\n   AND cr.status = 'ACTIVE'"

    query += "\n ORDER BY cr.priority ASC, cr.route_id ASC"

    with get_connection() as connection:
        rows = connection.execute(query, (category_id,)).fetchall()

    return [_route_dict(row) for row in rows]


def fetch_category_route(route_id: int) -> dict[str, Any] | None:
    """Return a single route with account and board detail, or None."""

    query = _ROUTES_JOIN + "\n WHERE cr.route_id = ?"

    with get_connection() as connection:
        row = connection.execute(query, (route_id,)).fetchone()

    return _route_dict(row) if row else None


def add_category_route(
    category_id: int,
    account_id: int,
    board_id: int,
    priority: int = 1,
) -> int:
    """
    Link a category to a Pinterest account and board.

    The board must belong to the given account and the pair must not
    already be routed for the category.

    Raises:
        ValueError: If the category does not exist, the account/board is
            missing or inactive, the board does not belong to the account,
            or the route already exists.
    """

    with get_connection() as connection:
        category = connection.execute(
            "SELECT category_id, category_slug FROM categories"
            " WHERE category_id = ?",
            (category_id,),
        ).fetchone()

        if category is None:
            raise ValueError("Category not found.")

        account = connection.execute(
            "SELECT account_id, status FROM pinterest_accounts"
            " WHERE account_id = ?",
            (account_id,),
        ).fetchone()

        if account is None:
            raise ValueError("Pinterest account not found.")

        if account["status"] != "ACTIVE":
            raise ValueError("Pinterest account is not active.")

        board = connection.execute(
            "SELECT board_id, account_id, status FROM pinterest_boards"
            " WHERE board_id = ?",
            (board_id,),
        ).fetchone()

        if board is None:
            raise ValueError("Pinterest board not found.")

        if int(board["account_id"]) != account_id:
            raise ValueError(
                "The selected board does not belong to the selected account."
            )

        if board["status"] != "ACTIVE":
            raise ValueError("Pinterest board is not active.")

        duplicate = connection.execute(
            "SELECT 1 FROM category_routes"
            " WHERE category_id = ? AND account_id = ? AND board_id = ?"
            " LIMIT 1",
            (category_id, account_id, board_id),
        ).fetchone()

        if duplicate is not None:
            raise ValueError(
                "This category is already routed to that account and board."
            )

        cursor = connection.execute(
            """
            INSERT INTO category_routes (
                category_id,
                category_slug,
                account_id,
                board_id,
                priority
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                category_id,
                category["category_slug"],
                account_id,
                board_id,
                priority,
            ),
        )

        connection.commit()

    if cursor.lastrowid is None:
        raise sqlite3.Error("Insert succeeded but no route_id was returned.")

    return int(cursor.lastrowid)


def update_category_route(
    route_id: int,
    priority: int | None = None,
    status: str | None = None,
) -> dict[str, Any] | None:
    """
    Update a route's priority and/or archive/restore it.

    Returns:
        The updated route, or None if the route does not exist.
    """

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM category_routes WHERE route_id = ?",
            (route_id,),
        ).fetchone()

        if row is None:
            return None

        new_priority = (
            priority if priority is not None else row["priority"]
        )
        new_status = status if status is not None else row["status"]

        connection.execute(
            """
            UPDATE category_routes
            SET priority = ?, status = ?
            WHERE route_id = ?
            """,
            (new_priority, new_status, route_id),
        )
        connection.commit()

    return fetch_category_route(route_id)
