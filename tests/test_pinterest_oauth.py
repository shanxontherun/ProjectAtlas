"""
ATLAS-029C Pinterest OAuth test suite.

Builds a throwaway database from the real migrations and exercises the
real OAuth flow with mocked Pinterest API responses (no real credentials
are required or used):

  - secure state generation
  - state validation (valid / missing / mismatched / expired / replay)
  - missing OAuth configuration
  - callback errors (denial, missing code, invalid state)
  - token exchange success / failure
  - account mapping (real account upsert, seed-conversion protection)
  - credential persistence (server-side only)
  - safe /accounts response (no credentials anywhere)
  - duplicate-connection handling (reconnect reuses the connection)
  - disconnect (credentials removed, metadata preserved, seed untouched)
  - board synchronization (insert, dedupe on re-sync, seed untouched)
  - partial failure when board sync fails
  - token refresh
  - API endpoint behavior (connect / callback / disconnect)

Run with:  PYTHONPATH=/workspace python3 tests/test_pinterest_oauth.py
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "services"))

import services.database as database_module  # noqa: E402
import services.pinterest_oauth as pinterest_oauth  # noqa: E402
from services.pinterest_oauth import (  # noqa: E402
    PinterestApiError,
    PinterestConfigError,
    PinterestDeniedError,
    PinterestOAuthError,
    PinterestStateError,
    PinterestTokenError,
    complete_pinterest_connect,
    exchange_code_for_token,
    generate_oauth_state,
    refresh_access_token,
    start_pinterest_connect,
    store_oauth_state,
    validate_oauth_state,
)
from services.accounts_service import (  # noqa: E402
    disconnect_pinterest_connection,
    fetch_accounts,
    fetch_connection_credentials,
    fetch_connection_safe_row,
    refresh_stored_pinterest_credentials,
)
from services.pinterest_accounts import (  # noqa: E402
    fetch_account,
    upsert_real_pinterest_account,
)
from services.constants import (  # noqa: E402
    CONNECTION_CONNECTED,
    CONNECTION_DISCONNECTED,
    CONNECTION_NOT_CONNECTED,
    CREDENTIAL_PINTEREST_ACCESS_TOKEN,
    CREDENTIAL_PINTEREST_REFRESH_TOKEN,
)

FAKE_TOKEN_PAYLOAD = {
    "access_token": "pina_fake_access_token_123",
    "refresh_token": "pinr_fake_refresh_token_456",
    "token_type": "bearer",
    "expires_in": 2592000,
    "scope": "user_accounts:read boards:read pins:read pins:write",
}

FAKE_USER_PAYLOAD = {
    "id": "987654321",
    "username": "real_pinterest_user",
    "account_type": "BUSINESS",
    "profile_image": "https://example.com/avatar.png",
}

FAKE_BOARDS_PAYLOAD = {
    "items": [
        {"id": "board_real_1", "name": "Real Board One", "privacy": "PUBLIC"},
        {"id": "board_real_2", "name": "Real Board Two", "privacy": "SECRET"},
    ],
    "bookmark": None,
}


def build_database(db_path: Path) -> None:
    """Apply every sql/*.sql migration in filename order to a fresh DB."""

    conn = sqlite3.connect(db_path)

    for migration in sorted((PROJECT_ROOT / "sql").glob("*.sql")):
        conn.executescript(migration.read_text(encoding="utf-8"))

    conn.commit()
    conn.close()


def open_db(db_path: Path) -> sqlite3.Connection:
    """Open a connection with named-row access for assertions."""

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def make_fake_http(
    *,
    token_status: int = 200,
    user_status: int = 200,
    boards_status: int = 200,
    boards_payload: dict | None = None,
) -> tuple[object, list[str]]:
    """Build a mock ``_http_request`` dispatcher recording called URLs."""

    calls: list[str] = []

    def handler(
        url: str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        data: bytes | None = None,
    ) -> tuple[int, object]:
        calls.append(url)
        if "oauth/token" in url:
            if token_status != 200:
                return token_status, {}
            return token_status, FAKE_TOKEN_PAYLOAD
        if url.startswith(pinterest_oauth.PINTEREST_USER_ENDPOINT):
            if user_status != 200:
                return user_status, {}
            return user_status, FAKE_USER_PAYLOAD
        if url.startswith(pinterest_oauth.PINTEREST_BOARDS_ENDPOINT):
            if boards_status != 200:
                return boards_status, {}
            return boards_status, (boards_payload or FAKE_BOARDS_PAYLOAD)
        return 500, {}

    return handler, calls


def run_full_flow(
    code: str = "auth-code-1",
) -> dict:
    """Complete a full mocked OAuth flow against the current DB."""

    state = generate_oauth_state()
    store_oauth_state(state)
    return complete_pinterest_connect(state=state, code=code)


def main() -> None:
    failures: list[str] = []

    def check(
        name: str,
        condition: bool,
        detail: str = "",
    ) -> None:
        status = "ok" if condition else "FAIL"
        print(f"[{status}] {name}")
        if not condition:
            failures.append(f"{name}: {detail}")

    # ------------------------------------------------------------
    # Isolation: every check runs against the same throwaway DB.
    # ------------------------------------------------------------
    tmp = tempfile.mkdtemp(prefix="atlas_pinterest_oauth_test_")
    db_path = Path(tmp) / "atlas.db"
    build_database(db_path)

    original_path = database_module.DATABASE_PATH
    database_module.DATABASE_PATH = db_path

    saved_env = {
        key: os.environ.get(key)
        for key in (
            "PINTEREST_CLIENT_ID",
            "PINTEREST_CLIENT_SECRET",
            "PINTEREST_REDIRECT_URI",
        )
    }
    os.environ["PINTEREST_CLIENT_ID"] = "test-client-id"
    os.environ["PINTEREST_CLIENT_SECRET"] = "test-client-secret"
    os.environ["PINTEREST_REDIRECT_URI"] = "https://example.com/api/accounts/pinterest/callback"

    try:
        # --------------------------------------------------------
        # 1. Secure state generation
        # --------------------------------------------------------
        first = generate_oauth_state()
        second = generate_oauth_state()

        check(
            "state is long and url-safe",
            len(first) >= 32
            and first.replace("_", "").replace("-", "").isalnum(),
            f"state={first!r}",
        )
        check(
            "states are unique",
            first != second,
            "identical states generated",
        )

        # --------------------------------------------------------
        # 2. State validation
        # --------------------------------------------------------
        valid_state = generate_oauth_state()
        store_oauth_state(valid_state)
        validate_oauth_state(valid_state)
        check(
            "valid state is accepted",
            True,
        )

        try:
            validate_oauth_state(valid_state)
            check("replayed state rejected", False, "accepted twice")
        except PinterestStateError:
            check("replayed state rejected", True)

        for bad_state in (None, "not-a-real-state"):
            try:
                validate_oauth_state(bad_state)
                check(
                    f"state {bad_state!r} rejected",
                    False,
                    "was accepted",
                )
            except PinterestStateError:
                check(f"state {bad_state!r} rejected", True)

        # Expired state: insert one with a past expiry directly.
        expired_state = generate_oauth_state()
        conn = open_db(db_path)
        conn.execute(
            "INSERT INTO oauth_states (state, expires_at)"
            " VALUES (?, ?)",
            (expired_state, "2000-01-01T00:00:00+00:00"),
        )
        conn.commit()
        conn.close()

        try:
            validate_oauth_state(expired_state)
            check("expired state rejected", False, "was accepted")
        except PinterestStateError:
            check("expired state rejected", True)

        # --------------------------------------------------------
        # 3. Missing configuration
        # --------------------------------------------------------
        os.environ.pop("PINTEREST_CLIENT_ID", None)
        os.environ.pop("PINTEREST_CLIENT_SECRET", None)
        os.environ.pop("PINTEREST_REDIRECT_URI", None)

        check(
            "config availability false when env missing",
            pinterest_oauth.pinterest_config_available() is False,
        )

        try:
            start_pinterest_connect()
            check("missing config raises", False, "no error raised")
        except PinterestConfigError:
            check("missing config raises", True)

        os.environ["PINTEREST_CLIENT_ID"] = "test-client-id"
        os.environ["PINTEREST_CLIENT_SECRET"] = "test-client-secret"
        os.environ["PINTEREST_REDIRECT_URI"] = "https://example.com/api/accounts/pinterest/callback"

        # --------------------------------------------------------
        # 4. Connect starts and builds the authorization URL
        # --------------------------------------------------------
        with mock.patch.object(
            pinterest_oauth,
            "_http_request",
            *make_fake_http(),
        ):
            result = start_pinterest_connect()

        import urllib.parse

        parsed = urllib.parse.urlparse(result["authorization_url"])
        query = urllib.parse.parse_qs(parsed.query)

        check(
            "authorization URL points at Pinterest OAuth",
            parsed.scheme == "https"
            and parsed.netloc == "www.pinterest.com"
            and parsed.path == "/oauth/",
            result["authorization_url"],
        )
        check(
            "authorization URL has required OAuth params",
            set(query.keys()) == {
                "client_id",
                "redirect_uri",
                "response_type",
                "scope",
                "state",
            },
            str(sorted(query.keys())),
        )
        check(
            "response_type is code",
            query.get("response_type") == ["code"],
        )
        check(
            "scopes cover user + boards + pins",
            set(query["scope"][0].split(",")) == {
                "user_accounts:read",
                "boards:read",
                "pins:read",
                "pins:write",
            },
            query["scope"][0],
        )
        check(
            "state never appears in response payload",
            "state" not in result,
            str(result),
        )

        # --------------------------------------------------------
        # 5. Callback errors: denial / missing code / invalid state
        # --------------------------------------------------------
        state = generate_oauth_state()
        store_oauth_state(state)
        try:
            complete_pinterest_connect(state=state, code=None, error="access_denied")
            check("user denial raises PinterestDeniedError", False, "no error")
        except PinterestDeniedError:
            check("user denial raises PinterestDeniedError", True)

        state = generate_oauth_state()
        store_oauth_state(state)
        try:
            complete_pinterest_connect(state=state, code=None)
            check("missing code raises", False, "no error")
        except PinterestOAuthError:
            check("missing code raises", True)

        try:
            complete_pinterest_connect(state=None, code="whatever")
            check("missing state raises", False, "no error")
        except PinterestStateError:
            check("missing state raises", True)

        # --------------------------------------------------------
        # 6. Token exchange success / failure
        # --------------------------------------------------------
        handler, _ = make_fake_http()
        with mock.patch.object(pinterest_oauth, "_http_request", handler):
            tokens = exchange_code_for_token("some-code")

        check(
            "token exchange parses tokens",
            tokens["access_token"] == FAKE_TOKEN_PAYLOAD["access_token"]
            and tokens["refresh_token"] == FAKE_TOKEN_PAYLOAD["refresh_token"]
            and tokens["expires_in"] == 2592000,
            str(tokens),
        )

        handler_fail, _ = make_fake_http(token_status=400)
        with mock.patch.object(pinterest_oauth, "_http_request", handler_fail):
            try:
                exchange_code_for_token("bad-code")
                check("token exchange failure raises", False, "no error")
            except PinterestTokenError:
                check("token exchange failure raises", True)

        # --------------------------------------------------------
        # 7. Full flow: real account + connection + credentials + boards
        # --------------------------------------------------------
        handler, calls = make_fake_http()
        with mock.patch.object(pinterest_oauth, "_http_request", handler):
            result = run_full_flow()

        check(
            "full flow reports success",
            result["status"] == "success",
            str(result),
        )
        check(
            "full flow syncs 2 boards",
            result["boards_synced"] == 2,
            str(result["boards_synced"]),
        )

        connection = result["connection"]
        check(
            "connection is CONNECTED and non-seed",
            connection["connection_status"] == CONNECTION_CONNECTED
            and connection["is_seed"] is False
            and connection["username"] == FAKE_USER_PAYLOAD["username"],
            str(connection),
        )
        check(
            "connected_at is set",
            connection["connected_at"] is not None,
            str(connection["connected_at"]),
        )
        check(
            "profile_url derived from username (safe)",
            connection["profile_url"]
            == "https://www.pinterest.com/real_pinterest_user/",
            str(connection.get("profile_url")),
        )

        # Account row: real, non-seed, with Pinterest user id.
        conn = open_db(db_path)
        real_account = conn.execute(
            "SELECT * FROM pinterest_accounts WHERE username = ?",
            (FAKE_USER_PAYLOAD["username"],),
        ).fetchone()
        check(
            "real Pinterest account persisted (is_seed=0, user id set)",
            real_account is not None
            and int(real_account["is_seed"]) == 0
            and real_account["pinterest_user_id"] == FAKE_USER_PAYLOAD["id"],
            dict(real_account) if real_account else None,
        )

        # Seed accounts/connections unchanged.
        seed_accounts = conn.execute(
            "SELECT COUNT(*) AS n FROM pinterest_accounts WHERE is_seed = 1"
        ).fetchone()["n"]
        seed_connections = conn.execute(
            "SELECT COUNT(*) AS n FROM account_connections WHERE is_seed = 1"
            " AND connection_status = ?",
            (CONNECTION_NOT_CONNECTED,),
        ).fetchone()["n"]
        check(
            "seed accounts and connections untouched",
            seed_accounts == 2 and seed_connections == 2,
            f"accounts={seed_accounts} connections={seed_connections}",
        )

        # Credentials stored server-side.
        credentials = fetch_connection_credentials(connection["connection_id"])
        check(
            "access + refresh tokens stored server-side",
            credentials.get(CREDENTIAL_PINTEREST_ACCESS_TOKEN)
            == FAKE_TOKEN_PAYLOAD["access_token"]
            and credentials.get(CREDENTIAL_PINTEREST_REFRESH_TOKEN)
            == FAKE_TOKEN_PAYLOAD["refresh_token"],
            str(list(credentials.keys())),
        )

        # Real boards synced; seed boards untouched.
        real_boards = conn.execute(
            "SELECT board_id, board_name, status, pinterest_board_id, privacy"
            " FROM pinterest_boards WHERE pinterest_board_id IS NOT NULL"
        ).fetchall()
        seed_boards = conn.execute(
            "SELECT COUNT(*) AS n FROM pinterest_boards"
            " WHERE pinterest_board_id IS NULL AND status = 'ACTIVE'"
        ).fetchone()["n"]
        check(
            "real boards persisted with Pinterest ids and privacy",
            len(real_boards) == 2
            and {r["pinterest_board_id"] for r in real_boards}
            == {"board_real_1", "board_real_2"}
            and {r["privacy"] for r in real_boards} == {"PUBLIC", "SECRET"}
            and all(r["status"] == "ACTIVE" for r in real_boards),
            str([dict(r) for r in real_boards]),
        )
        check(
            "seed boards untouched (5 ACTIVE, no Pinterest ids)",
            seed_boards == 5,
            f"seed ACTIVE boards={seed_boards}",
        )

        # OAuth + user + boards endpoints were all called.
        called_paths = {u for u in calls}
        check(
            "token + user + boards endpoints called",
            any("oauth/token" in u for u in called_paths)
            and any(u.startswith(pinterest_oauth.PINTEREST_USER_ENDPOINT) for u in called_paths)
            and any(u.startswith(pinterest_oauth.PINTEREST_BOARDS_ENDPOINT) for u in called_paths),
            str(sorted(called_paths)),
        )

        connection_id = connection["connection_id"]
        conn.close()

        # --------------------------------------------------------
        # 8. Safe /accounts response (no credentials)
        # --------------------------------------------------------
        groups = fetch_accounts()
        serialized = json.dumps(groups)
        leaked_values = [
            value
            for value in (
                FAKE_TOKEN_PAYLOAD["access_token"],
                FAKE_TOKEN_PAYLOAD["refresh_token"],
            )
            if value in serialized
        ]
        check(
            "no token values in /accounts read model",
            not leaked_values,
            f"leaked: {leaked_values}",
        )

        all_accounts = [
            account for group in groups for account in group["accounts"]
        ]
        credential_fields = [
            "credential_value",
            "access_token",
            "refresh_token",
            "token",
            "api_key",
            "secret",
            "client_secret",
        ]
        leaked_fields = [
            field
            for field in credential_fields
            if any(field in account for account in all_accounts)
        ]
        check(
            "no credential fields in /accounts read model",
            not leaked_fields,
            f"leaked: {leaked_fields}",
        )

        connected = next(
            a for a in all_accounts if a["username"] == FAKE_USER_PAYLOAD["username"]
        )
        check(
            "connected real account visible with safe metadata",
            connected["connection_status"] == CONNECTION_CONNECTED
            and connected["is_seed"] is False
            and connected["display_name"] == FAKE_USER_PAYLOAD["username"]
            and connected["connected_at"] is not None,
            str(connected),
        )

        # --------------------------------------------------------
        # 9. Duplicate connection handling (reconnect reuses)
        # --------------------------------------------------------
        handler, _ = make_fake_http()
        with mock.patch.object(pinterest_oauth, "_http_request", handler):
            second_flow = run_full_flow(code="auth-code-2")

        check(
            "reconnect reuses the same connection",
            second_flow["connection"]["connection_id"] == connection_id,
            f"{second_flow['connection']['connection_id']} != {connection_id}",
        )

        conn = open_db(db_path)
        account_count = conn.execute(
            "SELECT COUNT(*) AS n FROM pinterest_accounts"
            " WHERE pinterest_user_id = ?",
            (FAKE_USER_PAYLOAD["id"],),
        ).fetchone()["n"]
        connection_count = conn.execute(
            "SELECT COUNT(*) AS n FROM account_connections"
            " WHERE provider = 'PINTEREST' AND pinterest_account_id = ?"
            " AND connection_status = ?",
            (real_account["account_id"], CONNECTION_CONNECTED),
        ).fetchone()["n"]
        check(
            "no duplicate accounts or connections on reconnect",
            account_count == 1 and connection_count == 1,
            f"accounts={account_count} connections={connection_count}",
        )

        # --------------------------------------------------------
        # 10. Board synchronization dedupe + removal handling
        # --------------------------------------------------------
        reduced_boards = {
            "items": [
                {"id": "board_real_1", "name": "Real Board One", "privacy": "PUBLIC"},
            ],
            "bookmark": None,
        }
        handler, _ = make_fake_http(boards_payload=reduced_boards)
        with mock.patch.object(pinterest_oauth, "_http_request", handler):
            third_flow = run_full_flow(code="auth-code-3")

        check(
            "re-sync returns updated board count",
            third_flow["boards_synced"] == 1,
            str(third_flow["boards_synced"]),
        )

        conn = open_db(db_path)
        real_board_rows = conn.execute(
            "SELECT board_id, board_name, status, pinterest_board_id"
            " FROM pinterest_boards"
            " WHERE account_id = ? AND pinterest_board_id IS NOT NULL"
            " ORDER BY board_id",
            (real_account["account_id"],),
        ).fetchall()
        check(
            "re-sync does not duplicate boards",
            len(real_board_rows) == 2,
            f"real board rows={len(real_board_rows)}",
        )
        statuses = {r["pinterest_board_id"]: r["status"] for r in real_board_rows}
        check(
            "removed Pinterest board marked INACTIVE",
            statuses.get("board_real_1") == "ACTIVE"
            and statuses.get("board_real_2") == "INACTIVE",
            str(statuses),
        )
        seed_boards_after = conn.execute(
            "SELECT COUNT(*) AS n FROM pinterest_boards"
            " WHERE pinterest_board_id IS NULL AND status = 'ACTIVE'"
        ).fetchone()["n"]
        check(
            "seed boards still untouched after re-sync",
            seed_boards_after == 5,
            f"seed ACTIVE boards={seed_boards_after}",
        )
        conn.close()

        # --------------------------------------------------------
        # 11. Partial failure when board sync fails
        # --------------------------------------------------------
        handler, _ = make_fake_http(boards_status=500)
        with mock.patch.object(pinterest_oauth, "_http_request", handler):
            partial = run_full_flow(code="auth-code-4")

        check(
            "board sync failure reports partial success",
            partial["status"] == "partial",
            str(partial["status"]),
        )
        check(
            "partial failure still marks connection CONNECTED",
            partial["connection"]["connection_status"] == CONNECTION_CONNECTED,
            str(partial["connection"]["connection_status"]),
        )

        # --------------------------------------------------------
        # 12. Disconnect
        # --------------------------------------------------------
        disconnected = disconnect_pinterest_connection(connection_id)
        check(
            "disconnect marks DISCONNECTED",
            disconnected is not None
            and disconnected["connection_status"] == CONNECTION_DISCONNECTED,
            str(disconnected),
        )
        check(
            "disconnect preserves safe metadata",
            disconnected["username"] == FAKE_USER_PAYLOAD["username"]
            and disconnected["connected_at"] is None,
            str(disconnected),
        )
        check(
            "disconnect removes stored credentials",
            fetch_connection_credentials(connection_id) == {},
            str(fetch_connection_credentials(connection_id)),
        )

        # Reconnecting after disconnect reuses the same connection.
        handler, _ = make_fake_http()
        with mock.patch.object(pinterest_oauth, "_http_request", handler):
            reconnect = run_full_flow(code="auth-code-5")
        check(
            "reconnect after disconnect reuses connection id",
            reconnect["connection"]["connection_id"] == connection_id,
            str(reconnect["connection"]["connection_id"]),
        )

        # --------------------------------------------------------
        # 13. Seed protection
        # --------------------------------------------------------
        try:
            upsert_real_pinterest_account(
                {"id": "999", "username": "atlashome"}
            )
            check(
                "seed account never converted to real",
                False,
                "upsert succeeded",
            )
        except sqlite3.Error:
            check("seed account never converted to real", True)

        seed_conn = open_db(db_path)
        seed_connection_id = seed_conn.execute(
            "SELECT connection_id FROM account_connections"
            " WHERE is_seed = 1 LIMIT 1"
        ).fetchone()["connection_id"]
        seed_conn.close()

        try:
            disconnect_pinterest_connection(seed_connection_id)
            check("seed connection cannot be disconnected", False, "succeeded")
        except ValueError:
            check("seed connection cannot be disconnected", True)

        # --------------------------------------------------------
        # 14. Token refresh
        # --------------------------------------------------------
        refreshed_payload = {
            "access_token": "pina_refreshed_token",
            "refresh_token": "pinr_rotated_token",
            "token_type": "bearer",
            "expires_in": 3600,
            "scope": "user_accounts:read boards:read pins:read pins:write",
        }

        def refresh_handler(
            url: str,
            *,
            method: str = "GET",
            headers: dict[str, str] | None = None,
            data: bytes | None = None,
        ) -> tuple[int, object]:
            if "oauth/token" in url:
                return 200, refreshed_payload
            return 500, {}

        with mock.patch.object(pinterest_oauth, "_http_request", refresh_handler):
            refreshed = refresh_access_token("pinr_stored_token", scope="boards:read")

        check(
            "refresh grant returns new access token",
            refreshed["access_token"] == "pina_refreshed_token"
            and refreshed["refresh_token"] == "pinr_rotated_token",
            str(refreshed),
        )

        with mock.patch.object(pinterest_oauth, "_http_request", refresh_handler):
            stored = refresh_stored_pinterest_credentials(connection_id)

        check(
            "stored credentials refreshed server-side",
            stored["access_token"] == "pina_refreshed_token",
            str(list(stored.keys())),
        )
        refreshed_credentials = fetch_connection_credentials(connection_id)
        check(
            "rotated refresh token persisted",
            refreshed_credentials.get(CREDENTIAL_PINTEREST_REFRESH_TOKEN)
            == "pinr_rotated_token",
            str(list(refreshed_credentials.keys())),
        )

        # No refresh token stored -> clear error.
        no_token_connection = disconnect_pinterest_connection(connection_id)
        check(
            "disconnect (again) leaves no credentials",
            no_token_connection["connection_status"] == CONNECTION_DISCONNECTED,
        )
        try:
            refresh_stored_pinterest_credentials(connection_id)
            check(
                "refresh without stored token fails safely",
                False,
                "no error raised",
            )
        except ValueError:
            check("refresh without stored token fails safely", True)

        # --------------------------------------------------------
        # 15. API endpoints (FastAPI TestClient)
        # --------------------------------------------------------
        from fastapi.testclient import TestClient

        import atlas_api as api

        client = TestClient(api.app)

        # Connect endpoint with configuration missing.
        os.environ.pop("PINTEREST_CLIENT_ID", None)
        os.environ.pop("PINTEREST_CLIENT_SECRET", None)
        os.environ.pop("PINTEREST_REDIRECT_URI", None)
        response = client.get("/accounts/pinterest/connect")
        check(
            "GET connect returns 503 when config missing",
            response.status_code == 503,
            str(response.status_code),
        )

        os.environ["PINTEREST_CLIENT_ID"] = "test-client-id"
        os.environ["PINTEREST_CLIENT_SECRET"] = "test-client-secret"
        os.environ["PINTEREST_REDIRECT_URI"] = "https://example.com/api/accounts/pinterest/callback"

        response = client.get("/accounts/pinterest/connect")
        check(
            "GET connect returns authorization URL",
            response.status_code == 200
            and "authorization_url" in response.json(),
            f"{response.status_code} {response.text[:120]}",
        )

        # Callback: success (mocked HTTP).
        handler, _ = make_fake_http()
        with mock.patch.object(pinterest_oauth, "_http_request", handler):
            state = generate_oauth_state()
            store_oauth_state(state)
            response = client.get(
                "/accounts/pinterest/callback",
                params={"state": state, "code": "endpoint-code"},
                follow_redirects=False,
            )
        check(
            "callback redirects to success",
            response.status_code == 302
            and "/accounts?pinterest=success" in response.headers["location"],
            f"{response.status_code} {response.headers.get('location')}",
        )

        # Callback: user denial.
        state = generate_oauth_state()
        store_oauth_state(state)
        response = client.get(
            "/accounts/pinterest/callback",
            params={"state": state, "error": "access_denied"},
            follow_redirects=False,
        )
        check(
            "callback redirects on user denial",
            response.status_code == 302
            and "/accounts?pinterest=denied" in response.headers["location"],
            f"{response.status_code} {response.headers.get('location')}",
        )

        # Callback: invalid state.
        response = client.get(
            "/accounts/pinterest/callback",
            params={"state": "not-a-real-state", "code": "x"},
            follow_redirects=False,
        )
        check(
            "callback redirects on invalid state",
            response.status_code == 302
            and "/accounts?pinterest=error" in response.headers["location"]
            and "reason=state" in response.headers["location"],
            f"{response.status_code} {response.headers.get('location')}",
        )

        # Callback redirect must never leak tokens.
        handler, _ = make_fake_http()
        with mock.patch.object(pinterest_oauth, "_http_request", handler):
            state = generate_oauth_state()
            store_oauth_state(state)
            response = client.get(
                "/accounts/pinterest/callback",
                params={"state": state, "code": "leak-check"},
                follow_redirects=False,
            )
        location = response.headers["location"]
        check(
            "callback redirect contains no token/code values",
            "pina_fake" not in location
            and "pinr_fake" not in location
            and "leak-check" not in location,
            location,
        )

        # GET /accounts reflects the real connected account.
        response = client.get("/accounts")
        payload = response.json()
        pinterest = next(g for g in payload if g["provider"] == "PINTEREST")
        connected_accounts = [
            a for a in pinterest["accounts"] if a["username"] == FAKE_USER_PAYLOAD["username"]
        ]
        check(
            "GET /accounts shows real connected account",
            response.status_code == 200
            and connected_accounts
            and connected_accounts[0]["connection_status"] == CONNECTION_CONNECTED
            and connected_accounts[0]["is_seed"] is False,
            str(connected_accounts),
        )

        # Disconnect endpoint.
        response = client.post(
            "/accounts/pinterest/disconnect",
            json={"connection_id": connection_id},
        )
        check(
            "POST disconnect returns DISCONNECTED row",
            response.status_code == 200
            and response.json()["connection_status"] == CONNECTION_DISCONNECTED,
            f"{response.status_code} {response.text[:160]}",
        )

        response = client.post(
            "/accounts/pinterest/disconnect",
            json={"connection_id": 999999},
        )
        check(
            "POST disconnect returns 404 for unknown connection",
            response.status_code == 404,
            str(response.status_code),
        )

        response = client.post(
            "/accounts/pinterest/disconnect",
            json={"connection_id": seed_connection_id},
        )
        check(
            "POST disconnect refuses seed connections",
            response.status_code == 409,
            f"{response.status_code} {response.text[:160]}",
        )

        # GET /accounts response never contains credential-shaped strings.
        response = client.get("/accounts")
        serialized_api = response.text
        check(
            "GET /accounts body has no credential-shaped strings",
            "pina_" not in serialized_api
            and "pinr_" not in serialized_api
            and "test-client-secret" not in serialized_api,
            "credential-like string present",
        )
    finally:
        database_module.DATABASE_PATH = original_path
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    print()

    if failures:
        print(f"FAILED ({len(failures)}):")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)

    print("All Pinterest OAuth checks passed.")


if __name__ == "__main__":
    main()
