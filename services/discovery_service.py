"""
Discovery Service.

Coordinates Amazon Best Sellers and the Amazon Parser.
"""

from __future__ import annotations

import logging

from services.amazon_bestsellers import fetch_bestsellers
from services.amazon_parser import AmazonParser
from services.amazon_client import AmazonClient

logger = logging.getLogger(__name__)


class DiscoveryService:

    def __init__(self, client: AmazonClient):

        self.client = client
        self.parser = AmazonParser(client)

    def discover(
        self,
        limit: int = 20,
    ):

        logger.info("Starting discovery...")

        products = fetch_bestsellers(
            self.client,
            limit=limit,
        )

        parsed_products = []

        for item in products:

            try:

                logger.info(
                    "Parsing %s",
                    item["title"],
                )

                product = self.parser.parse(
                    item["product_url"],
                )

                product.category = "Laundry Bags"

                parsed_products.append(product)

            except Exception:

                logger.exception(
                    "Failed parsing %s",
                    item["product_url"],
                )

        logger.info(
            "Discovery complete (%s products).",
            len(parsed_products),
        )

        return parsed_products