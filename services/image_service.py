"""
Image Service.

Updates image information stored directly on research_products.
"""

from __future__ import annotations

from services.database import get_connection


def fetch_products_pending_images() -> list[dict]:
    """
    Return products whose images still need downloading.
    """

    query = """
    SELECT
        research_product_id,
        asin,
        product_name,
        image_url,
        local_image_path,
        image_status
    FROM research_products
    WHERE
        image_status='PENDING'
        AND image_url IS NOT NULL
        AND image_url <> ''
    ORDER BY research_product_id
    """

    with get_connection() as connection:
        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]


def mark_image_downloaded(
    research_product_id: int,
    local_image_path: str,
) -> None:
    """
    Save local image path and mark download complete.
    """

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
    """
    Mark image download failed.
    """

    query = """
    UPDATE research_products
    SET image_status='FAILED'
    WHERE research_product_id=?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (research_product_id,),
        )

        connection.commit()