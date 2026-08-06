"""
Atlas AI Worker

Generates Pinterest AI content for pending research products.
"""

from __future__ import annotations

from services.ai_service import (
    AlreadyGeneratedError,
    generate_and_save_ai_content,
)
from services.research_products import fetch_pending_research_products


def main() -> None:
    """
    Entry point for the AI Worker.
    """

    print("=" * 60)
    print("ATLAS AI WORKER")
    print("=" * 60)

    products = fetch_pending_research_products()

    print(f"Found {len(products)} pending research product(s).\n")

    generated = 0
    skipped = 0
    failed = 0

    for index, product in enumerate(products, start=1):

        product_id = product["research_product_id"]

        print(f"[{index}/{len(products)}] {product['product_name']}")

        try:

            generate_and_save_ai_content(product)

            print("   ✓ AI content generated.\n")

            generated += 1

        except AlreadyGeneratedError:

            print("   ✓ Already generated. Skipping.\n")

            skipped += 1

        except Exception as exc:

            print(f"   ✗ ERROR: {exc}\n")

            failed += 1

    print("=" * 60)
    print("AI WORKER COMPLETE")
    print("=" * 60)
    print(f"Generated : {generated}")
    print(f"Skipped   : {skipped}")
    print(f"Failed    : {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()