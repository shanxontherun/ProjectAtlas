"""
Research Products data access layer.

Handles all database operations for the research_products table.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from database import get_connection


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
    Insert a research product and return its ID.
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
            raise sqlite3.Error("Failed to create research product.")

        return int(cursor.lastrowid)


def fetch_all_research_products() -> list[dict[str, Any]]:
    """
    Return every research product.
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