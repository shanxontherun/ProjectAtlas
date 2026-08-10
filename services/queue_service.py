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
    AND pa.is_seed = 0
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


# ---------------------------------------------------------------------
# PUBLISHING READ MODEL
# ---------------------------------------------------------------------


_PUBLISHING_SELECT = """
    SELECT
        pq.pin_id,
        pq.ai_content_id,
        pq.account_id,
        pq.board_id,
        pq.affiliate_url,
        pq.image_url,
        pq.publish_order,
        pq.status AS queue_status,
        pq.scheduled_at,
        pq.published_at,
        pq.last_error,
        pq.created_at AS queued_at,

        rp.research_product_id,
        rp.product_name,
        rp.category,
        rp.price,
        rp.rating,
        rp.asin,

        ac.ai_score,
        ac.pinterest_title,
        ac.pinterest_description,

        ca.creative_id,
        ca.headline AS creative_headline,
        ca.selected_template,
        ca.selected_variant,
        ca.properties_json,
        ca.image_path AS creative_image_path,

        pa.account_name,
        pa.username,
        pa.niche_slug,
        pa.is_seed,

        pb.board_name,
        pb.category_slug AS board_category_slug,
        pb.pin_count,
        pb.follower_count
    FROM pinterest_queue pq
    INNER JOIN ai_content ac
        ON pq.ai_content_id = ac.ai_content_id
    INNER JOIN research_products rp
        ON ac.research_product_id = rp.research_product_id
    LEFT JOIN creative_assets ca
        ON ca.ai_content_id = ac.ai_content_id
    INNER JOIN pinterest_accounts pa
        ON pq.account_id = pa.account_id
    INNER JOIN pinterest_boards pb
        ON pq.board_id = pb.board_id
"""


def fetch_publishing_rows(
    statuses: tuple[str, ...],
    real_accounts_only: bool = False,
) -> list[dict[str, Any]]:
    """
    Return publishing rows filtered by queue status.

    Joins the queue to the AI content, research product, creative,
    account and board so the Publishing Center read model needs a single
    query instead of scattering lookups across tables.

    When ``real_accounts_only`` is set, rows tied to seed accounts are
    excluded so migration-016 seed activity never appears as real
    Pinterest publishing records.
    """

    placeholders = ",".join("?" for _ in statuses)

    query = (
        _PUBLISHING_SELECT
        + f"\nWHERE pq.status IN ({placeholders})"
    )

    params: list[Any] = list(statuses)

    if real_accounts_only:

        query += "\nAND pa.is_seed = 0"

    query += "\nORDER BY pq.publish_order, pq.created_at"

    with get_connection() as connection:

        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def fetch_queue_item_details(
    pin_id: int,
) -> dict[str, Any] | None:
    """
    Return a single publishing row for a queue item.

    Used by publish-now so the endpoint can feed the exact same joined
    fields as the publisher worker without duplicating the query.
    """

    query = _PUBLISHING_SELECT + "\nWHERE pq.pin_id = ?"

    with get_connection() as connection:

        row = connection.execute(
            query,
            (pin_id,),
        ).fetchone()

    return dict(row) if row else None


