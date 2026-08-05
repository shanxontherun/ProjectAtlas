"""
Amazon Product Model.

Shared across the Discovery pipeline.
"""

from pydantic import BaseModel, Field


class AmazonProduct(BaseModel):
    """
    Canonical Amazon product model.
    """

    asin: str

    title: str

    product_url: str

    image_url: str | None = None

    brand: str | None = None

    price: float | None = None

    currency: str = Field(default="USD")

    rating: float | None = None

    review_count: int | None = None

    category: str | None = None