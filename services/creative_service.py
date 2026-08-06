"""
Creative Assets data access layer.

Handles all database operations for the creative_assets table, plus
the read-side queries needed by the creative worker to pick pending
AI content and resolve product images.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.database import get_connection

from creative.exceptions import RenderError


DEFAULT_TEMPLATE_ID = "home_01"
DEFAULT_BRAND_ID = "atlas"
DEFAULT_CTA = "Shop now"

# Product images are stored per ASIN next to the product registry.
PRODUCT_IMAGE_ROOT = Path("storage/products/amazon")


# ---------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------


def create_creative(
    ai_content_id: int,
    template_name: str,
    headline: str,
    image_path: str,
) -> int:
    """
    Create a creative asset.

    Args:
        ai_content_id:
            Owning AI content record.
        template_name:
            Template used to render the creative.
        headline:
            Creative headline (schema requires a non-null value).
        image_path:
            Absolute path of the rendered image.

    Returns:
        Newly created creative_id.
    """

    query = """
    INSERT INTO creative_assets (

        ai_content_id,
        template_name,
        headline,
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
                headline,
                image_path,
            ),
        )

        connection.commit()

        return int(cursor.lastrowid)


# ---------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------


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


def creative_exists(
    ai_content_id: int,
) -> bool:
    """
    Return True if any creative already exists for the AI content.

    Used for idempotency: a record that already has a creative (in
    any state) must never be rendered a second time.
    """

    query = """
    SELECT 1
    FROM creative_assets
    WHERE ai_content_id = ?
    LIMIT 1
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (ai_content_id,),
        ).fetchone()

    return row is not None


def fetch_pending_creative_content() -> list[dict[str, Any]]:
    """
    Return validated AI content that has no creative yet.

    Only content that passed validation (``validation_status='VALID'``)
    and has not already produced a creative is eligible, so re-running
    the worker never generates duplicates.

    Returns:
        Records with the fields the rendering engine needs:
        ``ai_content_id``, ``research_product_id``, ``product_name``,
        ``asin``, ``pinterest_title``, ``pinterest_description``,
        ``rating`` and ``price``.
    """

    query = """
    SELECT
        ac.ai_content_id,
        ac.research_product_id,
        rp.product_name,
        rp.asin,
        ac.pinterest_title,
        ac.pinterest_description,
        rp.rating,
        rp.price
    FROM ai_content ac
    INNER JOIN research_products rp
        ON ac.research_product_id = rp.research_product_id
    WHERE
        ac.status = 'GENERATED'
        AND ac.validation_status = 'VALID'
        AND NOT EXISTS (
            SELECT 1
            FROM creative_assets ca
            WHERE ca.ai_content_id = ac.ai_content_id
        )
    ORDER BY ac.ai_content_id
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]


def resolve_local_product_image(
    product: dict[str, Any],
) -> Path:
    """
    Resolve the local product image for a research product.

    Images live at ``storage/products/amazon/<asin>/original.jpg``.

    Raises:
        RenderError:
            If the product has no ASIN or the image file is missing.
    """

    asin = product.get("asin")

    if not asin:
        raise RenderError(
            f"Product '{product.get('product_name', '?')}' has no "
            "ASIN to resolve a local image."
        )

    image_path = PRODUCT_IMAGE_ROOT / str(asin) / "original.jpg"

    if not image_path.is_file():
        raise RenderError(
            f"Local product image not found: {image_path}"
        )

    return image_path


def build_render_content(
    product: dict[str, Any],
) -> dict[str, object]:
    """
    Build the content dict consumed by the rendering engine.

    Maps the database record to the data-map targets used by the
    default template (``pinterest_title``, ``pinterest_description``,
    ``rating``, ``price``, ``cta``).
    """

    content: dict[str, object] = {
        "pinterest_title": product.get("pinterest_title") or "",
        "pinterest_description": (
            product.get("pinterest_description") or ""
        ),
        "rating": product.get("rating") or 0,
        "price": str(product.get("price") or ""),
        "cta": DEFAULT_CTA,
    }

    return content


# ---------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------


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

    The failure message is stored on the ``error`` column so the
    reason survives for debugging.
    """

    query = """
    UPDATE creative_assets
    SET
        status = 'FAILED',
        error = ?
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


def record_creative_failure(
    ai_content_id: int,
    template_name: str,
    headline: str,
    error: str,
) -> int:
    """
    Record a FAILED creative for AI content that could not render.

    Creates a creative_assets row in FAILED state carrying the error
    message, so invalid or failed creatives are persisted (not
    silently dropped) and remain idempotent on re-run.

    Returns:
        Newly created creative_id.
    """

    query = """
    INSERT INTO creative_assets (

        ai_content_id,
        template_name,
        headline,
        image_path,
        status,
        error

    )
    VALUES (?, ?, ?, '', 'FAILED', ?)
    """

    with get_connection() as connection:

        cursor = connection.execute(
            query,
            (
                ai_content_id,
                template_name,
                headline,
                error,
            ),
        )

        connection.commit()

        return int(cursor.lastrowid)


# ---------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------


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
