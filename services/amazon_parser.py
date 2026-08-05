"""
Amazon Product Parser.

Parses a single Amazon product page into an AmazonProduct model.
"""

from __future__ import annotations

import json
import logging
import re

from playwright.sync_api import TimeoutError

from models.amazon_product import AmazonProduct
from services.amazon_client import AmazonClient
from services.html_utils import (
    load_json,
    safe_float,
    safe_int,
)

logger = logging.getLogger(__name__)


class AmazonParser:

    def __init__(self, client: AmazonClient):

        self.client = client
        self.page = client.page

    def parse(self, product_url: str) -> AmazonProduct:

        logger.info("Opening %s", product_url)

        self.page.goto(
            product_url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        self.page.wait_for_timeout(2000)

        json_data = self._extract_json()

        asin = (
            self._extract_asin(json_data)
            or self._extract_asin_from_url(product_url)
            or ""
        )

        title = (
            self._extract_title(json_data)
            or self._extract_title_css()
            or ""
        )

        brand = (
            self._extract_brand(json_data)
            or self._extract_brand_css()
        )

        price = (
            self._extract_price(json_data)
            or self._extract_price_css()
        )

        rating = (
            self._extract_rating(json_data)
            or self._extract_rating_css()
        )

        review_count = (
            self._extract_review_count(json_data)
            or self._extract_review_count_css()
        )

        image_url = (
            self._extract_image(json_data)
            or self._extract_image_css()
        )

        return AmazonProduct(
            asin=asin,
            title=title,
            brand=brand,
            price=price,
            currency="USD",
            rating=rating,
            review_count=review_count,
            image_url=image_url,
            product_url=product_url,
        )

    ###########################################################

    def _extract_json(self):

        scripts = self.page.locator(
            'script[type="application/ld+json"]'
        )

        for i in range(scripts.count()):

            try:

                text = scripts.nth(i).inner_text()

                data = load_json(text)

                if data:

                    return data

            except Exception:

                continue

        return None

    ###########################################################

    def _extract_title(self, data):

        if not data:
            return None

        if isinstance(data, dict):

            return data.get("name")

        return None

    ###########################################################

    def _extract_brand(self, data):

        if not data:
            return None

        brand = data.get("brand")

        if isinstance(brand, dict):

            return brand.get("name")

        if isinstance(brand, str):

            return brand

        return None

    ###########################################################

    def _extract_price(self, data):

        if not data:
            return None

        offers = data.get("offers")

        if isinstance(offers, dict):

            return safe_float(
                offers.get("price")
            )

        return None

    ###########################################################

    def _extract_rating(self, data):

        if not data:
            return None

        rating = data.get("aggregateRating")

        if isinstance(rating, dict):

            return safe_float(
                str(rating.get("ratingValue"))
            )

        return None

    ###########################################################

    def _extract_review_count(self, data):

        if not data:
            return None

        rating = data.get("aggregateRating")

        if isinstance(rating, dict):

            return safe_int(
                str(rating.get("reviewCount"))
            )

        return None

    ###########################################################

    def _extract_image(self, data):

        if not data:
            return None

        image = data.get("image")

        if isinstance(image, list):

            return image[0]

        if isinstance(image, str):

            return image

        return None

    ###########################################################

    def _extract_asin(self, data):

        if not data:
            return None

        return data.get("sku")

    ###########################################################

    def _extract_asin_from_url(self, url):

        match = re.search(
            r"/dp/([A-Z0-9]{10})",
            url,
        )

        if match:

            return match.group(1)

        return None

    ###########################################################
    # CSS FALLBACKS
    ###########################################################

    def _extract_title_css(self):

        selectors = [
            "#productTitle",
            "span#productTitle",
            "h1 span",
        ]

        for selector in selectors:

            try:

                locator = self.page.locator(selector).first

                if locator.count() == 0:
                    continue

                text = locator.inner_text().strip()

                if text:
                    return text

            except Exception:
                continue

        return None

    def _extract_brand_css(self):

        try:

            text = self.page.locator(
                "#bylineInfo"
            ).inner_text().strip()

            prefixes = [
             "Brand:",
             "Visit the",
             "Store",
            ]

            for prefix in prefixes:
                text = text.replace(prefix, "")

            return text.strip()

        except Exception:

            return None

    def _extract_price_css(self):

        selectors = [
            ".a-price .a-offscreen",
            "#corePrice_feature_div .a-offscreen",
        ]

        for selector in selectors:

            try:

                text = self.page.locator(
                    selector
                ).first.inner_text()

                value = safe_float(text)

                if value:

                    return value

            except Exception:

                continue

        return None

    def _extract_rating_css(self):

        try:

            text = self.page.locator(
                "span[data-hook='rating-out-of-text']"
            ).inner_text()

            return safe_float(text)

        except Exception:

            return None

    def _extract_review_count_css(self):

        selectors = [
            "#acrCustomerReviewText",
            "span[data-hook='total-review-count']",
            "#acrCustomerReviewLink",
        ]

        for selector in selectors:

            try:

                locator = self.page.locator(selector).first

                if locator.count() == 0:
                    continue

                text = locator.inner_text()

                value = safe_int(text)

                if value:

                    return value

            except Exception:
                continue

        return None

    def _extract_image_css(self):

        try:

            return self.page.locator(
                "#landingImage"
            ).get_attribute("src")

        except Exception:

            return None