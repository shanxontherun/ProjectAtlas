"""
Creative Assets data access layer.

Handles all database operations for the creative_assets table, plus
the read-side queries needed by the creative worker to pick pending
AI content and resolve product images.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from creative.exceptions import CreativeError, RenderError
from creative.registry import TemplateRegistry
from creative.rendering import RenderingEngine

from services.database import get_connection


DEFAULT_TEMPLATE_ID = "home_01"
DEFAULT_BRAND_ID = "atlas"
DEFAULT_CTA = "Shop now"

# Product images are stored per ASIN next to the product registry.
# Anchored to the workspace root so the path resolves regardless of the
# process cwd (uvicorn runs from services/, workers from the repo root).
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PRODUCT_IMAGE_ROOT = _WORKSPACE_ROOT / "storage" / "products" / "amazon"

# Structured development logging around creative generation. Disabled
# in production by setting ATLAS_DEV_LOG=0.
DEV_LOG_ENABLED = os.getenv("ATLAS_DEV_LOG", "1") == "1"

logger = logging.getLogger(__name__)


class CreativeContentNotFoundError(Exception):
    """
    Raised when no AI content exists for a research product.

    A creative can only be generated for a product that has already
    produced AI content (Creative Studio consumes AI Studio output).
    """


class CreativeLockedError(Exception):
    """
    Raised when a creative is no longer editable.

    Approved and queued creatives are read-only: their presentation
    state (template, variant, properties) is frozen after approval, so
    the Studio must never mutate them server-side.
    """


def _dev_log(event: str, **fields: Any) -> None:
    """
    Emit a structured development log line for creative generation.

    Development only: no-op when ATLAS_DEV_LOG != "1".
    """

    if not DEV_LOG_ENABLED:
        return

    record: dict[str, Any] = {
        "event": event,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    record.update(fields)

    logger.info("CREATIVE %s %s", event, json.dumps(record, default=str))


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


def fetch_creative_content_for_product(
    research_product_id: int,
) -> dict[str, Any] | None:
    """
    Return the render record for a research product's AI content.

    Mirrors the field contract of ``fetch_pending_creative_content``
    so the API-driven generation path (POST /creatives/generate) feeds
    the same rendering pipeline as the worker.
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
    WHERE ac.research_product_id = ?
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (research_product_id,),
        ).fetchone()

    return dict(row) if row else None


def fetch_creatives_workflow(
    research_product_id: int | None = None,
) -> list[dict[str, Any]]:
    """
    Return every research product with AI content and its creative (if any).

    This is the Creative Studio queue read model. Rows join
    ``research_products`` to ``ai_content`` (INNER) so only products
    that have already produced AI content appear, then LEFT JOIN to
    ``creative_assets`` so waiting items (creative_id is NULL) render
    alongside generated and approved ones.

    Pass a ``research_product_id`` to filter to a single product
    (used after generate/approve so the API can return the updated row).
    """

    query = """
    SELECT
        rp.research_product_id,
        rp.product_name,
        rp.category,
        rp.image_url,
        rp.price,
        rp.rating,
        rp.review_count,
        rp.asin,
        ac.ai_content_id,
        ac.pinterest_title,
        ac.pinterest_description,
        ac.ai_score,
        ac.status AS ai_status,
        ac.validation_status,
        ca.creative_id,
        ca.template_name,
        ca.headline AS creative_headline,
        ca.image_path AS creative_image_path,
        ca.status AS creative_status,
        ca.error AS creative_error,
        ca.created_at AS creative_created_at,
        ca.selected_template,
        ca.selected_variant,
        ca.properties_json AS creative_properties
    FROM research_products rp
    INNER JOIN ai_content ac
        ON ac.research_product_id = rp.research_product_id
    LEFT JOIN creative_assets ca
        ON ca.ai_content_id = ac.ai_content_id
    """

    params: tuple = ()

    if research_product_id is not None:
        query += "\n WHERE rp.research_product_id = ?"
        params = (research_product_id,)

    query += "\n ORDER BY rp.research_product_id ASC"

    with get_connection() as connection:

        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


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


