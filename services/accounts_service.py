"""
Accounts data access layer (ATLAS-029B).

Accounts is Atlas's central source of truth for external integrations.
This service exposes only SAFE metadata: provider, display name, username,
marketplace, connection status, connected_at and the is_seed flag.

Credentials are NEVER read here. Pinterest account identity is reused from
the existing ``pinterest_accounts`` table via ``account_connections``; the
API must never SELECT the ``connection_credentials`` table.

The ``is_seed`` flag and ``connection_status`` are separate concepts:
a non-seed account is NOT automatically connected.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Any

from services.constants import (
    AI_PROVIDER_CUSTOM,
    AI_PROVIDER_GEMINI,
    AI_PROVIDER_OPENAI,
    AI_PROVIDER_OPENROUTER,
    CONNECTION_CONFIGURED,
    CONNECTION_NOT_CONFIGURED,
    PROVIDER_AI,
    PROVIDER_AMAZON_ASSOCIATES,
    PROVIDER_PINTEREST,
)
from services.database import get_connection

# Env names already used by the existing AI configuration
# (services/ai_service.py). Only existence is checked here; values are
# never read, logged, or returned.
_AI_BASE_URL_ENV = "AI_BASE_URL"
_AI_API_KEY_ENV = "AI_API_KEY"
_AI_MODEL_ENV = "AI_MODEL"


# --------------------------------------------------
# Pinterest
# --------------------------------------------------


def _safe_connection_row(row: sqlite3.Row) -> dict[str, Any]:
    """
    Project a connection row to safe frontend metadata only.

    Never includes credential columns (they live in a separate table that
    is never queried here).
    """

    return {
        "connection_id": int(row["connection_id"]),
        "provider": str(row["provider"]),
        "display_name": str(row["display_name"]),
        "username": row["username"],
        "marketplace": row["marketplace"],
        "connection_status": str(row["connection_status"]),
        "connected_at": row["connected_at"],
        "is_seed": int(row["is_seed"]) == 1,
    }


def _fetch_connection_rows(provider: str) -> list[sqlite3.Row]:
    """
    Return the safe metadata columns for a provider's connections.

    ``is_seed`` is selected so callers can distinguish development/test
    accounts from real ones without conflating it with connection status.
    """

    query = """
    SELECT
        connection_id,
        provider,
        display_name,
        username,
        marketplace,
        connection_status,
        connected_at,
        is_seed
    FROM account_connections
    WHERE provider = ?
    ORDER BY is_seed ASC, display_name ASC
    """

    with get_connection() as connection:
        rows = connection.execute(query, (provider,)).fetchall()

    return rows


def fetch_pinterest_accounts() -> list[dict[str, Any]]:
    """
    Return safe metadata for every Pinterest connection.

    Pinterest identity is reused from the existing ``pinterest_accounts``
    table through ``account_connections``; no parallel Pinterest table is
    created. Existing seed accounts surface as NOT_CONNECTED, never as a
    real connection.
    """

    return [
        _safe_connection_row(row)
        for row in _fetch_connection_rows(PROVIDER_PINTEREST)
    ]


def fetch_amazon_accounts() -> list[dict[str, Any]]:
    """
    Return safe metadata for every Amazon Associates connection.

    Empty in the Accounts Foundation (no Amazon configuration exists yet);
    a row appears here only when a genuine Amazon Associates account is
    configured in a later sprint.
    """

    return [
        _safe_connection_row(row)
        for row in _fetch_connection_rows(PROVIDER_AMAZON_ASSOCIATES)
    ]


# --------------------------------------------------
# AI Providers (env-derived, no second credential system)
# --------------------------------------------------


def _ai_configured() -> bool:
    """
    Whether the existing AI environment configuration is present.

    Mirrors the existing env contract used by ``services/ai_service.py``
    (AI_BASE_URL / AI_API_KEY / AI_MODEL). Only existence is checked; no
    value is read, logged, or returned. Presence means the provider is
    configured, not that a live connection was verified.
    """

    return bool(
        os.environ.get(_AI_BASE_URL_ENV)
        and os.environ.get(_AI_API_KEY_ENV)
        and os.environ.get(_AI_MODEL_ENV)
    )


def _ai_provider_from_base_url() -> str | None:
    """
    Guess the AI provider label from the configured base URL host.

    Only the base URL is inspected (an endpoint, not a secret). Unknown
    endpoints map to a generic label.
    """

    base_url = os.environ.get(_AI_BASE_URL_ENV) or ""

    normalized = base_url.strip().lower()

    if "openrouter" in normalized:
        return AI_PROVIDER_OPENROUTER

    if "generativelanguage" in normalized:
        return AI_PROVIDER_GEMINI

    if "openai" in normalized:
        return AI_PROVIDER_OPENAI

    return AI_PROVIDER_CUSTOM


def fetch_ai_providers() -> list[dict[str, Any]]:
    """
    Return safe AI provider status derived from the existing env config.

    Providers are synthesized (not DB-backed) because AI configuration is
    environment-based; this reuses the existing configuration instead of
    creating a second credential system. Keys and base URLs are never
    returned.
    """

    configured = _ai_configured()
    configured_label = _ai_provider_from_base_url() if configured else None

    providers = [
        AI_PROVIDER_OPENROUTER,
        AI_PROVIDER_GEMINI,
        AI_PROVIDER_OPENAI,
    ]

    accounts: list[dict[str, Any]] = []

    for label in providers:
        status = (
            CONNECTION_CONFIGURED
            if configured and label == configured_label
            else CONNECTION_NOT_CONFIGURED
        )

        accounts.append(
            {
                "connection_id": None,
                "provider": PROVIDER_AI,
                "display_name": label,
                "username": None,
                "marketplace": None,
                "connection_status": status,
                "connected_at": None,
                "is_seed": False,
            }
        )

    return accounts


# --------------------------------------------------
# Read model
# --------------------------------------------------


def fetch_accounts() -> list[dict[str, Any]]:
    """
    Return the Accounts page read model grouped by provider.

    Each provider group exposes safe metadata only; the frontend never
    receives credentials.
    """

    groups: list[dict[str, Any]] = [
        {
            "provider": PROVIDER_PINTEREST,
            "label": "Pinterest",
            "accounts": fetch_pinterest_accounts(),
        },
        {
            "provider": PROVIDER_AMAZON_ASSOCIATES,
            "label": "Amazon Associates",
            "accounts": fetch_amazon_accounts(),
        },
        {
            "provider": PROVIDER_AI,
            "label": "AI Providers",
            "accounts": fetch_ai_providers(),
        },
    ]

    return groups
