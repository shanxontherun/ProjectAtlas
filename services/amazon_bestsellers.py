"""
Amazon Best Sellers Service.

Collects product URLs from Amazon Best Sellers.
"""

from __future__ import annotations

from typing import Any

from services.amazon_client import AmazonClient


BESTSELLERS_URL = (
    "https://www.amazon.com/Best-Sellers-Home-Kitchen-Storage-Organization-Products/zgbs/home-garden/3744371"
)


def fetch_bestsellers(
    client: AmazonClient,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Return bestseller product URLs.
    """

    print("Opening Amazon Best Sellers...")

    client.page.goto(
        BESTSELLERS_URL,
        wait_until="domcontentloaded",
        timeout=60000,
    )

    client.page.wait_for_timeout(3000)

    products: list[dict[str, Any]] = []

    #
    # Best Seller product cards
    #
    cards = client.page.locator("div.p13n-sc-uncoverable-faceout")

    total = cards.count()

    print(f"Found {total} bestseller cards.")

    for index in range(total):

        if len(products) >= limit:
            break

        try:

            card = cards.nth(index)

            link = (
                card
                .locator("a")
                .first
                .get_attribute("href")
            )

            if not link:
                continue

            if link.startswith("/"):

                link = (
                    "https://www.amazon.com"
                    + link
                )

            title = (
                card
                .locator("img")
                .first
                .get_attribute("alt")
            )

            thumbnail = (
                card
                .locator("img")
                .first
                .get_attribute("src")
            )

            products.append(
                {
                    "title": title,
                    "product_url": link,
                    "thumbnail_url": thumbnail,
                    "rank": len(products) + 1,
                }
            )

        except Exception:
            continue

    print(
        f"Collected {len(products)} products."
    )

    return products