"""
Atlas AI Prompt Library.

Contains reusable prompt templates for all AI workers.
"""

from __future__ import annotations

import json


SYSTEM_PROMPT = """
You are Atlas AI.

You are an expert in:

- Pinterest SEO
- Affiliate marketing
- Amazon product marketing
- Consumer psychology
- Copywriting

Your job is to generate high-quality marketing content.

Rules:

1. Respond ONLY with valid JSON.
2. Do NOT use markdown.
3. Do NOT explain your answer.
4. Do NOT wrap JSON inside code fences.
5. Every field must be present.
6. Keep descriptions concise.
"""


def build_product_prompt(
    product: dict,
) -> str:
    """
    Build a prompt for an Amazon product.
    """

    payload = {
        "asin": product["asin"],
        "title": product["product_name"],
        "category": product["category"],
        "price": product["price"],
        "currency": product["currency"],
        "rating": product["rating"],
        "review_count": product["review_count"],
    }

    return f"""
Generate Pinterest marketing content for this Amazon product.

Product:

{json.dumps(payload, indent=4)}

Return ONLY this JSON schema:

{{
    "title": "",
    "description": "",
    "keywords": [],
    "cta": "",
    "target_audience": "",
    "benefits": []
}}
"""