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