def _decode_properties(raw: str | None) -> dict[str, Any]:
    """
    Decode the ``properties_json`` presentation column.

    Returns an empty dict for NULL or malformed payloads so callers can
    always merge onto a stable baseline.
    """

    if not raw:
        return {}

    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return {}

    return value if isinstance(value, dict) else {}


def _encode_properties(properties: dict[str, Any] | None) -> str | None:
    """
    Encode a presentation properties dict into ``properties_json``.

    Returns None for an empty dict so fresh rows keep the column NULL.
    """

    if not properties:
        return None

    return json.dumps(properties, default=str)


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


def mark_creative_approved(
    creative_id: int,
) -> None:
    """
    Mark a creative as approved.

    The approval workflow reuses the existing ``status`` column
    (GENERATED / APPROVED / FAILED); no schema change is needed.
    """

    query = """
    UPDATE creative_assets
    SET status = 'APPROVED'
    WHERE creative_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (creative_id,),
        )

        connection.commit()


def update_creative_presentation(
    creative_id: int,
    *,
    selected_template: str | None = None,
    selected_variant: str | None = None,
    headline: str | None = None,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Persist a creative's presentation state.

    Template and variant selections plus the lightweight properties
    (CTA, brand, logo position, overlay style) are stored alongside the
    creative so the Studio restores exactly what was reviewed after a
    refresh — never a hardcoded default.

    None-valued arguments keep the existing value, so callers can send
    the full presentation state and only the provided fields change.

    Returns:
        The updated creative row, or None when the creative does not
        exist.
    """

    creative = fetch_creative(creative_id)

    if creative is None:
        return None

    merged_properties = _decode_properties(creative.get("properties_json"))

    if properties:
        merged_properties.update(properties)

    query = """
    UPDATE creative_assets
    SET
        selected_template = ?,
        selected_variant = ?,
        headline = ?,
        properties_json = ?
    WHERE creative_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (
                (
                    selected_template
                    if selected_template is not None
                    else creative.get("selected_template")
                ),
                (
                    selected_variant
                    if selected_variant is not None
                    else creative.get("selected_variant")
                ),
                headline if headline is not None else creative.get("headline"),
                _encode_properties(merged_properties),
                creative_id,
            ),
        )

        connection.commit()

    return fetch_creative(creative_id)


def _latest_creative_for_product(
    research_product_id: int,
) -> tuple[int, str] | None:
    """
    Return ``(creative_id, status)`` of a product's latest creative.

    Shared lookup used by every workflow transition (save, approve,
    reopen) so the join logic stays in one place.
    """

    query = """
    SELECT ca.creative_id, ca.status
    FROM ai_content ac
    INNER JOIN creative_assets ca
        ON ca.ai_content_id = ac.ai_content_id
    WHERE ac.research_product_id = ?
    ORDER BY ca.creative_id DESC
    LIMIT 1
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (research_product_id,),
        ).fetchone()

    if row is None:
        return None

    return int(row[0]), row[1]


