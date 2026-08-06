"""
Creative Worker Phase C integration smoke test.

Builds an isolated database (applying every sql/ migration in order),
seeds validated AI content and product fixtures, then runs the worker
to prove:

- successful creative generation
- duplicate skip (idempotency on re-run)
- invalid template handling
- renderer failure handling
- the worker continues after a failure

Run with:  python tests/test_creative_worker.py
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

import services.database as database  # noqa: E402

from services.creative_service import (  # noqa: E402
    fetch_creatives_by_ai_content,
    fetch_generated_creatives,
)

import workers.creative_worker as creative_worker  # noqa: E402

from workers.creative_worker import run_worker  # noqa: E402


TEST_ASIN_VALID = "TESTASIN001"
TEST_ASIN_MISSING = "TESTASIN002"

SOURCE_IMAGE = PROJECT_ROOT / "creative" / "assets" / "test.jpg"

CREATIVE_IMAGE_DIR = (
    PROJECT_ROOT / "storage" / "products" / "amazon"
)


def _build_isolated_database() -> Path:
    """
    Create a fresh database by applying every sql/ migration in order.
    """

    temp_dir = Path(tempfile.mkdtemp(prefix="atlas_creative_test_"))
    db_path = temp_dir / "atlas.db"

    connection = sqlite3.connect(db_path)
    connection.executescript("PRAGMA foreign_keys = ON;")

    for migration in sorted((PROJECT_ROOT / "sql").glob("*.sql")):
        connection.executescript(migration.read_text(encoding="utf-8"))

    connection.commit()
    connection.close()

    return db_path


def _prepare_image(asin: str) -> None:
    """
    Copy the shared test image into the product image store for asin.
    """

    destination_dir = CREATIVE_IMAGE_DIR / asin
    destination_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE_IMAGE, destination_dir / "original.jpg")


def _remove_image(asin: str) -> None:
    """
    Remove the fixture image created by _prepare_image.
    """

    shutil.rmtree(CREATIVE_IMAGE_DIR / asin, ignore_errors=True)


def _insert_product_and_content(
    asin: str,
    product_name: str,
    title: str,
) -> int:
    """
    Insert a GENERATED research product plus VALID ai_content record.

    Returns the ai_content_id.
    """

    with database.get_connection() as connection:

        cursor = connection.execute(
            """
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
                ai_summary,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'GENERATED')
            """,
            (
                1,
                asin,
                "Home Storage",
                product_name,
                "https://example.com/product",
                "Amazon",
                19.99,
                "USD",
                4.5,
                120,
                "https://example.com/image.jpg",
                "Fixture summary",
            ),
        )

        research_product_id = int(cursor.lastrowid)

        cursor = connection.execute(
            """
            INSERT INTO ai_content (
                research_product_id,
                seo_title,
                pinterest_title,
                pinterest_description,
                pinterest_keywords,
                board_name,
                instagram_caption,
                blog_summary,
                ai_score,
                status,
                validation_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'GENERATED', 'VALID')
            """,
            (
                research_product_id,
                title,
                title,
                "Fixture description",
                "keyword",
                "home-storage",
                "Instagram caption",
                "Blog summary",
                90,
            ),
        )

        ai_content_id = int(cursor.lastrowid)

        connection.commit()

    return int(ai_content_id)


def _statuses() -> list[str]:
    """
    Return the status of every creative_assets row.
    """

    with database.get_connection() as connection:

        rows = connection.execute(
            "SELECT status FROM creative_assets ORDER BY creative_id"
        ).fetchall()

    return [str(row[0]) for row in rows]


def _latest_creative() -> dict:
    """
    Return the most recently created creative as a dict.
    """

    with database.get_connection() as connection:

        row = connection.execute(
            """
            SELECT *
            FROM creative_assets
            ORDER BY creative_id DESC
            LIMIT 1
            """
        ).fetchone()

    return dict(row)


def _creative_for_ai_content(ai_content_id: int) -> dict:
    """
    Return the first creative for an AI content record as a dict.
    """

    creatives = fetch_creatives_by_ai_content(ai_content_id)

    if not creatives:
        return {}

    return creatives[0]


def main() -> None:
    failures: list[str] = []

    def check(
        name: str,
        condition: bool,
        detail: str = "",
    ) -> None:
        status = "ok" if condition else "FAIL"
        print(f"[{status}] {name}")
        if not condition:
            failures.append(f"{name}: {detail}")

    original_database_path = database.DATABASE_PATH

    db_path = _build_isolated_database()

    try:

        database.DATABASE_PATH = db_path

        # ---- 1. successful creative generation -----------------------

        _prepare_image(TEST_ASIN_VALID)

        ai_content_id = _insert_product_and_content(
            TEST_ASIN_VALID,
            "Portable Laundry Bag",
            "Portable Laundry Bag Essentials for Travel",
        )

        summary = run_worker()

        generated = fetch_generated_creatives()
        creative = _latest_creative()

        check(
            "successful generation count",
            summary == {"generated": 1, "skipped": 0, "failed": 0},
            str(summary),
        )
        check(
            "generated creative persisted",
            len(generated) == 1,
            f"{len(generated)} rows",
        )
        check(
            "creative links to ai content",
            creative["ai_content_id"] == ai_content_id,
            str(creative["ai_content_id"]),
        )
        check(
            "creative stores rendered template",
            creative["template_name"] == "home_01",
            str(creative["template_name"]),
        )
        check(
            "creative stores rendered image path",
            Path(creative["image_path"]).is_file(),
            str(creative["image_path"]),
        )
        check(
            "creative status is GENERATED",
            creative["status"] == "GENERATED",
            str(creative["status"]),
        )

        # ---- 2. duplicate skip (idempotency) --------------------------

        summary = run_worker()

        check(
            "re-run generates nothing new",
            summary == {"generated": 0, "skipped": 0, "failed": 0},
            str(summary),
        )
        check(
            "re-run did not create duplicates",
            len(fetch_generated_creatives()) == 1,
            f"{len(fetch_generated_creatives())} rows",
        )

        # ---- 3. invalid template handling ----------------------------

        invalid_template_id = _insert_product_and_content(
            TEST_ASIN_VALID,
            "Invalid Template Product",
            "Invalid template fixture",
        )

        original_template_id = creative_worker.DEFAULT_TEMPLATE_ID
        creative_worker.DEFAULT_TEMPLATE_ID = "does_not_exist"

        try:

            summary = run_worker()

        finally:

            creative_worker.DEFAULT_TEMPLATE_ID = original_template_id

        failed_creative = _creative_for_ai_content(invalid_template_id)

        check(
            "invalid template fails the creative",
            summary == {"generated": 0, "skipped": 0, "failed": 1},
            str(summary),
        )
        check(
            "invalid template marked FAILED",
            failed_creative.get("status") == "FAILED",
            str(failed_creative.get("status")),
        )
        check(
            "invalid template failure recorded",
            "not found" in str(failed_creative.get("error", "")).lower(),
            str(failed_creative.get("error")),
        )

        # ---- 4. renderer failure handling ----------------------------

        missing_image_id = _insert_product_and_content(
            TEST_ASIN_MISSING,
            "Missing Image Product",
            "Missing image fixture",
        )

        summary = run_worker()

        failed_creative = _creative_for_ai_content(missing_image_id)

        check(
            "renderer failure fails the creative",
            summary == {"generated": 0, "skipped": 0, "failed": 1},
            str(summary),
        )
        check(
            "renderer failure marked FAILED",
            failed_creative.get("status") == "FAILED",
            str(failed_creative.get("status")),
        )
        check(
            "renderer failure message recorded",
            "image" in str(failed_creative.get("error", "")).lower(),
            str(failed_creative.get("error")),
        )

        # ---- 5. worker continues after failure ------------------------

        failing_id = _insert_product_and_content(
            TEST_ASIN_MISSING,
            "Failing Product",
            "Failing fixture",
        )
        valid_id = _insert_product_and_content(
            TEST_ASIN_VALID,
            "Continuing Product",
            "Continuing fixture",
        )

        summary = run_worker()

        check(
            "worker continues after failure",
            summary == {"generated": 1, "skipped": 0, "failed": 1},
            str(summary),
        )

        valid_creative = _creative_for_ai_content(valid_id)
        failing_creative = _creative_for_ai_content(failing_id)

        check(
            "valid record generated after failure",
            valid_creative.get("status") == "GENERATED",
            str(valid_creative.get("status")),
        )
        check(
            "failing record marked FAILED",
            failing_creative.get("status") == "FAILED",
            str(failing_creative.get("status")),
        )
        check(
            "all failures recorded",
            _statuses().count("FAILED") == 3,
            str(_statuses()),
        )

    finally:

        database.DATABASE_PATH = original_database_path

        _remove_image(TEST_ASIN_VALID)
        _remove_image(TEST_ASIN_MISSING)

        shutil.rmtree(db_path.parent, ignore_errors=True)

    print()

    if failures:
        print("FAILURES:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