def fetch_publishing_summary() -> dict[str, int]:
    """
    Return the Publishing Center summary counts.

    Ready and scheduled counts come from the real queue records created
    by the publishing workflow. Published and failed counts are derived
    only from queue items on real (non-seed) accounts, so migration-016
    seed activity never reports as real Pinterest publishing. Boards
    counts the active configured boards.
    """

    query = """
    SELECT status, COUNT(*) AS total
    FROM pinterest_queue
    GROUP BY status
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    counts = {row["status"]: row["total"] for row in rows}

    real_query = """
    SELECT pq.status, COUNT(*) AS total
    FROM pinterest_queue pq
    INNER JOIN pinterest_accounts pa
        ON pq.account_id = pa.account_id
    WHERE pa.is_seed = 0
    GROUP BY pq.status
    """

    with get_connection() as connection:

        real_rows = connection.execute(real_query).fetchall()

    real_counts = {row["status"]: row["total"] for row in real_rows}

    boards_query = """
    SELECT COUNT(*) AS total
    FROM pinterest_boards
    WHERE status = 'ACTIVE'
    """

    with get_connection() as connection:

        board_row = connection.execute(boards_query).fetchone()

    return {
        "ready": int(counts.get("PENDING", 0)),
        "scheduled": int(counts.get("READY", 0)),
        "published": int(real_counts.get("PUBLISHED", 0)),
        "failed": int(real_counts.get("FAILED", 0)),
        "boards": int(board_row["total"]) if board_row else 0,
    }


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


def mark_queue_scheduled(
    pin_id: int,
    scheduled_at: str,
) -> None:
    """
    Mark a queue item as READY with a scheduled publish time.

    READY items are picked up by the publishing flow and appear in the
    Publishing Center as scheduled pins.
    """

    query = """
    UPDATE pinterest_queue
    SET
        status = 'READY',
        scheduled_at = ?
    WHERE pin_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (
                scheduled_at,
                pin_id,
            ),
        )

        connection.commit()


def update_queue_board(
    pin_id: int,
    account_id: int,
    board_id: int,
) -> None:
    """
    Update the destination account and board of a queue item.

    Keeps the item queued for the same content while the user refines
    the Pinterest destination in the Publishing Center.
    """

    query = """
    UPDATE pinterest_queue
    SET
        account_id = ?,
        board_id = ?
    WHERE pin_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (
                account_id,
                board_id,
                pin_id,
            ),
        )

        connection.commit()


def mark_queue_cancelled(
    pin_id: int,
) -> None:
    """
    Mark a queue item as CANCELLED.

    Cancelling removes the item from the active publishing queue without
    deleting the row, preserving the audit trail for the history view.
    """

    query = """
    UPDATE pinterest_queue
    SET status = 'CANCELLED'
    WHERE pin_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (pin_id,),
        )

        connection.commit()


def fetch_active_queue_by_ai_content(
    ai_content_id: int,
) -> list[dict[str, Any]]:
    """
    Return active (non-terminal) queue items for AI content.

    Used to keep a creative's publishing queue singleton: an approved
    creative already sitting in the queue must not be queued twice.
    """

    query = """
    SELECT *
    FROM pinterest_queue
    WHERE
        ai_content_id = ?
        AND status NOT IN ('PUBLISHED', 'FAILED', 'CANCELLED')
    """

    with get_connection() as connection:

        rows = connection.execute(
            query,
            (ai_content_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def find_cancelled_queue_item(
    ai_content_id: int,
    account_id: int,
    board_id: int,
) -> dict[str, Any] | None:
    """
    Return a CANCELLED queue item matching the same content and
    destination, if any.

    Re-queueing a creative after it was removed from the publishing
    queue must reuse the cancelled row (the queue table's UNIQUE
    constraint on ``(ai_content_id, account_id, board_id)`` forbids a
    fresh insert with the same destination).
    """

    query = """
    SELECT *
    FROM pinterest_queue
    WHERE
        ai_content_id = ?
        AND account_id = ?
        AND board_id = ?
        AND status = 'CANCELLED'
    ORDER BY pin_id DESC
    LIMIT 1
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (
                ai_content_id,
                account_id,
                board_id,
            ),
        ).fetchone()

    return dict(row) if row else None


def reactivate_queue_item(
    pin_id: int,
) -> None:
    """
    Return a cancelled queue item to the active publishing queue.

    Resets the status to PENDING and clears the scheduling and publish
    timestamps so the item appears as a fresh, ready-to-publish pin.
    """

    query = """
    UPDATE pinterest_queue
    SET
        status = 'PENDING',
        scheduled_at = NULL,
        published_at = NULL,
        last_error = NULL
    WHERE pin_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (pin_id,),
        )

        connection.commit()



    