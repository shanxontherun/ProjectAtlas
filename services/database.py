"""
Database access layer for Atlas Core API.

Uses the sqlite3 standard library module (no ORM).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

# SQLite file lives next to services/ at ../database/atlas.db
DATABASE_PATH: Path = Path(__file__).resolve().parent.parent / "database" / "atlas.db"


def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the Atlas SQLite database.

    Rows are returned as sqlite3.Row so callers can access columns by name.
    """
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DATABASE_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    # Enforce foreign key constraints for this connection
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def fetch_all_categories() -> list[dict[str, Any]]:
    """
    Return every row from the categories table as a list of dictionaries.

    Column names match the database schema so the API can serialize them
    directly to JSON.
    """
    query = """
        SELECT
            category_id,
            category_name,
            priority,
            status,
            daily_target,
            created_at,
            updated_at
        FROM categories
        ORDER BY priority DESC, category_id ASC
    """

    with get_connection() as connection:
        cursor = connection.execute(query)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def create_job(
    department: str,
    job_type: str,
    priority: int,
    payload: dict[str, Any] | None,
) -> int:
    """
    Insert a new job into the jobs table and return its job_id.

    The payload dict is serialized to JSON text before storage.
    Status defaults to PENDING via the table schema.
    """
    # Store structured payload as a JSON string (TEXT column)
    payload_text: str | None = (
        json.dumps(payload, ensure_ascii=False) if payload is not None else None
    )

    query = """
        INSERT INTO jobs (
            department,
            job_type,
            priority,
            payload
        )
        VALUES (?, ?, ?, ?)
    """

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                query,
                (department, job_type, priority, payload_text),
            )
            connection.commit()
            job_id = cursor.lastrowid
    except sqlite3.Error:
        # Re-raise so the API layer can map to an HTTP error response
        raise

    if job_id is None:
        raise sqlite3.Error("Insert succeeded but no job_id was returned")

    return int(job_id)


def claim_next_pending_job() -> dict[str, Any] | None:
    """
    Atomically claim the oldest PENDING job.

    Within a single SQLite transaction:
      1. Select the oldest row where status = 'PENDING'
      2. Mark it IN_PROGRESS and set started_at = CURRENT_TIMESTAMP

    Returns the claimed job as a dict, or None when the queue is empty.
    Payload TEXT is deserialized back into a Python object for the API.
    """
    # Oldest first; job_id breaks ties for stable ordering
    select_query = """
        SELECT
            job_id,
            department,
            job_type,
            priority,
            payload,
            status
        FROM jobs
        WHERE status = 'PENDING'
        ORDER BY created_at ASC, job_id ASC
        LIMIT 1
    """

    update_query = """
        UPDATE jobs
        SET
            status = 'IN_PROGRESS',
            started_at = CURRENT_TIMESTAMP
        WHERE job_id = ?
          AND status = 'PENDING'
    """

    connection = get_connection()
    try:
        # BEGIN IMMEDIATE locks the DB for write so two workers cannot claim
        # the same job between SELECT and UPDATE.
        connection.execute("BEGIN IMMEDIATE")

        row = connection.execute(select_query).fetchone()
        if row is None:
            connection.rollback()
            return None

        job_id = int(row["job_id"])
        cursor = connection.execute(update_query, (job_id,))

        # Guard against a race if another connection somehow claimed it
        if cursor.rowcount != 1:
            connection.rollback()
            return None

        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()

    # Deserialize payload JSON text for the response body
    payload_raw: str | None = row["payload"]
    payload: Any
    if payload_raw is None:
        payload = None
    else:
        payload = json.loads(payload_raw)

    return {
        "job_id": job_id,
        "department": row["department"],
        "job_type": row["job_type"],
        "priority": row["priority"],
        "payload": payload,
        "status": "IN_PROGRESS",
    }


def update_job_status(
    job_id: int,
    new_status: str,
    error_message: str | None = None,
) -> dict[str, Any] | None:
    """
    Update a job's status and mark it completed.

    Always sets completed_at = CURRENT_TIMESTAMP.
    When error_message is provided, it is persisted on the row.

    Returns {"job_id", "status"} on success, or None if the job_id
    does not exist.
    """
    # Build SET clause dynamically so error_message is only written when sent
    set_clauses: list[str] = [
        "status = ?",
        "completed_at = CURRENT_TIMESTAMP",
    ]
    params: list[Any] = [new_status]

    if error_message is not None:
        set_clauses.append("error_message = ?")
        params.append(error_message)

    params.append(job_id)

    query = f"""
        UPDATE jobs
        SET {", ".join(set_clauses)}
        WHERE job_id = ?
    """

    try:
        with get_connection() as connection:
            cursor = connection.execute(query, params)
            connection.commit()
            rowcount = cursor.rowcount
    except sqlite3.Error:
        raise

    if rowcount == 0:
        return None

    return {
        "job_id": job_id,
        "status": new_status,
    }



