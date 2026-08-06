"""
Internal I/O and error-formatting helpers for the Creative Engine.

Shared between the template registry and the brand profile loader so
both report consistent, clear errors without duplicating logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from creative.exceptions import CreativeError


def read_json(
    path: Path,
    error_type: type[CreativeError],
) -> dict[str, Any]:
    """
    Read and parse a JSON file.

    Args:
        path:
            Absolute or relative path to the JSON file.
        error_type:
            CreativeError subclass to raise on failure.

    Raises:
        error_type:
            If the file is unreadable or contains invalid JSON.
    """

    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        raise error_type(f"Cannot read '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise error_type(f"Invalid JSON in '{path}': {exc}") from exc


def format_validation_errors(
    exc: PydanticValidationError,
) -> list[str]:
    """
    Format pydantic validation errors into readable field strings.

    Each entry looks like ``zones.0.bounds.width: Input should be ...``
    so callers can surface precise, actionable failures.
    """

    lines: list[str] = []

    for error in exc.errors():

        location = ".".join(
            str(part) for part in error.get("loc", ())
        )

        message = error.get("msg", "invalid value")

        if location:
            lines.append(f"{location}: {message}")
        else:
            lines.append(message)

    return lines
