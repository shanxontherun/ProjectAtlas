"""
Amazon Search Service.

Searches Amazon and returns product information.
"""

from __future__ import annotations

from urllib.parse import quote_plus
from typing import Any

from services.amazon_client import AmazonClient


AMAZON_BASE_URL = "https://www.amazon.com"


def search_products(
    client: AmazonClient,
    search_term: str,
    max_products: int = 20,
) -> list[dict[str, Any]]:
    """
    Search Amazon and return product information.

    Returns:
        [
            {
                "title": "...",
                "product_url": "...",
                "thumbnail_url": "...",
                "position": 1,
                "search_term": "kitchen storage",
            }
        ]
    """

    search_url = (
        f"{AMAZON_BASE_URL}/s?k={quote_plus(search_term)}"
    )

    print(f"Searching Amazon: {search_term}")

    client.page.goto(
        search_url,
        wait_until="domcontentloaded",
        timeout=60000,
    )

    client.page.wait_for_timeout(3000)

    product_cards = client.page.locator(
        "div[data-component-type='s-search-result']"
    )

    products: list[dict[str, Any]] = []

    total_cards = product_cards.count()

    print(f"Found {total_cards} search result(s).")

    for index in range(total_cards):

        if len(products) >= max_products:
            break

        card = product_cards.nth(index)

        try:

            title_locator = card.locator("h2 span").first

            link_locator = card.locator("h2 a").first

            image_locator = card.locator("img").first

            title = title_locator.inner_text().strip()

            product_url = link_locator.get_attribute("href")

            thumbnail_url = image_locator.get_attribute("src")

            if not product_url:
                continue

            if product_url.startswith("/"):

                product_url = (
                    AMAZON_BASE_URL
                    + product_url
                )

            products.append(
                {
                    "title": title,
                    "product_url": product_url,
                    "thumbnail_url": thumbnail_url,
                    "position": len(products) + 1,
                    "search_term": search_term,
                }
            )

        except Exception:
            continue

    print(
        f"Collected {len(products)} product(s)."
    )

    return products