"""
Research Products Repository.

Handles all database operations for the research_products table.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from services.database import get_connection


# ---------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------


def insert_research_product(
    job_id: int,
    asin: str | None,
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
    Insert a research product and return its ID.
    """

    query = """
    INSERT INTO research_products (

        job_id,
        asin,
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
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    with get_connection() as connection:

        cursor = connection.execute(
            query,
            (
                job_id,
                asin,
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
            raise sqlite3.Error(
                "Failed to create research product."
            )

        return int(cursor.lastrowid)


# ---------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------


def fetch_all_research_products() -> list[dict[str, Any]]:

    query = """
    SELECT *
    FROM research_products
    ORDER BY research_product_id
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]


def fetch_pending_research_products() -> list[dict[str, Any]]:

    query = """
    SELECT *
    FROM research_products
    WHERE status='NEW'
    ORDER BY research_product_id
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]


def fetch_products_pending_images() -> list[dict[str, Any]]:
    """
    Products waiting for image download.
    """

    query = """
    SELECT *

    FROM research_products

    WHERE

        image_status='PENDING'

        AND image_url IS NOT NULL

        AND image_url<>''

    ORDER BY research_product_id
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]


def fetch_product_by_asin(
    asin: str,
) -> dict[str, Any] | None:
    """
    Return a product if it already exists.
    """

    query = """
    SELECT *
    FROM research_products
    WHERE asin=?
    LIMIT 1
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (asin,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


# ---------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------


def mark_image_downloaded(
    research_product_id: int,
    local_image_path: str,
) -> None:

    query = """
    UPDATE research_products

    SET

        local_image_path=?,
        image_status='DOWNLOADED'

    WHERE research_product_id=?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (
                local_image_path,
                research_product_id,
            ),
        )

        connection.commit()


def mark_image_failed(
    research_product_id: int,
) -> None:

    query = """
    UPDATE research_products

    SET image_status='FAILED'

    WHERE research_product_id=?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (
                research_product_id,
            ),
        )

        connection.commit()