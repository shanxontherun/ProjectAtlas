"""
Atlas Image Downloader.

Downloads the highest-resolution Amazon product image
and stores it locally.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import Page


ROOT = Path("storage/products/amazon")


def _extract_image_url(landing) -> str | None:
    """
    Extract the highest-resolution image URL from Amazon.
    """

    image_url = landing.get_attribute("data-old-hires")

    if image_url:
        return image_url

    dynamic = landing.get_attribute("data-a-dynamic-image")

    if dynamic:

        try:
            images = json.loads(dynamic)

            if images:
                return next(iter(images.keys()))

        except Exception:
            pass

    return landing.get_attribute("src")


def download_product_image(
    page: Page,
    product: dict,
) -> Path:
    """
    Download the main Amazon product image.

    Returns
    -------
    Path
        Local image path.
    """

    asin = product["asin"]

    product_dir = ROOT / asin

    product_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    image_path = product_dir / "original.jpg"

    #
    # Idempotent
    #
    if image_path.exists():
        return image_path

    #
    # Open product page
    #
    page.goto(
        product["product_url"],
        wait_until="domcontentloaded",
        timeout=60000,
    )

    #
    # Amazon never reaches true network idle.
    #
    page.wait_for_timeout(2000)

    #
    # Try multiple selectors.
    #
    selectors = [
        "#landingImage",
        "#imgTagWrapperId img",
        "#main-image-container img",
    ]

    landing = None

    for selector in selectors:

        try:

            page.wait_for_selector(
                selector,
                timeout=5000,
            )

            landing = page.locator(selector).first

            break

        except Exception:

            continue

    if landing is None:
        raise RuntimeError(
            "Could not locate the main product image."
        )

    image_url = _extract_image_url(landing)

    if not image_url:
        raise RuntimeError(
            "Unable to determine image URL."
        )

    #
    # Download image
    #
    image_bytes = urlopen(
        image_url,
        timeout=30,
    ).read()

    image_path.write_bytes(
        image_bytes,
    )

    #
    # Save metadata
    #
    metadata = {
        "asin": product["asin"],
        "title": product["product_name"],
        "product_url": product["product_url"],
        "image_url": image_url,
        "price": product["price"],
        "rating": product["rating"],
        "review_count": product["review_count"],
        "downloaded_at": datetime.utcnow().isoformat(),
    }

    with open(
        product_dir / "metadata.json",
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4,
            ensure_ascii=False,
        )

    return image_path