"""
AI Service

Handles communication with the configured AI Gateway (OmniRoute).
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from services.ai_client import AIClient
from services.ai_prompts import REQUIRED_CONTENT_FIELDS, SYSTEM_PROMPT
from services.database import (
    ai_content_exists,
    create_ai_content,
    get_connection,
    mark_research_generated,
    update_ai_content,
)

load_dotenv()

BASE_URL = os.getenv("AI_BASE_URL")
API_KEY = os.getenv("AI_API_KEY")
MODEL = os.getenv("AI_MODEL")
REQUEST_TIMEOUT = 120

# Structured development logging around AI generation. Disabled in
# production by setting ATLAS_DEV_LOG=0.
DEV_LOG_ENABLED = os.getenv("ATLAS_DEV_LOG", "1") == "1"

logger = logging.getLogger(__name__)


def _dev_log(event: str, **fields: Any) -> None:
    """
    Emit a structured development log line for AI generation.

    Development only: no-op when ATLAS_DEV_LOG != "1".
    """

    if not DEV_LOG_ENABLED:
        return

    record: dict[str, Any] = {
        "event": event,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    record.update(fields)

    logger.info("AI %s %s", event, json.dumps(record, default=str))

def get_headers() -> dict[str, str]:
    """
    Return the standard headers for AI Gateway requests.
    """
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def test_connection() -> str:
    """
    Sends a simple request to the configured AI gateway.
    """

    if not BASE_URL:
        raise RuntimeError("AI_BASE_URL not configured.")

    if not API_KEY:
        raise RuntimeError("AI_API_KEY not configured.")

    if not MODEL:
        raise RuntimeError("AI_MODEL not configured.")

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=get_headers(),
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": "Reply with exactly: Atlas connected successfully.",
                }
            ],
            "temperature": 0,
            "stream": False,
        },
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]



def load_prompt() -> str:
    """
    Load the Pinterest prompt template.
    """

    prompt_path = Path(__file__).parent.parent / "prompts" / "pinterest_prompt.txt"

    return prompt_path.read_text(encoding="utf-8")

def build_prompt(product: dict) -> str:
    """
    Replace placeholders in the prompt template.
    """

    prompt = load_prompt()

    prompt = prompt.replace(
        "{{product_name}}",
        str(product.get("product_name", "")),
    )

    prompt = prompt.replace(
        "{{category}}",
        str(product.get("category", "")),
    )

    prompt = prompt.replace(
        "{{price}}",
        str(product.get("price", "")),
    )

    prompt = prompt.replace(
        "{{rating}}",
        str(product.get("rating", "")),
    )

    prompt = prompt.replace(
        "{{summary}}",
        str(product.get("ai_summary", "")),
    )

    return prompt
def parse_json_response(content: str) -> dict:
    """
    Parse JSON returned by an AI model, removing Markdown code fences if present.
    """

    content = content.strip()

    if content.startswith("```json"):
        content = content[7:]

    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()

    return json.loads(content)


# --------------------------------------------------
# AI Content Generation
# --------------------------------------------------


class AIValidationError(Exception):
    """
    Raised when AI-generated content fails validation.

    Indicates the AI response is malformed or missing required
    fields, as opposed to a transport or request failure from
    the AI client.
    """


class AlreadyGeneratedError(Exception):
    """
    Raised when AI content already exists for a research product.

    Used for idempotency so neither the AI worker nor the HTTP API
    ever generates a duplicate row for the same product.
    """


def validate_content_fields(
    content: dict[str, Any],
) -> None:
    """
    Validate that all required content fields are present.

    None, "" and whitespace-only values are treated as missing.

    Raises:
        AIValidationError:
            If any required field is missing or empty.
    """

    missing: list[str] = []

    for field in REQUIRED_CONTENT_FIELDS:

        value = content.get(field)

        if value is None:
            missing.append(field)

        elif isinstance(value, str) and not value.strip():
            missing.append(field)

    if missing:
        raise AIValidationError(
            "AI response missing required fields: "
            f"{', '.join(missing)}"
        )


def generate_ai_content(
    product: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate Pinterest AI content for a research product.

    Builds the prompt with the Pinterest template, calls the AI
    client, parses the JSON response and validates required fields.

    Pure business function: it never reads or writes the database.

    Returns:
        Content dict matching the ai_content table columns.

    Raises:
        AIValidationError:
            If the AI response is not a JSON object or is missing
            required fields.
    """

    prompt = build_prompt(product)

    start = time.monotonic()

    _dev_log(
        "ai_generate_request",
        research_product_id=product.get("research_product_id"),
        product_name=product.get("product_name"),
        prompt=prompt,
    )

    client = AIClient()

    response = client.generate(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
    )

    _dev_log(
        "ai_generate_response",
        research_product_id=product.get("research_product_id"),
        duration_ms=round((time.monotonic() - start) * 1000, 3),
        response=response,
    )

    content = parse_json_response(response)

    if not isinstance(content, dict):
        raise AIValidationError(
            "AI response is not a JSON object."
        )

    validate_content_fields(content)

    return content


