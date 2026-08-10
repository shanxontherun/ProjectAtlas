"""
Pinterest OAuth 2 Authorization Code flow (ATLAS-029C).

Implements the real Pinterest OAuth flow used by the Accounts page:

    Connect Pinterest
      -> redirect the user to Pinterest authorization
      -> Pinterest redirects back with an authorization code + state
      -> validate state (server-side, CSRF protection)
      -> exchange the code for tokens (server-side, never in the browser)
      -> fetch the authenticated Pinterest user
      -> persist account / connection / credentials (server-side only)
      -> sync the user's Pinterest boards
      -> return to Accounts

Security rules enforced here:

- OAuth code exchange always happens server-side.
- Client secrets, access tokens, refresh tokens, authorization codes and
  OAuth URLs are never logged and never returned to the frontend.
- OAuth state is cryptographically random, stored server-side with an
  expiry, and validated on the callback (missing / mismatched / expired
  states are rejected).
- User denial, missing code, and token / API errors fail safely with
  typed exceptions; the API layer maps them to a safe user-facing result.

This module performs the OAuth + Pinterest API network calls and the
flow orchestration; database persistence is delegated to the existing
data access services (``pinterest_accounts``, ``accounts_service``,
``pinterest_boards``). No secrets are ever serialized.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import secrets
import socket
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from services.constants import (
    CREDENTIAL_PINTEREST_ACCESS_TOKEN,
    CREDENTIAL_PINTEREST_REFRESH_TOKEN,
    CREDENTIAL_PINTEREST_SCOPE,
    CREDENTIAL_PINTEREST_TOKEN_EXPIRES_AT,
    PINTEREST_API_BASE,
    PINTEREST_AUTHORIZE_URL,
    PINTEREST_BOARDS_ENDPOINT,
    PINTEREST_CLIENT_ID_ENV,
    PINTEREST_CLIENT_SECRET_ENV,
    PINTEREST_OAUTH_SCOPES,
    PINTEREST_REDIRECT_URI_ENV,
    PINTEREST_STATE_TTL_SECONDS,
    PINTEREST_TOKEN_URL,
    PINTEREST_USER_ENDPOINT,
)
from services.database import get_connection

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT_SECONDS = 15

# How many pagination pages to fetch when syncing boards (safety cap).
_BOARD_PAGE_CAP = 20
_BOARD_PAGE_SIZE = 100


# --------------------------------------------------
# Typed errors (safe, user-facing messages only)
# --------------------------------------------------


class PinterestOAuthError(Exception):
    """Base class for Pinterest OAuth failures."""


class PinterestConfigError(PinterestOAuthError):
    """Pinterest OAuth is not configured (missing env vars)."""


class PinterestStateError(PinterestOAuthError):
    """The OAuth state is missing, mismatched or expired."""


class PinterestDeniedError(PinterestOAuthError):
    """The user denied (or cancelled) Pinterest authorization."""


class PinterestTokenError(PinterestOAuthError):
    """The token exchange / refresh failed."""


class PinterestApiError(PinterestOAuthError):
    """A Pinterest API call failed (auth, rate limit, malformed, etc.)."""


# --------------------------------------------------
# Configuration (secrets are never logged or returned)
# --------------------------------------------------


def pinterest_config_available() -> bool:
    """Whether the Pinterest OAuth environment configuration is present."""
    return bool(
        os.environ.get(PINTEREST_CLIENT_ID_ENV, "").strip()
        and os.environ.get(PINTEREST_CLIENT_SECRET_ENV, "").strip()
        and os.environ.get(PINTEREST_REDIRECT_URI_ENV, "").strip()
    )


def _read_pinterest_config() -> dict[str, str]:
    """
    Return the Pinterest OAuth client configuration.

    Raises:
        PinterestConfigError:
            If any required environment variable is missing.
    """

    client_id = os.environ.get(PINTEREST_CLIENT_ID_ENV, "").strip()
    client_secret = os.environ.get(PINTEREST_CLIENT_SECRET_ENV, "").strip()
    redirect_uri = os.environ.get(PINTEREST_REDIRECT_URI_ENV, "").strip()

    if not client_id or not client_secret or not redirect_uri:
        raise PinterestConfigError(
            "Pinterest OAuth is not configured. Set PINTEREST_CLIENT_ID, "
            "PINTEREST_CLIENT_SECRET and PINTEREST_REDIRECT_URI to connect "
            "a Pinterest account."
        )

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }


# --------------------------------------------------
# OAuth state (CSRF protection)
# --------------------------------------------------


def generate_oauth_state() -> str:
    """
    Return a cryptographically secure OAuth state value.

    Uses ``secrets.token_urlsafe`` with 256 bits of entropy so state
    values cannot be guessed or forged.
    """
    return secrets.token_urlsafe(32)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _state_expiry() -> str:
    return (
        _now_utc() + timedelta(seconds=PINTEREST_STATE_TTL_SECONDS)
    ).isoformat()


def store_oauth_state(state: str) -> None:
    """
    Persist an OAuth state with an expiry so the callback can validate it.

    Raises:
        sqlite3.Error: If the state cannot be stored.
    """

    query = "INSERT INTO oauth_states (state, expires_at) VALUES (?, ?)"
    connection = get_connection()
    try:
        connection.execute(query, (state, _state_expiry()))
        connection.commit()
    finally:
        connection.close()


def validate_oauth_state(state: str | None) -> None:
    """
    Validate an OAuth state on the callback.

    Rejects missing, unknown (mismatched / already-used) and expired
    states. The state row is consumed on validation so it cannot be
    replayed.

    Raises:
        PinterestStateError: If the state is missing, mismatched or expired.
        sqlite3.Error: If the state cannot be looked up.
    """

    if not state:
        raise PinterestStateError("OAuth state is missing.")

    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT expires_at FROM oauth_states WHERE state = ?",
            (state,),
        ).fetchone()

        connection.execute(
            "DELETE FROM oauth_states WHERE state = ?",
            (state,),
        )
        connection.execute(
            "DELETE FROM oauth_states WHERE expires_at < ?",
            (_now_utc().isoformat(),),
        )
        connection.commit()
    finally:
        connection.close()

    if row is None:
        raise PinterestStateError("OAuth state is invalid or has already been used.")

    expires_at = row["expires_at"]
    parsed = datetime.fromisoformat(expires_at)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    if parsed < _now_utc():
        raise PinterestStateError("OAuth state has expired.")


# --------------------------------------------------
# Authorization URL
# --------------------------------------------------


def build_authorization_url(state: str) -> str:
    """
    Build the Pinterest authorization URL for the current app config.

    Uses the required OAuth parameters (client_id, redirect_uri,
    response_type=code, scope, state). The caller must have already
    generated and stored ``state``.
    """

    config = _read_pinterest_config()

    query = urllib.parse.urlencode(
        {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "response_type": "code",
            "scope": PINTEREST_OAUTH_SCOPES,
            "state": state,
        }
    )

    return f"{PINTEREST_AUTHORIZE_URL}?{query}"


# --------------------------------------------------
# HTTP helper (never logs secrets)
# --------------------------------------------------


def _http_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> tuple[int, Any]:
    """
    Perform an HTTPS request and return ``(status_code, parsed_json)``.

    Transport failures raise ``PinterestApiError`` with a safe message.
    HTTP error statuses are returned (not raised) so callers can react to
    401 / 403 / 429 distinctly.
    """

    request = urllib.request.Request(
        url,
        method=method,
        headers=headers or {},
        data=data,
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=_HTTP_TIMEOUT_SECONDS,
        ) as response:
            status = int(response.getcode())
            body = response.read()
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        try:
            body = exc.read()
        except Exception:  # pragma: no cover - defensive
            body = b""
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError):
        raise PinterestApiError(
            "Couldn't reach Pinterest. Please try again in a moment."
        ) from None

    if not body:
        return status, {}

    try:
        payload = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        payload = {}

    return status, payload


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    token = base64.b64encode(
        f"{client_id}:{client_secret}".encode("utf-8")
    ).decode("ascii")
    return f"Basic {token}"


def _parse_token_payload(payload: Any) -> dict[str, str | None]:
    """Extract the safe token fields from a Pinterest token response."""

    if not isinstance(payload, dict):
        raise PinterestTokenError(
            "Pinterest returned an invalid token response."
        )

    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise PinterestTokenError(
            "Pinterest returned an invalid token response."
        )

    refresh_token = payload.get("refresh_token")
    expires_in_raw = payload.get("expires_in")
    scope = payload.get("scope")

    return {
        "access_token": access_token,
        "refresh_token": (
            refresh_token if isinstance(refresh_token, str) and refresh_token else None
        ),
        "expires_in": (
            int(expires_in_raw)
            if isinstance(expires_in_raw, (int, float))
            else None
        ),
        "scope": scope if isinstance(scope, str) else None,
    }


# --------------------------------------------------
# Token exchange / refresh (server-side only)
# --------------------------------------------------


def exchange_code_for_token(code: str) -> dict[str, str | None]:
    """
    Exchange an authorization code for access / refresh tokens.

    Uses HTTP Basic authentication (client_id:client_secret) against the
    current Pinterest token endpoint with the ``authorization_code``
    grant. The exchange runs entirely server-side.

    Raises:
        PinterestConfigError: If Pinterest OAuth is not configured.
        PinterestTokenError: If the exchange fails.
        PinterestApiError: If Pinterest cannot be reached.
    """

    config = _read_pinterest_config()

    form = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config["redirect_uri"],
        }
    ).encode("utf-8")

    status, payload = _http_request(
        PINTEREST_TOKEN_URL,
        method="POST",
        headers={
            "Authorization": _basic_auth_header(
                config["client_id"],
                config["client_secret"],
            ),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=form,
    )

    if status != 200:
        raise PinterestTokenError(
            "Pinterest rejected the authorization code. Please try again."
        )

    return _parse_token_payload(payload)


def refresh_access_token(
    refresh_token: str,
    scope: str | None = None,
) -> dict[str, str | None]:
    """
    Exchange a refresh token for a new access token (server-side).

    Uses Pinterest's current refresh-token grant against
    ``/v5/oauth/token`` with ``grant_type=refresh_token``.

    Raises:
        PinterestConfigError: If Pinterest OAuth is not configured.
        PinterestTokenError: If the refresh fails (e.g. expired/invalid).
        PinterestApiError: If Pinterest cannot be reached.
    """

    config = _read_pinterest_config()

    fields: dict[str, str] = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    if scope:
        fields["scope"] = scope

    form = urllib.parse.urlencode(fields).encode("utf-8")

    status, payload = _http_request(
        PINTEREST_TOKEN_URL,
        method="POST",
        headers={
            "Authorization": _basic_auth_header(
                config["client_id"],
                config["client_secret"],
            ),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=form,
    )

    if status != 200:
        raise PinterestTokenError(
            "Pinterest could not refresh the access token. "
            "Reconnect the Pinterest account."
        )

    return _parse_token_payload(payload)


# --------------------------------------------------
# Pinterest API calls
# --------------------------------------------------


def _authorized_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def fetch_pinterest_user(access_token: str) -> dict[str, Any]:
    """
    Fetch the authenticated Pinterest user from the current API endpoint.

    Returns only safe identity fields (id, username, account type).
    Never returns tokens.

    Raises:
        PinterestApiError: If Pinterest rejects or malforms the response.
    """

    status, payload = _http_request(
        PINTEREST_USER_ENDPOINT,
        headers=_authorized_headers(access_token),
    )

    if status in (401, 403):
        raise PinterestApiError(
            "Pinterest rejected the access token. Reconnect the account."
        )
    if status == 429:
        raise PinterestApiError(
            "Pinterest is rate-limiting requests. Try again in a moment."
        )
    if status != 200:
        raise PinterestApiError(
            "Pinterest couldn't return the account. Try again in a moment."
        )

    if not isinstance(payload, dict):
        raise PinterestApiError(
            "Pinterest returned an unexpected account response."
        )

    user_id = payload.get("id")
    username = payload.get("username")

    if user_id is None or not isinstance(username, str) or not username:
        raise PinterestApiError(
            "Pinterest returned an unexpected account response."
        )

    return {
        "id": str(user_id),
        "username": username,
        "account_type": (
            payload.get("account_type")
            if isinstance(payload.get("account_type"), str)
            else None
        ),
    }


def fetch_pinterest_boards(access_token: str) -> list[dict[str, Any]]:
    """
    Fetch the authenticated user's Pinterest boards (paginated).

    Returns safe board fields only: Pinterest board id, name and privacy.
    Never returns tokens or statistics.

    Raises:
        PinterestApiError: If Pinterest rejects or malforms the response.
    """

    boards: list[dict[str, Any]] = []
    bookmark: str | None = None

    for _ in range(_BOARD_PAGE_CAP):
        params: dict[str, Any] = {"page_size": _BOARD_PAGE_SIZE}
        if bookmark:
            params["bookmark"] = bookmark

        url = f"{PINTEREST_BOARDS_ENDPOINT}?{urllib.parse.urlencode(params)}"

        status, payload = _http_request(
            url,
            headers=_authorized_headers(access_token),
        )

        if status in (401, 403):
            raise PinterestApiError(
                "Pinterest rejected the access token. Reconnect the account."
            )
        if status == 429:
            raise PinterestApiError(
                "Pinterest is rate-limiting requests. Try again in a moment."
            )
        if status != 200:
            raise PinterestApiError(
                "Pinterest couldn't return the boards. Try again in a moment."
            )

        if not isinstance(payload, dict):
            raise PinterestApiError(
                "Pinterest returned an unexpected boards response."
            )

        items = payload.get("items")
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                board_id = item.get("id")
                name = item.get("name")
                if board_id is None or not isinstance(name, str) or not name:
                    continue
                boards.append(
                    {
                        "id": str(board_id),
                        "name": name,
                        "privacy": (
                            item.get("privacy")
                            if isinstance(item.get("privacy"), str)
                            else None
                        ),
                    }
                )

        bookmark = payload.get("bookmark")
        if not isinstance(bookmark, str) or not bookmark:
            break

    return boards


# --------------------------------------------------
# Flow orchestration
# --------------------------------------------------


def start_pinterest_connect() -> dict[str, str]:
    """
    Start a Pinterest OAuth flow and return the authorization URL.

    Generates and stores a cryptographically secure state, then builds
    the Pinterest authorization URL. The URL contains the client_id and
    state but no secret.

    Raises:
        PinterestConfigError: If Pinterest OAuth is not configured.
        sqlite3.Error: If the state cannot be stored.
    """

    _read_pinterest_config()

    state = generate_oauth_state()
    store_oauth_state(state)

    return {"authorization_url": build_authorization_url(state)}


def complete_pinterest_connect(
    state: str | None,
    code: str | None,
    error: str | None = None,
) -> dict[str, Any]:
    """
    Finish a Pinterest OAuth flow after the callback.

    Validates the state, then (server-side) exchanges the code, fetches
    the Pinterest user, persists the account / connection / credentials,
    and syncs the user's boards. Board sync is best-effort: if it fails
    the connection still completes with ``status="partial"`` so the UI
    never claims full success it did not achieve.

    Returns a safe result:
        {
            "status": "success" | "partial",
            "connection": {safe account_connections metadata},
            "boards_synced": int,
        }

    Raises:
        PinterestStateError: If the state is missing/mismatched/expired.
        PinterestDeniedError: If the user denied authorization.
        PinterestOAuthError: If the code is missing or Pinterest errors.
        PinterestTokenError / PinterestApiError: token or API failures.
        sqlite3.Error: If persistence fails (account/connection/credentials).
    """

    validate_oauth_state(state)

    if error:
        normalized = error.lower()
        if normalized in (
            "access_denied",
            "user_denied",
            "denied",
            "authentication_denied",
            "canceled",
            "cancelled",
        ):
            raise PinterestDeniedError()
        raise PinterestOAuthError(
            "Pinterest returned an error during authorization."
        )

    if not code:
        raise PinterestOAuthError(
            "Pinterest did not return an authorization code."
        )

    tokens = exchange_code_for_token(code)

    access_token = tokens["access_token"]
    if not access_token:
        raise PinterestTokenError(
            "Pinterest returned an invalid token response."
        )

    user = fetch_pinterest_user(access_token)

    # Persist real (non-seed) Pinterest account, reusing an existing row on
    # reconnection so multiple connects never create duplicate accounts.
    from services.pinterest_accounts import upsert_real_pinterest_account

    account_id = upsert_real_pinterest_account(user)

    from services.accounts_service import (
        create_or_update_pinterest_connection,
        fetch_connection_safe_row,
        save_connection_credentials,
    )

    connection_id = create_or_update_pinterest_connection(
        account_id=account_id,
        display_name=user["username"],
        username=user["username"],
    )

    credentials: dict[str, str] = {
        CREDENTIAL_PINTEREST_ACCESS_TOKEN: access_token,
    }
    if tokens.get("refresh_token"):
        credentials[CREDENTIAL_PINTEREST_REFRESH_TOKEN] = tokens["refresh_token"]
    if tokens.get("scope"):
        credentials[CREDENTIAL_PINTEREST_SCOPE] = tokens["scope"]

    expires_in = tokens.get("expires_in")
    if expires_in:
        expires_at = (
            _now_utc() + timedelta(seconds=int(expires_in))
        ).isoformat()
        credentials[CREDENTIAL_PINTEREST_TOKEN_EXPIRES_AT] = expires_at

    save_connection_credentials(connection_id, credentials)

    # Board sync is best effort: report a partial success rather than a
    # false full success when Pinterest returns boards with an error.
    boards_synced = 0
    boards_ok = True
    try:
        from services.pinterest_boards import sync_real_boards

        boards = fetch_pinterest_boards(access_token)
        boards_synced = sync_real_boards(account_id, boards)
    except (PinterestApiError, sqlite3.Error) as exc:
        boards_ok = False
        logger.warning("Pinterest board sync failed: %s", type(exc).__name__)

    connection = fetch_connection_safe_row(connection_id)

    return {
        "status": "success" if boards_ok else "partial",
        "connection": connection,
        "boards_synced": boards_synced,
    }