def insert_research_product(
    job_id: int,
    category: str,
    product_name: str,
    product_url: str,
    source: str = "Amazon",
    price: float | None = None,
    currency: str = "USD",
    rating: float | None = None,
    review_count: int | None = None,
    image_url: str | None = None,
    ai_summary: str | None = None,
) -> int:
    """
    Insert a research product and return its research_product_id.
    """

    query = """
        INSERT INTO research_products (
            job_id,
            category,
            product_name,
            product_url,
            source,
            price,
            currency,
            rating,
            review_count,
            image_url,
            ai_summary
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    with get_connection() as connection:
        cursor = connection.execute(
            query,
            (
                job_id,
                category,
                product_name,
                product_url,
                source,
                price,
                currency,
                rating,
                review_count,
                image_url,
                ai_summary,
            ),
        )
        connection.commit()

    if cursor.lastrowid is None:
        raise sqlite3.Error("Insert succeeded but no research_product_id was returned")

    return int(cursor.lastrowid)


def fetch_all_research_products() -> list[dict[str, Any]]:
    
    """
    Return every research product ordered by research_product_id.
    """

    query = """
        SELECT
            research_product_id,
            job_id,
            category,
            product_name,
            product_url,
            source,
            price,
            currency,
            rating,
            review_count,
            image_url,
            ai_summary,
            status,
            created_at
        FROM research_products
        ORDER BY research_product_id ASC
    """

    with get_connection() as connection:
        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]

def product_exists(product_key: str) -> bool:
    """
    Return True if the product already exists in the registry.
    """

    query = """
        SELECT 1
        FROM product_registry
        WHERE product_key = ?
        LIMIT 1
    """

    with get_connection() as connection:
        row = connection.execute(query, (product_key,)).fetchone()

    return row is not None


def create_product_registry_entry(
    product_key: str,
    product_url: str,
    product_name: str,
    category: str,
    source: str = "Amazon",
    asin: str | None = None,
    last_job_id: int | None = None,
) -> int:
    """
    Insert a new product into the registry.
    Returns the generated product_id.
    """

    query = """
        INSERT INTO product_registry (
            product_key,
            product_url,
            asin,
            product_name,
            category,
            source,
            last_job_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    with get_connection() as connection:
        cursor = connection.execute(
            query,
            (
                product_key,
                product_url,
                asin,
                product_name,
                category,
                source,
                last_job_id,
            ),
        )
        connection.commit()

    if cursor.lastrowid is None:
        raise sqlite3.Error(
            "Insert succeeded but no product_id was returned"
        )

    return int(cursor.lastrowid)

def touch_product(
    product_key: str,
    last_job_id: int | None = None,
) -> None:
    """
    Update the last_seen_at timestamp for an existing product.
    """

    query = """
        UPDATE product_registry
        SET
            last_seen_at = CURRENT_TIMESTAMP,
            last_job_id = ?
        WHERE product_key = ?
    """

    with get_connection() as connection:
        connection.execute(
            query,
            (
                last_job_id,
                product_key,
            ),
        )
        connection.commit()


def create_pin(
    research_product_id: int,
    pinterest_title: str | None = None,
    pinterest_description: str | None = None,
    pinterest_keywords: str | None = None,
    board_name: str | None = None,
    affiliate_url: str | None = None,
    image_url: str | None = None,
) -> int:
    """
    Insert a new Pinterest queue item.

    Returns the generated pin_id.
    """

    query = """
        INSERT INTO pinterest_queue (
            research_product_id,
            pinterest_title,
            pinterest_description,
            pinterest_keywords,
            board_name,
            affiliate_url,
            image_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    with get_connection() as connection:
        cursor = connection.execute(
            query,
            (
                research_product_id,
                pinterest_title,
                pinterest_description,
                pinterest_keywords,
                board_name,
                affiliate_url,
                image_url,
            ),
        )
        connection.commit()

    if cursor.lastrowid is None:
        raise sqlite3.Error(
            "Insert succeeded but no pin_id was returned"
        )

    return int(cursor.lastrowid)  

def fetch_pending_pins() -> list[dict[str, Any]]:
    """
    Return every Pinterest queue item waiting to be processed.
    """

    query = """
        SELECT
            pin_id,
            research_product_id,
            pinterest_title,
            pinterest_description,
            pinterest_keywords,
            board_name,
            affiliate_url,
            image_url,
            status,
            scheduled_at,
            published_at,
            created_at
        FROM pinterest_queue
        WHERE status = 'PENDING'
        ORDER BY created_at ASC
    """

    with get_connection() as connection:
        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]

def mark_pin_ready(pin_id: int) -> None:
    """
    Mark a Pinterest queue item as READY.
    """

    query = """
        UPDATE pinterest_queue
        SET status = 'READY'
        WHERE pin_id = ?
    """

    with get_connection() as connection:
        connection.execute(query, (pin_id,))
        connection.commit()   

def mark_pin_published(pin_id: int) -> None:
    """
    Mark a Pinterest queue item as PUBLISHED.
    """

    query = """
        UPDATE pinterest_queue
        SET
            status = 'PUBLISHED',
            published_at = CURRENT_TIMESTAMP
        WHERE pin_id = ?
    """

    with get_connection() as connection:
        connection.execute(query, (pin_id,))
        connection.commit()

def mark_pin_failed(pin_id: int) -> None:
    """
    Mark a Pinterest queue item as FAILED.
    """

    query = """
        UPDATE pinterest_queue
        SET status = 'FAILED'
        WHERE pin_id = ?
    """

    with get_connection() as connection:
        connection.execute(query, (pin_id,))
        connection.commit()
           