def generate_and_save_ai_content(
    product: dict[str, Any],
) -> int:
    """
    Generate AI content for a research product and persist it.

    Single shared entry point for generation + persistence, reused by
    both the AI worker and the HTTP API so the workflow lives in
    exactly one place.

    Skips nothing: callers are expected to pre-check idempotency via
    the exception below.

    Args:
        product:
            Research product dict (must contain ``research_product_id``
            plus the fields the Pinterest prompt template needs).

    Returns:
        The persisted ``ai_content_id``.

    Raises:
        AlreadyGeneratedError:
            If AI content already exists for the research product.
        AIValidationError:
            If the AI response is malformed or missing required fields.
    """

    product_id = int(product["research_product_id"])

    _dev_log(
        "ai_generate_start",
        research_product_id=product_id,
        product_name=product.get("product_name"),
        mode="create",
    )

    if ai_content_exists(product_id):
        raise AlreadyGeneratedError(
            f"AI content already exists for product {product_id}"
        )

    content = generate_ai_content(product)

    ai_content_id = create_ai_content(
        product_id,
        content,
    )

    mark_research_generated(product_id)

    _dev_log(
        "ai_db_update",
        research_product_id=product_id,
        ai_content_id=ai_content_id,
        mode="create",
    )

    return ai_content_id


def regenerate_and_save_ai_content(
    product: dict[str, Any],
) -> int:
    """
    Regenerate AI content for a research product, replacing existing content.

    Manual user action path: generates fresh content and UPDATEs the
    existing ai_content row in place. Never appends text and never
    creates a second row for the same product.

    Workers never use this path — they stay idempotent via
    ``generate_and_save_ai_content``, which raises
    ``AlreadyGeneratedError`` when content already exists.

    Args:
        product:
            Research product dict (must contain ``research_product_id``).

    Returns:
        The updated ``ai_content_id``.

    Raises:
        AIValidationError:
            If the AI response is malformed or missing required fields.
        sqlite3.Error:
            If no existing ai_content row exists to update.
    """

    product_id = int(product["research_product_id"])

    _dev_log(
        "ai_generate_start",
        research_product_id=product_id,
        product_name=product.get("product_name"),
        mode="update",
    )

    start = time.monotonic()

    content = generate_ai_content(product)

    ai_content_id = update_ai_content(
        product_id,
        content,
    )

    mark_research_generated(product_id)

    _dev_log(
        "ai_db_update",
        research_product_id=product_id,
        ai_content_id=ai_content_id,
        mode="update",
        duration_ms=round((time.monotonic() - start) * 1000, 3),
    )

    return ai_content_id


def fetch_generated_ai_content() -> list[dict[str, Any]]:
    """
    Return all AI content that is ready to be routed.
    """

    query = """
    SELECT
        ac.ai_content_id,
        rp.category AS category_slug,
        rp.product_url,
        rp.image_url
    FROM ai_content ac
    INNER JOIN research_products rp
        ON ac.research_product_id = rp.research_product_id
    WHERE rp.status = 'GENERATED'
    ORDER BY ac.ai_content_id
    """

    with get_connection() as connection:
        rows = connection.execute(query).fetchall()

    products = []

    for row in rows:
        product = dict(row)

        product["category_slug"] = (
            product["category_slug"]
            .strip()
            .lower()
            .replace(" ", "_")
        )

        products.append(product)

    return products

def fetch_pending_validation() -> list[dict[str, Any]]:
    """
    Return AI content waiting for validation.
    """

    query = """
    SELECT *
    FROM ai_content
    WHERE
        status = 'GENERATED'
        AND validation_status = 'PENDING'
    ORDER BY ai_content_id
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]

def mark_validation_valid(
    ai_content_id: int,
) -> None:
    """
    Mark AI content as VALID.
    """

    query = """
    UPDATE ai_content
    SET
        validation_status='VALID',
        validation_error=NULL
    WHERE ai_content_id=?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (ai_content_id,),
        )

        connection.commit()

def mark_validation_invalid(
    ai_content_id: int,
    error: str,
) -> None:
    """
    Mark AI content as INVALID.
    """

    query = """
    UPDATE ai_content
    SET
        validation_status='INVALID',
        validation_error=?
    WHERE ai_content_id=?
    """

    with get_connection() as connection:

        connection.execute(
            query,
            (
                error,
                ai_content_id,
            ),
        )

        connection.commit()

def fetch_validated_ai_content() -> list[dict[str, Any]]:
    """
    Return AI content that passed validation.
    """

    query = """
    SELECT
        ac.ai_content_id,
        LOWER(REPLACE(rp.category, ' ', '_')) AS category_slug,
        rp.product_url,
        rp.image_url
    FROM ai_content ac
    INNER JOIN research_products rp
        ON ac.research_product_id = rp.research_product_id
    WHERE
        ac.status='GENERATED'
        AND ac.validation_status='VALID'
    ORDER BY ac.ai_content_id
    """

    with get_connection() as connection:

        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]

