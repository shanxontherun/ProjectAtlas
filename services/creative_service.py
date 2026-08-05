"""
Creative Assets data access layer.

Handles all database operations for the creative_assets table.
"""

from __future__ import annotations

from typing import Any

from services.database import get_connection


def create_creative(
    ai_content_id: int,
    template_name: str,
    creative_brief: str | None,
    image_path: str,
) -> int:
    """
    Create a creative asset.

    Returns:
        Newly created creative_id.
    """

    query = """
    INSERT INTO creative_assets (

        ai_content_id,
        template_name,
        creative_brief,
        image_path,
        status

    )
    VALUES (?, ?, ?, ?, 'GENERATED')
    """

    with get_connection() as connection:

        cursor = connection.execute(
            query,
            (
                ai_content_id,
                template_name,
                creative_brief,
                image_path,
            ),
        )

        connection.commit()

        return int(cursor.lastrowid)


def fetch_creative(
    creative_id: int,
) -> dict[str, Any] | None:
    """
    Return a creative asset by ID.
    """

    query = """
    SELECT *
    FROM creative_assets
    WHERE creative_id = ?
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (creative_id,),
        ).fetchone()

    return dict(row) if row else None


def fetch_creatives_by_ai_content(
    ai_content_id: int,
) -> list[dict[str, Any]]:
    """
    Return all creatives for an AI content record.
    """

    query = """
    SELECT *
    FROM creative_assets
    WHERE ai_content_id = ?
    ORDER BY created_at
    """

    with get_connection() as connection:

        rows = connection.execute(
            query,
            (ai_content_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def fetch_generated_creatives() -> list[dict[str, Any]]:
    """
    Return all generated creatives.
    """

    query = """
    SELECT *
    FROM creative_assets
    WHERE status = 'GENERATED'
    ORDER BY created_at
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]


def mark_creative_generated(
    creative_id: int,
) -> None:
    """
    Mark a creative as generated.
    """

    query = """
    UPDATE creative_assets
    SET status = 'GENERATED'
    WHERE creative_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (creative_id,),
        )

        connection.commit()


def mark_creative_failed(
    creative_id: int,
    error: str,
) -> None:
    """
    Mark a creative as failed.
    """

    query = """
    UPDATE creative_assets
    SET
        status = 'FAILED',
        creative_brief = ?
    WHERE creative_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (
                error,
                creative_id,
            ),
        )

        connection.commit()


def delete_creative(
    creative_id: int,
) -> None:
    """
    Delete a creative asset.
    """

    query = """
    DELETE
    FROM creative_assets
    WHERE creative_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (creative_id,),
        )

        connection.commit()