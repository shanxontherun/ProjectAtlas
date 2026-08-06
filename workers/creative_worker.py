"""
Atlas Creative Worker.

Orchestrates creative asset generation for validated AI content:

    1. Fetch validated AI content that has no creative yet.
    2. Resolve the local product image.
    3. Select the default template and brand.
    4. Render through the RenderingEngine.
    5. Persist the creative via the repository layer.
    6. Continue on per-record failures.

The worker contains only orchestration, logging and error handling.
Rendering, typography, image composition and database access all live
in the Creative Engine and repository layers.
"""

from __future__ import annotations

import logging
from typing import Any

from creative.exceptions import CreativeError
from creative.registry import TemplateRegistry
from creative.rendering import RenderingEngine

from services.creative_service import (
    DEFAULT_TEMPLATE_ID,
    build_render_content,
    create_creative,
    creative_exists,
    fetch_pending_creative_content,
    record_creative_failure,
    resolve_local_product_image,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def run_worker(
    engine: RenderingEngine | None = None,
) -> dict[str, int]:
    """
    Run one creative generation pass.

    Args:
        engine:
            Optional pre-built rendering engine. When omitted, an
            engine with the default template registry is created.

    Returns:
        A summary dict with ``generated``, ``skipped`` and
        ``failed`` counts.
    """

    records = fetch_pending_creative_content()

    summary = {
        "generated": 0,
        "skipped": 0,
        "failed": 0,
    }

    if not records:
        return summary

    if engine is None:
        engine = RenderingEngine(registry=TemplateRegistry())

    for record in records:

        ai_content_id = int(record["ai_content_id"])

        if creative_exists(ai_content_id):
            summary["skipped"] += 1
            logger.info("SKIP: %s (creative already exists)", ai_content_id)
            continue

        product_label = (
            record.get("product_name")
            or record.get("pinterest_title")
            or str(ai_content_id)
        )

        logger.info("Rendering: %s", product_label)

        try:

            image_path = resolve_local_product_image(record)

            content = build_render_content(record)
            output_filename = (
                f"{DEFAULT_TEMPLATE_ID}_ai{ai_content_id:06d}"
            )
            result = engine.render(
                DEFAULT_TEMPLATE_ID,
                content,
                product_image=image_path,
                output_filename=output_filename,
            )

            headline = str(record.get("pinterest_title") or product_label)

            creative_id = create_creative(
                ai_content_id=ai_content_id,
                template_name=result.template_id,
                headline=headline,
                image_path=str(result.path),
            )

            summary["generated"] += 1

            logger.info("SUCCESS: %s", creative_id)

        except CreativeError as exc:

            summary["failed"] += 1

            _persist_failure(record, ai_content_id, str(exc))

            logger.error("%s", exc)

        except Exception as exc:

            summary["failed"] += 1

            _persist_failure(record, ai_content_id, str(exc))

            logger.error("%s", exc)

    return summary


def _persist_failure(
    record: dict[str, Any],
    ai_content_id: int,
    error: str,
) -> None:
    """
    Record a FAILED creative so re-running never retries the record.
    """

    headline = str(
        record.get("pinterest_title")
        or record.get("product_name")
        or ai_content_id
    )

    try:

        record_creative_failure(
            ai_content_id=ai_content_id,
            template_name=DEFAULT_TEMPLATE_ID,
            headline=headline,
            error=error,
        )

    except Exception:

        logger.exception(
            "Unable to record failure for %s",
            ai_content_id,
        )


def main() -> None:

    print("=" * 80)
    print("ATLAS CREATIVE WORKER")
    print("=" * 80)

    summary = run_worker()

    print("=" * 80)
    print("CREATIVE WORKER COMPLETE")
    print("=" * 80)
    print(f"Generated : {summary['generated']}")
    print(f"Skipped   : {summary['skipped']}")
    print(f"Failed    : {summary['failed']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
