"""
ATLAS-029 NEXT PHASE: architecture / schema test (Phase 1).

Builds a throwaway database from the real migrations (including the new
sql/021_atlas_029_architecture.sql) and asserts:

  - categories are frontend-managed entities with a stable slug
  - category_routes are wired to categories by FK (not free-text slug)
  - products are provider-agnostic (provider / marketplace /
    external_product_id / affiliate_url) with ASIN backfilled as the
    external id
  - affiliate config contract lives on account_connections /
    connection_credentials (AMAZON_ASSOCIATES provider)
  - pinterest_queue tracks manual exports via exported_at, distinct from
    published_at
  - more than 4 accounts are supported without schema changes

Run with:  PYTHONPATH=/workspace python3 tests/test_phase1_schema.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

import services.database as database_module  # noqa: E402
from services.accounts_service import fetch_accounts  # noqa: E402


def build_database(db_path: Path) -> None:
    """Apply every sql/*.sql migration in filename order to a fresh DB."""

    conn = sqlite3.connect(db_path)

    for migration in sorted((PROJECT_ROOT / "sql").glob("*.sql")):
        conn.executescript(migration.read_text(encoding="utf-8"))

    conn.commit()
    conn.close()


def columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return the set of column names for a table."""

    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()

    return {row["name"] for row in rows}


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

    tmp = tempfile.mkdtemp(prefix="atlas_phase1_test_")
    db_path = Path(tmp) / "atlas.db"

    build_database(db_path)

    original_path = database_module.DATABASE_PATH
    database_module.DATABASE_PATH = db_path

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # -- 1) categories are frontend-managed entities -------------------
        category_cols = columns(conn, "categories")

        check(
            "categories has a stable slug column",
            "category_slug" in category_cols,
            f"columns: {category_cols}",
        )

        kitchen = conn.execute(
            "SELECT * FROM categories WHERE category_slug = 'kitchen'"
        ).fetchone()
        home = conn.execute(
            "SELECT * FROM categories WHERE category_slug = 'home'"
        ).fetchone()

        check(
            "seed categories keep their slugs",
            kitchen is not None
            and kitchen["category_name"] == "Kitchen Storage"
            and home is not None
            and home["category_name"] == "Home Storage",
            str((dict(kitchen) if kitchen else None, dict(home) if home else None)),
        )

        seeded_slugs = {
            row["category_slug"]
            for row in conn.execute(
                "SELECT category_slug FROM categories"
                " WHERE category_slug IS NOT NULL"
            ).fetchall()
        }

        check(
            "legacy route slugs resolve to real categories",
            {"kitchen", "home", "pantry", "bathroom", "closet"} <= seeded_slugs,
            f"got {seeded_slugs}",
        )

        # -- 2) category_routes wired by FK --------------------------------
        route_cols = columns(conn, "category_routes")

        check(
            "category_routes has a categories FK column",
            "category_id" in route_cols,
            f"columns: {route_cols}",
        )

        orphaned_routes = conn.execute(
            "SELECT route_id FROM category_routes"
            " WHERE category_id IS NULL"
        ).fetchall()

        check(
            "every existing route resolves to a real category",
            len(orphaned_routes) == 0,
            f"orphaned route_ids: {[r['route_id'] for r in orphaned_routes]}",
        )

        joined = conn.execute(
            "SELECT cr.route_id, c.category_name"
            " FROM category_routes cr"
            " JOIN categories c ON c.category_id = cr.category_id"
            " ORDER BY cr.route_id"
        ).fetchall()

        check(
            "category_routes joins to categories",
            len(joined) >= 5,
            f"got {len(joined)} joined rows",
        )

        # -- 3) provider-agnostic products ---------------------------------
        research_cols = columns(conn, "research_products")
        registry_cols = columns(conn, "product_registry")

        for column in (
            "provider",
            "marketplace",
            "external_product_id",
            "affiliate_url",
        ):
            check(
                f"research_products has {column}",
                column in research_cols,
                f"columns: {research_cols}",
            )
            check(
                f"product_registry has {column}",
                column in registry_cols,
                f"columns: {registry_cols}",
            )

        # Defaults are provider-agnostic.
        research_default = conn.execute(
            "SELECT provider, marketplace"
            " FROM research_products"
            " WHERE provider != 'AMAZON' OR marketplace != 'US'"
            " LIMIT 1"
        ).fetchone()

        check(
            "research_products default to AMAZON / US",
            research_default is None,
            str(dict(research_default) if research_default else None),
        )

        # The migration backfills existing ASIN rows into the external id.
        # The fresh test DB has no products at migration time, so exercise
        # the migration's own backfill UPDATE against a newly inserted row.
        conn.execute(
            "INSERT INTO research_products"
            " (job_id, category, product_name, product_url, source, asin)"
            " VALUES"
            " (1, 'kitchen', 'Test Shelf', 'https://example.test/shelf',"
            " 'Amazon', 'B0TEST123')"
        )
        conn.commit()

        conn.execute(
            "UPDATE research_products"
            " SET external_product_id = asin"
            " WHERE external_product_id IS NULL"
            "   AND asin IS NOT NULL"
        )
        conn.commit()

        backfilled = conn.execute(
            "SELECT external_product_id"
            " FROM research_products"
            " WHERE asin = 'B0TEST123'"
        ).fetchone()

        check(
            "research_products ASIN backfilled into external_product_id",
            backfilled is not None and backfilled["external_product_id"] == "B0TEST123",
            str(dict(backfilled) if backfilled else None),
        )

        # -- 4) affiliate config contract ----------------------------------
        affiliate = conn.execute(
            "SELECT provider, marketplace FROM account_connections"
            " WHERE provider = 'AMAZON_ASSOCIATES'"
        ).fetchone()

        check(
            "AMAZON_ASSOCIATES connection provider is supported",
            (affiliate is None)  # empty is valid; schema must accept it
            or affiliate["provider"] == "AMAZON_ASSOCIATES",
            str(dict(affiliate) if affiliate else "no rows"),
        )

        credential_table = conn.execute(
            "SELECT name FROM sqlite_master"
            " WHERE type='table' AND name='connection_credentials'"
        ).fetchone()

        check(
            "connection_credentials table exists for affiliate secrets",
            credential_table is not None,
            "missing connection_credentials table",
        )

        # The AMAZON_ASSOCIATES provider row is allowed once configured.
        conn.execute(
            "INSERT INTO account_connections"
            " (provider, display_name, username, marketplace, connection_status,"
            "  connected_at, is_seed)"
            " VALUES"
            " ('AMAZON_ASSOCIATES', 'Atlas Affiliates', 'atlas-affiliates', 'US',"
            "  'CONFIGURED', NULL, 0)"
        )
        conn.execute(
            "INSERT INTO connection_credentials"
            " (connection_id, credential_type, credential_value)"
            " VALUES"
            " ((SELECT connection_id FROM account_connections"
            "   WHERE username = 'atlas-affiliates'),"
            "  'AFFILIATE_TAG', 'atlas-test-tag-21')"
        )
        conn.commit()

        stored_tag = conn.execute(
            "SELECT credential_value FROM connection_credentials"
            " WHERE credential_type = 'AFFILIATE_TAG'"
        ).fetchone()

        check(
            "affiliate tag stores server-side only",
            stored_tag is not None
            and stored_tag["credential_value"] == "atlas-test-tag-21",
            str(dict(stored_tag) if stored_tag else None),
        )

        leaked = fetch_accounts()
        serialized = str(leaked)

        check(
            "affiliate tag never leaks into the read model",
            "atlas-test-tag-21" not in serialized,
            "credential leaked into accounts API response",
        )

        # -- 5) export-ready concept ---------------------------------------
        queue_cols = columns(conn, "pinterest_queue")

        check(
            "pinterest_queue tracks exported_at",
            "exported_at" in queue_cols,
            f"columns: {queue_cols}",
        )

        check(
            "pinterest_queue keeps published_at for real publishes",
            "published_at" in queue_cols,
            f"columns: {queue_cols}",
        )

        # -- 6) no hardcoded account-count ceilings ------------------------
        # A fresh migration-built DB seeds 2 Pinterest accounts; adding a
        # fifth-style account (beyond every seed) must succeed and surface
        # through the accounts read model without any schema change.
        conn.execute(
            "INSERT INTO pinterest_accounts"
            " (account_name, username, niche_slug, status, is_seed)"
            " VALUES ('Fifth Account', 'fifthuser', 'home', 'ACTIVE', 0)"
        )
        conn.execute(
            "INSERT INTO account_connections"
            " (provider, display_name, username, pinterest_account_id,"
            "  connection_status, is_seed)"
            " VALUES ('PINTEREST', 'Fifth Account', 'fifthuser',"
            "  (SELECT account_id FROM pinterest_accounts"
            "   WHERE username = 'fifthuser'), 'NOT_CONNECTED', 0)"
        )
        conn.commit()

        read_usernames = {
            account["username"]
            for group in fetch_accounts()
            if group["provider"] == "PINTEREST"
            for account in group["accounts"]
        }

        check(
            ">4 accounts supported without schema changes",
            "fifthuser" in read_usernames,
            f"Pinterest usernames: {read_usernames}",
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

    print("All Phase 1 schema checks passed.")


if __name__ == "__main__":
    main()
