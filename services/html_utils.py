"""
HTML helper utilities.

Reusable parsing helpers.
"""

from __future__ import annotations

import json
import re


def safe_float(value: str | None) -> float | None:

    if not value:
        return None

    value = value.replace(",", "")

    match = re.search(r"\d+(\.\d+)?", value)

    if not match:
        return None

    return float(match.group())


def safe_int(value: str | None) -> int | None:

    if not value:
        return None

    value = value.replace(",", "")

    digits = re.findall(r"\d+", value)

    if not digits:
        return None

    return int("".join(digits))


def load_json(text: str):

    try:
        return json.loads(text)
    except Exception:
        return None