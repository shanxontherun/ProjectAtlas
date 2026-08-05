"""
Atlas Image Worker.

Downloads Amazon product images and stores them locally.
"""

from __future__ import annotations

import logging

from services.amazon_client import AmazonClient
from services.image_downloader import download_product_image
from services.research_products import (
    fetch_products_pending_images,
    mark_image_downloaded,
    mark_image_failed,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:

    print("=" * 80)
    print("ATLAS IMAGE WORKER")
    print("=" * 80)

    products = fetch_products_pending_images()

    if not products:
        print("No pending images.")
        return

    print(f"Found {len(products)} pending image(s).\n")

    client = AmazonClient(
        headless=False,
    )

    try:

        client.open()

        page = client.page

        downloaded = 0
        failed = 0

        for product in products:

            logger.info(
                "Downloading: %s",
                product["product_name"],
            )

            try:

                local_path = download_product_image(
                    page,
                    product,
                )

                mark_image_downloaded(
                    research_product_id=product["research_product_id"],
                    local_image_path=str(local_path),
                )

                downloaded += 1

                logger.info(
                    "SUCCESS: %s",
                    product["asin"],
                )

            except Exception as exc:

                mark_image_failed(
                    product["research_product_id"],
                )

                failed += 1

                logger.exception(
                    "FAILED: %s",
                    exc,
                )

        print()
        print("=" * 80)
        print("IMAGE WORKER COMPLETE")
        print("=" * 80)
        print(f"Downloaded : {downloaded}")
        print(f"Failed     : {failed}")
        print("=" * 80)

    finally:

        client.close()


if __name__ == "__main__":
    main()