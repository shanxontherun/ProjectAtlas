"""
Pinterest Queue data access layer.

Handles all database operations for the pinterest_queue table.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from services.database import get_connection


def create_queue_item(
    ai_content_id: int,
    account_id: int,
    board_id: int,
    affiliate_url: str | None = None,
    image_url: str | None = None,
    publish_order: int = 1,
) -> int:
    """
    Create a Pinterest queue item.

    Raises:
        ValueError:
            If the queue item already exists.
    """

    query = """
    INSERT INTO pinterest_queue (
        ai_content_id,
        account_id,
        board_id,
        affiliate_url,
        image_url,
        publish_order,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
    """

    with get_connection() as connection:

        try:

            cursor = connection.execute(
                query,
                (
                    ai_content_id,
                    account_id,
                    board_id,
                    affiliate_url,
                    image_url,
                    publish_order,
                ),
            )

            connection.commit()

            if cursor.lastrowid is None:
                raise sqlite3.Error(
                    "Failed to create queue item."
                )

            return int(cursor.lastrowid)

        except sqlite3.IntegrityError as exc:

            raise ValueError(
                "Queue item already exists."
            ) from exc


def fetch_pending_queue() -> list[dict[str, Any]]:
    """
    Return all pending queue items.
    """

    query = """
    SELECT *
    FROM pinterest_queue
    WHERE status = 'PENDING'
    ORDER BY
        publish_order,
        created_at
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]

def fetch_next_pending_queue(
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Return the next queue items waiting to be published.
    """

    query = """
    SELECT
        pq.*,
        ac.pinterest_title,
        ac.pinterest_description,
        ac.pinterest_keywords,

        pa.account_name,
        pb.board_name

    FROM pinterest_queue pq

    INNER JOIN ai_content ac
        ON pq.ai_content_id = ac.ai_content_id

    INNER JOIN pinterest_accounts pa
        ON pq.account_id = pa.account_id

    INNER JOIN pinterest_boards pb
        ON pq.board_id = pb.board_id
        
    WHERE pq.status = 'PENDING'
    ORDER BY
        pq.publish_order,
        pq.created_at
    LIMIT ?
    """

    with get_connection() as connection:

        rows = connection.execute(
            query,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def fetch_ready_queue() -> list[dict[str, Any]]:
    """
    Return all READY queue items.
    """

    query = """
    SELECT *
    FROM pinterest_queue
    WHERE status = 'READY'
    ORDER BY
        scheduled_at,
        publish_order
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]


def fetch_queue_by_ai_content(
    ai_content_id: int,
) -> list[dict[str, Any]]:
    """
    Return all queue items for an AI content record.
    """

    query = """
    SELECT *
    FROM pinterest_queue
    WHERE ai_content_id = ?
    ORDER BY publish_order
    """

    with get_connection() as connection:

        rows = connection.execute(
            query,
            (ai_content_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def fetch_queue_item(
    pin_id: int,
) -> dict[str, Any] | None:
    """
    Return a queue item by ID.
    """

    query = """
    SELECT *
    FROM pinterest_queue
    WHERE pin_id = ?
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (pin_id,),
        ).fetchone()

    return dict(row) if row else None


def mark_queue_ready(
    pin_id: int,
) -> None:
    """
    Mark a queue item as READY.
    """

    query = """
    UPDATE pinterest_queue
    SET status = 'READY'
    WHERE pin_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (pin_id,),
        )

        connection.commit()


def mark_queue_published(
    pin_id: int,
) -> None:
    """
    Mark a queue item as PUBLISHED.
    """

    query = """
    UPDATE pinterest_queue
    SET
        status = 'PUBLISHED',
        published_at = CURRENT_TIMESTAMP
    WHERE pin_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (pin_id,),
        )

        connection.commit()


def mark_queue_failed(
    pin_id: int,
    error: str,
) -> None:
    """
    Mark a queue item as FAILED.
    """

    query = """
    UPDATE pinterest_queue
    SET
        status = 'FAILED',
        retry_count = retry_count + 1,
        last_error = ?
    WHERE pin_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (
                error,
                pin_id,
            ),
        )

        connection.commit()



    