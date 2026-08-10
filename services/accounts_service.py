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
from datetime import datetime, timedelta, timezone
from typing import Any

from services.constants import (
    AI_PROVIDER_CUSTOM,
    AI_PROVIDER_GEMINI,
    AI_PROVIDER_OPENAI,
    AI_PROVIDER_OPENROUTER,
    CONNECTION_CONFIGURED,
    CONNECTION_CONNECTED,
    CONNECTION_DISCONNECTED,
    CONNECTION_NOT_CONFIGURED,
    CREDENTIAL_PINTEREST_ACCESS_TOKEN,
    CREDENTIAL_PINTEREST_REFRESH_TOKEN,
    CREDENTIAL_PINTEREST_SCOPE,
    CREDENTIAL_PINTEREST_TOKEN_EXPIRES_AT,
    PROVIDER_AI,
    PROVIDER_AMAZON_ASSOCIATES,
    PROVIDER_PINTEREST,
)
from services.database import get_connection
from services.pinterest_oauth import refresh_access_token

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
    is never queried here). A Pinterest profile URL is derived from the
    username (never a secret) when one exists.
    """

    username = row["username"]

    profile_url = None
    if (
        str(row["provider"]) == PROVIDER_PINTEREST
        and username
    ):
        profile_url = f"https://www.pinterest.com/{username}/"

    return {
        "connection_id": int(row["connection_id"]),
        "provider": str(row["provider"]),
        "display_name": str(row["display_name"]),
        "username": username,
        "marketplace": row["marketplace"],
        "connection_status": str(row["connection_status"]),
        "connected_at": row["connected_at"],
        "is_seed": int(row["is_seed"]) == 1,
        "profile_url": profile_url,
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
# Pinterest connection + credential management (server-side only)
# --------------------------------------------------


def fetch_connection_safe_row(
    connection_id: int,
) -> dict[str, Any] | None:
    """
    Return the safe metadata row for a connection, or None.

    Never reads the ``connection_credentials`` table.
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
    WHERE connection_id = ?
    """

    with get_connection() as connection:
        row = connection.execute(
            query,
            (connection_id,),
        ).fetchone()

    return _safe_connection_row(row) if row else None


def create_or_update_pinterest_connection(
    *,
    account_id: int,
    display_name: str,
    username: str,
) -> int:
    """
    Create or update the real Pinterest connection for an account.

    Reconnection reuses the existing ``account_connections`` row for the
    account (via the unique ``(provider, pinterest_account_id)`` key), so
    reconnecting an already-connected Pinterest account updates the same
    connection instead of creating a duplicate. The connection is marked
    CONNECTED with ``is_seed = 0``.

    Returns:
        The ``connection_id`` of the created/updated connection.
    """

    query_find = """
    SELECT connection_id
    FROM account_connections
    WHERE provider = ? AND pinterest_account_id = ?
    """

    query_update = """
    UPDATE account_connections
    SET
        display_name = ?,
        username = ?,
        connection_status = ?,
        connected_at = CURRENT_TIMESTAMP,
        is_seed = 0,
        updated_at = CURRENT_TIMESTAMP
    WHERE connection_id = ?
    """

    query_insert = """
    INSERT INTO account_connections (
        provider,
        display_name,
        username,
        pinterest_account_id,
        connection_status,
        connected_at,
        is_seed
    )
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)
    """

    with get_connection() as connection:

        row = connection.execute(
            query_find,
            (PROVIDER_PINTEREST, account_id),
        ).fetchone()

        if row is not None:
            connection_id = int(row["connection_id"])
            connection.execute(
                query_update,
                (
                    display_name,
                    username,
                    CONNECTION_CONNECTED,
                    connection_id,
                ),
            )
        else:
            cursor = connection.execute(
                query_insert,
                (
                    PROVIDER_PINTEREST,
                    display_name,
                    username,
                    account_id,
                    CONNECTION_CONNECTED,
                ),
            )
            connection_id = int(cursor.lastrowid)

        connection.commit()

    return connection_id


def save_connection_credentials(
    connection_id: int,
    credentials: dict[str, str],
) -> None:
    """
    Upsert server-side-only credentials for a connection.

    Credentials live in ``connection_credentials`` (a separate table from
    safe metadata) and are never returned by the API. The upsert keeps a
    single row per ``(connection_id, credential_type)``.

    Raises:
        sqlite3.Error: If a credential cannot be persisted.
    """

    query = """
    INSERT INTO connection_credentials (
        connection_id,
        credential_type,
        credential_value,
        updated_at
    )
    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT (connection_id, credential_type)
    DO UPDATE SET
        credential_value = excluded.credential_value,
        updated_at = CURRENT_TIMESTAMP
    """

    with get_connection() as connection:
        for credential_type, value in credentials.items():
            connection.execute(
                query,
                (connection_id, credential_type, value),
            )
        connection.commit()


def fetch_connection_credentials(
    connection_id: int,
) -> dict[str, str]:
    """
    Return the stored credentials for a connection.

    Server-side only. The Accounts API never calls this; it exists for the
    token-refresh and future publishing paths. Credentials are never
    serialized to the frontend.

    Raises:
        sqlite3.Error: If the credential lookup fails.
    """

    query = """
    SELECT credential_type, credential_value
    FROM connection_credentials
    WHERE connection_id = ?
    """

    with get_connection() as connection:
        rows = connection.execute(
            query,
            (connection_id,),
        ).fetchall()

    return {
        str(row["credential_type"]): str(row["credential_value"])
        for row in rows
    }


def refresh_stored_pinterest_credentials(
    connection_id: int,
) -> dict[str, Any]:
    """
    Refresh a Pinterest connection's access token server-side.

    Reads the stored refresh token, calls Pinterest's current
    refresh-token grant, and updates the stored credentials (new access
    token, rotated refresh token if returned, scope and expiry). Safe to
    call before any authenticated Pinterest API request when the stored
    access token may have expired.

    Returns:
        A dict with the new ``access_token`` for server-side use. Never
        exposed by the API.

    Raises:
        ValueError: If no refresh token is stored.
        PinterestConfigError / PinterestTokenError / PinterestApiError:
            From the underlying refresh call.
        sqlite3.Error: If the stored credentials cannot be updated.
    """

    stored = fetch_connection_credentials(connection_id)

    refresh_token = stored.get(CREDENTIAL_PINTEREST_REFRESH_TOKEN)
    if not refresh_token:
        raise ValueError(
            "No Pinterest refresh token is stored for this connection."
        )

    scope = stored.get(CREDENTIAL_PINTEREST_SCOPE)

    tokens = refresh_access_token(refresh_token, scope=scope)

    access_token = tokens.get("access_token")
    if not access_token:
        raise ValueError(
            "Pinterest returned no new access token during refresh."
        )

    updates: dict[str, str] = {
        CREDENTIAL_PINTEREST_ACCESS_TOKEN: access_token,
    }

    if tokens.get("refresh_token"):
        updates[CREDENTIAL_PINTEREST_REFRESH_TOKEN] = tokens["refresh_token"]

    if tokens.get("scope"):
        updates[CREDENTIAL_PINTEREST_SCOPE] = tokens["scope"]

    expires_in = tokens.get("expires_in")
    if expires_in:
        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(seconds=int(expires_in))
        ).isoformat()
        updates[CREDENTIAL_PINTEREST_TOKEN_EXPIRES_AT] = expires_at

    save_connection_credentials(connection_id, updates)

    return {"access_token": access_token}


def disconnect_pinterest_connection(
    connection_id: int,
) -> dict[str, Any] | None:
    """
    Disconnect a Pinterest connection.

    Removes stored credentials, marks the connection DISCONNECTED and
    clears ``connected_at`` while preserving safe account metadata
    (display name, username, Pinterest account link). Seed/sample
    connections are never modified.

    Returns:
        The updated safe connection row, or None if the connection does
        not exist.

    Raises:
        ValueError: If the connection is a seed/sample account.
        sqlite3.Error: If the update fails.
    """

    with get_connection() as connection:

        row = connection.execute(
            "SELECT connection_id, is_seed FROM account_connections"
            " WHERE connection_id = ?",
            (connection_id,),
        ).fetchone()

        if row is None:
            return None

        if int(row["is_seed"]) == 1:
            raise ValueError(
                "Sample accounts cannot be disconnected."
            )

        connection.execute(
            "UPDATE account_connections"
            " SET connection_status = ?, connected_at = NULL,"
            " updated_at = CURRENT_TIMESTAMP"
            " WHERE connection_id = ?",
            (CONNECTION_DISCONNECTED, connection_id),
        )

        connection.execute(
            "DELETE FROM connection_credentials WHERE connection_id = ?",
            (connection_id,),
        )

        connection.commit()

    return fetch_connection_safe_row(connection_id)


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
