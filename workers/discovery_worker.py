"""
Discovery Worker.

Discovers Amazon products and stores them in Atlas.
"""

from __future__ import annotations

import logging

from services.amazon_client import AmazonClient
from services.discovery_service import DiscoveryService
from services.research_products import (
    insert_research_product,
    fetch_product_by_asin,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:

    client = AmazonClient(
        headless=False,
    )

    try:

        client.open()

        discovery = DiscoveryService(client)

        products = discovery.discover(limit=10)

        print()
        print("=" * 80)
        print(f"Discovered {len(products)} products.")
        print("=" * 80)

        inserted = 0
        skipped = 0

        for product in products:

            #
            # Basic validation
            #
            if not product.asin:
                logger.warning(
                    "Skipping '%s' (missing ASIN).",
                    product.title,
                )
                skipped += 1
                continue

            if not product.product_url:
                logger.warning(
                    "Skipping '%s' (missing product URL).",
                    product.title,
                )
                skipped += 1
                continue

            if not product.image_url:
                logger.warning(
                    "Skipping '%s' (missing image URL).",
                    product.title,
                )
                skipped += 1
                continue

            #
            # Skip duplicates
            #
            existing = fetch_product_by_asin(product.asin)

            if existing is not None:
                logger.info(
                    "Already exists: %s",
                    product.asin,
                )
                skipped += 1
                continue

            research_product_id = insert_research_product(
                job_id=1,
                asin=product.asin,
                category=product.category,
                product_name=product.title,
                product_url=product.product_url,
                source="Amazon",
                price=product.price,
                currency=product.currency,
                rating=product.rating,
                review_count=product.review_count,
                image_url=product.image_url,
                ai_summary=None,
            )

            inserted += 1

            logger.info(
                "Inserted Product %s | %s",
                research_product_id,
                product.title,
            )

        print()
        print("=" * 80)
        print("DISCOVERY COMPLETE")
        print("=" * 80)
        print(f"Inserted : {inserted}")
        print(f"Skipped  : {skipped}")
        print("=" * 80)

    finally:
        client.close()


if __name__ == "__main__":
    main()