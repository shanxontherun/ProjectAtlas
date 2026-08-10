"""
ATLAS-029B Accounts Foundation smoke test.

Builds a throwaway database from the real migrations and asserts the
Accounts read model:
  - is grouped by provider (Pinterest / Amazon Associates / AI)
  - returns SAFE metadata only (no credentials anywhere)
  - never reports CONNECTED for seed accounts
  - keeps is_seed separate from connection_status
  - supports multiple accounts per provider
  - surfaces AI providers from env presence without leaking values

Run with:  PYTHONPATH=/workspace python3 tests/test_accounts_foundation.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

import services.database as database_module  # noqa: E402
from services.accounts_service import (  # noqa: E402
    fetch_accounts,
    fetch_ai_providers,
)
from services.constants import (  # noqa: E402
    CONNECTION_CONFIGURED,
    CONNECTION_NOT_CONFIGURED,
    CONNECTION_NOT_CONNECTED,
)


def build_database(db_path: Path) -> None:
    """Apply every sql/*.sql migration in filename order to a fresh DB."""

    conn = sqlite3.connect(db_path)

    for migration in sorted((PROJECT_ROOT / "sql").glob("*.sql")):
        conn.executescript(
            migration.read_text(encoding="utf-8")
        )

    conn.commit()
    conn.close()


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

    tmp = tempfile.mkdtemp(prefix="atlas_accounts_test_")
    db_path = Path(tmp) / "atlas.db"

    build_database(db_path)

    original_path = database_module.DATABASE_PATH
    database_module.DATABASE_PATH = db_path

    try:
        groups = fetch_accounts()
        providers = [g["provider"] for g in groups]

        check(
            "providers grouped in order",
            providers == ["PINTEREST", "AMAZON_ASSOCIATES", "AI"],
            f"got {providers}",
        )

        pinterest = next(g for g in groups if g["provider"] == "PINTEREST")
        pinterest_accounts = pinterest["accounts"]

        check(
            "multiple Pinterest accounts supported",
            len(pinterest_accounts) >= 2,
            f"got {len(pinterest_accounts)}",
        )

        check(
            "seed Pinterest accounts are NOT_CONNECTED",
            all(
                a["connection_status"] == CONNECTION_NOT_CONNECTED
                and a["is_seed"] is True
                for a in pinterest_accounts
            ),
            str(pinterest_accounts),
        )

        check(
            "no Pinterest account claims CONNECTED",
            all(a["connection_status"] != "CONNECTED" for a in pinterest_accounts),
            str(pinterest_accounts),
        )

        amazon = next(g for g in groups if g["provider"] == "AMAZON_ASSOCIATES")

        check(
            "Amazon Associates is empty (nothing configured)",
            amazon["accounts"] == [],
            str(amazon["accounts"]),
        )

        # A non-seed Pinterest account is NOT automatically connected.
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO pinterest_accounts (account_name, username, niche_slug, status, is_seed)"
            " VALUES ('Real Account', 'realuser', 'home', 'ACTIVE', 0)"
        )
        conn.execute(
            "INSERT INTO account_connections"
            " (provider, display_name, username, pinterest_account_id, connection_status, is_seed)"
            " VALUES ('PINTEREST', 'Real Account', 'realuser',"
            " (SELECT account_id FROM pinterest_accounts WHERE username='realuser'),"
            " 'NOT_CONNECTED', 0)"
        )
        conn.commit()
        conn.close()

        refresh = fetch_accounts()
        pinterest_refresh = next(
            g for g in refresh if g["provider"] == "PINTEREST"
        )["accounts"]
        real = next(a for a in pinterest_refresh if a["username"] == "realuser")

        check(
            "non-seed account is NOT automatically connected",
            real["connection_status"] == CONNECTION_NOT_CONNECTED
            and real["is_seed"] is False,
            str(real),
        )

        # AI providers: no env -> nothing configured.
        os.environ.pop("AI_BASE_URL", None)
        os.environ.pop("AI_API_KEY", None)
        os.environ.pop("AI_MODEL", None)

        ai = fetch_ai_providers()

        check(
            "AI providers listed without env",
            {a["display_name"] for a in ai} == {"OpenRouter", "Gemini", "OpenAI"},
            str([a["display_name"] for a in ai]),
        )

        check(
            "AI providers NOT_CONFIGURED without env",
            all(
                a["connection_status"] == CONNECTION_NOT_CONFIGURED
                for a in ai
            ),
            str([(a["display_name"], a["connection_status"]) for a in ai]),
        )

        # AI providers: env present -> matching provider CONFIGURED.
        os.environ["AI_BASE_URL"] = "https://openrouter.ai/api/v1"
        os.environ["AI_API_KEY"] = "placeholder-test-key"
        os.environ["AI_MODEL"] = "placeholder-test-model"

        ai_configured = fetch_ai_providers()

        check(
            "matching AI provider CONFIGURED with env",
            next(
                a
                for a in ai_configured
                if a["display_name"] == "OpenRouter"
            )["connection_status"]
            == CONNECTION_CONFIGURED,
            str(
                [
                    (a["display_name"], a["connection_status"])
                    for a in ai_configured
                ]
            ),
        )

        check(
            "non-matching AI providers stay NOT_CONFIGURED",
            all(
                a["connection_status"] == CONNECTION_NOT_CONFIGURED
                for a in ai_configured
                if a["display_name"] != "OpenRouter"
            ),
            str(
                [
                    (a["display_name"], a["connection_status"])
                    for a in ai_configured
                ]
            ),
        )

        # Security: serialized payload must never contain credential fields.
        all_accounts = [
            account
            for group in fetch_accounts()
            for account in group["accounts"]
        ]
        credential_fields = [
            "credential_value",
            "api_key",
            "access_token",
            "refresh_token",
            "token",
            "associate_tag",
            "secret",
        ]

        leaked = [
            field
            for field in credential_fields
            if any(field in account for account in all_accounts)
        ]

        check(
            "no credential fields in the read model",
            not leaked,
            f"leaked: {leaked}",
        )

        conn = sqlite3.connect(db_path)
        credential_table = conn.execute(
            "SELECT name FROM sqlite_master"
            " WHERE type='table' AND name='connection_credentials'"
        ).fetchone()

        check(
            "connection_credentials table exists (server-side only)",
            credential_table is not None,
            "missing connection_credentials table",
        )
        conn.close()
    finally:
        database_module.DATABASE_PATH = original_path

    print()

    if failures:
        print(f"FAILED ({len(failures)}):")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)

    print("All accounts foundation checks passed.")


if __name__ == "__main__":
    main()