def save_creative_presentation(
    research_product_id: int,
    *,
    selected_template: str | None = None,
    selected_variant: str | None = None,
    headline: str | None = None,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Persist presentation edits made in the Creative Studio.

    Rejects changes to approved or queued creatives: once a creative is
    approved it is frozen, so the Studio must lock editing instead of
    reaching the server.

    Returns:
        The updated creative row, or None when the product has no
        creative yet.

    Raises:
        CreativeLockedError:
            If the product's creative is already approved or queued.
    """

    latest = _latest_creative_for_product(research_product_id)

    if latest is None:
        return None

    creative_id, status = latest

    if status in ("APPROVED", "QUEUED"):
        raise CreativeLockedError(
            f"Creative {creative_id} is {status} and cannot be edited."
        )

    return update_creative_presentation(
        creative_id,
        selected_template=selected_template,
        selected_variant=selected_variant,
        headline=headline,
        properties=properties,
    )


def approve_creative_for_product(
    research_product_id: int,
    *,
    selected_template: str | None = None,
    selected_variant: str | None = None,
    headline: str | None = None,
    properties: dict[str, Any] | None = None,
) -> int | None:
    """
    Approve the creative of a research product's AI content.

    Persists the approved presentation state (template, variant,
    headline and properties) before flipping the status to APPROVED, so
    the approved creative restores exactly after a refresh.

    Returns the approved ``creative_id``, or None when the product has
    no creative to approve.
    """

    latest = _latest_creative_for_product(research_product_id)

    if latest is None:
        return None

    creative_id = latest[0]

    update_creative_presentation(
        creative_id,
        selected_template=selected_template,
        selected_variant=selected_variant,
        headline=headline,
        properties=properties,
    )

    mark_creative_approved(creative_id)

    return creative_id


def queue_creative_for_publishing(
    research_product_id: int,
) -> int | None:
    """
    Transition an approved creative into the publishing queue.

    Only flips the workflow ``status`` (APPROVED -> QUEUED); every
    editorial decision (headline, description, CTA, template, variant,
    overlay, logo position, properties) is preserved untouched.

    Returns the queued ``creative_id``, or None when the product has
    no creative to queue.

    Raises:
        CreativeLockedError:
            If the creative is not currently approved.
    """

    latest = _latest_creative_for_product(research_product_id)

    if latest is None:
        return None

    creative_id, status = latest

    if status != "APPROVED":
        raise CreativeLockedError(
            f"Creative {creative_id} is {status} and cannot be queued "
            "for publishing. Only approved creatives can be queued."
        )

    _update_creative_status(creative_id, "QUEUED")

    return creative_id


def unqueue_creative_from_publishing(
    research_product_id: int,
) -> int | None:
    """
    Return a queued creative to the approved state.

    Frees a creative that was previously placed in the publishing
    queue, flipping ``status`` (QUEUED -> APPROVED) so the creative
    becomes editable again in the Creative Studio.

    Returns the ``creative_id``, or None when the product has no
    queued creative to release.
    """

    latest = _latest_creative_for_product(research_product_id)

    if latest is None:
        return None

    creative_id, status = latest

    if status != "QUEUED":
        return creative_id

    _update_creative_status(creative_id, "APPROVED")

    return creative_id


def reopen_creative_for_review(
    research_product_id: int,
) -> int | None:
    """
    Return an approved creative to the editable review state.

    Only flips the workflow ``status`` (APPROVED -> GENERATED); every
    editorial decision (headline, description, CTA, template, variant,
    overlay, logo position, properties) is preserved untouched.

    Reuses the existing status model — no new statuses, no new tables.

    Returns the reopened ``creative_id``, or None when the product has
    no creative.

    Raises:
        CreativeLockedError:
            If the creative has already been queued for publishing (or
            is otherwise not in an approvable state).
    """

    latest = _latest_creative_for_product(research_product_id)

    if latest is None:
        return None

    creative_id, status = latest

    if status == "QUEUED":
        raise CreativeLockedError(
            f"Creative {creative_id} has already been queued for "
            "publishing. Remove it from the publishing queue before "
            "editing."
        )

    if status == "APPROVED":
        _update_creative_status(creative_id, "GENERATED")

    return creative_id


def _update_creative_status(
    creative_id: int,
    status: str,
) -> None:
    """
    Set a creative's workflow status directly.
    """

    query = """
    UPDATE creative_assets
    SET status = ?
    WHERE creative_id = ?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (
                status,
                creative_id,
            ),
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


def fetch_creative_image_path(
    creative_id: int,
) -> str | None:
    """
    Return the stored image path of a creative asset, if any.
    """

    query = """
    SELECT image_path
    FROM creative_assets
    WHERE creative_id = ?
    """

    with get_connection() as connection:

        row = connection.execute(
            query,
            (creative_id,),
        ).fetchone()

    if row is None:
        return None

    return row[0]


# ---------------------------------------------------------------------
# GENERATION
# ---------------------------------------------------------------------


def _latest_creative_for_ai_content(
    ai_content_id: int,
) -> dict[str, Any] | None:
    """
    Return the most recently created creative for AI content, if any.
    """

    creatives = fetch_creatives_by_ai_content(ai_content_id)

    return creatives[-1] if creatives else None


def generate_and_save_creative(
    research_product_id: int,
    engine: RenderingEngine | None = None,
    *,
    selected_template: str | None = None,
    selected_variant: str | None = None,
    headline: str | None = None,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Render and persist a creative for a research product's AI content.

    Single shared entry point for manual creative generation (POST
    /creatives/generate). It reuses the exact building blocks of the
    creative worker — image resolution, content mapping and the
    RenderingEngine — so the API path and the batch worker produce
    identical creatives.

    Idempotent: a creative that already exists (in any non-FAILED
    state) is returned unchanged and never rendered twice. A FAILED
    creative is deleted first so manual retry produces a fresh render.

    Args:
        research_product_id:
            Product whose AI content should be rendered.
        engine:
            Optional pre-built rendering engine. When omitted, an
            engine with the default template registry is created.
        selected_template:
            Template selection persisted with the creative.
        selected_variant:
            Variant selection persisted with the creative.
        headline:
            Headline override persisted with the creative.
        properties:
            Presentation properties (CTA, brand, logo position, overlay
            style) persisted with the creative.

    Returns:
        The persisted creative row dict.

    Raises:
        CreativeContentNotFoundError:
            If the product has no AI content.
        CreativeError:
            If the product image cannot be resolved or rendering fails.
    """

    record = fetch_creative_content_for_product(research_product_id)

    if record is None:
        raise CreativeContentNotFoundError(
            f"Research product {research_product_id} has no AI content "
            "to render a creative from."
        )

    ai_content_id = int(record["ai_content_id"])

    product_label = (
        record.get("product_name")
        or record.get("pinterest_title")
        or str(ai_content_id)
    )

    _dev_log(
        "creative_generate_start",
        research_product_id=research_product_id,
        ai_content_id=ai_content_id,
        product_name=product_label,
    )

    existing = _latest_creative_for_ai_content(ai_content_id)

    if existing is not None and existing["status"] != "FAILED":
        _dev_log(
            "creative_skipped",
            research_product_id=research_product_id,
            ai_content_id=ai_content_id,
            creative_id=existing["creative_id"],
            reason="creative_already_exists",
        )
        return existing

    if existing is not None:
        delete_creative(int(existing["creative_id"]))

    start = time.monotonic()

    image_path = resolve_local_product_image(record)

    content = build_render_content(record)
    output_filename = (
        f"{DEFAULT_TEMPLATE_ID}_ai{ai_content_id:06d}"
    )

    if engine is None:
        engine = RenderingEngine(registry=TemplateRegistry())

    result = engine.render(
        DEFAULT_TEMPLATE_ID,
        content,
        product_image=image_path,
        output_filename=output_filename,
    )

    creative_id = create_creative(
        ai_content_id=ai_content_id,
        template_name=result.template_id,
        headline=headline or (
            record.get("pinterest_title")
            or record.get("product_name")
            or str(ai_content_id)
        ),
        image_path=str(result.path),
    )

    update_creative_presentation(
        creative_id,
        selected_template=selected_template,
        selected_variant=selected_variant,
        properties=properties,
    )

    _dev_log(
        "creative_db_update",
        research_product_id=research_product_id,
        ai_content_id=ai_content_id,
        creative_id=creative_id,
        template=result.template_id,
        variant=result.variant,
        image_path=str(result.path),
        duration_ms=round((time.monotonic() - start) * 1000, 3),
    )

    return fetch_creative(creative_id)
