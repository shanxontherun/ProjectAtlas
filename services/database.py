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
