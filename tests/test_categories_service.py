"""
ATLAS-029 NEXT PHASE: categories service test (Phase 2).

Builds a throwaway database from the real migrations and asserts the
categories service:

  - lists categories with route counts (frontend-managed, not hardcoded)
  - creates categories (auto-slug), rejecting duplicate names and slugs
  - edits categories and keeps the legacy route slug in sync
  - archives / activates categories
  - reads category routes with account + board detail (Pinterest board
    IDs surfaced when available; seed flags preserved)
  - adds routes with validation (board must belong to the account,
    no duplicates)
  - supports any number of categories / accounts / boards

Run with:  PYTHONPATH=/workspace python3 tests/test_categories_service.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

import services.database as database_module  # noqa: E402
from services.categories_service import (  # noqa: E402
    add_category_route,
    create_category,
    fetch_category,
    list_categories,
    list_category_routes,
    set_category_status,
    update_category,
    update_category_route,
)


def build_database(db_path: Path) -> None:
    """Apply every sql/*.sql migration in filename order to a fresh DB."""

    conn = sqlite3.connect(db_path)

    for migration in sorted((PROJECT_ROOT / "sql").glob("*.sql")):
        conn.executescript(migration.read_text(encoding="utf-8"))

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

    tmp = tempfile.mkdtemp(prefix="atlas_categories_test_")
    db_path = Path(tmp) / "atlas.db"

    build_database(db_path)

    original_path = database_module.DATABASE_PATH
    database_module.DATABASE_PATH = db_path

    try:
        # -- list -----------------------------------------------------------
        categories = list_categories()

        check(
            "seed categories listed with counts",
            len(categories) >= 2
            and categories[0]["category_name"] == "Kitchen Storage"
            and categories[0]["status"] == "ACTIVE"
            and "active_routes" in categories[0],
            str(categories),
        )

        # -- create ---------------------------------------------------------
        created = create_category("Coffee Corner", priority=7, daily_target=3)

        check(
            "create auto-derives a slug",
            fetch_category(created)["category_slug"] == "coffee_corner",
            str(fetch_category(created)),
        )

        duplicate_name = False
        try:
            create_category("Coffee Corner")
        except ValueError:
            duplicate_name = True

        check(
            "duplicate category name rejected",
            duplicate_name,
            "expected ValueError for duplicate name",
        )

        duplicate_slug = False
        try:
            create_category("Other", slug="coffee_corner")
        except ValueError:
            duplicate_slug = True

        check(
            "duplicate category slug rejected",
            duplicate_slug,
            "expected ValueError for duplicate slug",
        )

        # -- edit -----------------------------------------------------------
        edited = update_category(created, name="Coffee & Kitchen", priority=9)

        check(
            "edit updates fields",
            edited is not None
            and edited["category_name"] == "Coffee & Kitchen"
            and edited["priority"] == 9,
            str(edited),
        )

        # Editing a slug keeps legacy category_routes.category_slug in sync.
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO category_routes (category_id, category_slug,"
            " account_id, board_id, priority)"
            " VALUES (?, 'coffee_corner', 1, 1, 1)",
            (created,),
        )
        conn.commit()
        conn.close()

        update_category(created, slug="coffee")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        synced = conn.execute(
            "SELECT category_slug FROM category_routes WHERE category_id = ?",
            (created,),
        ).fetchone()["category_slug"]
        conn.close()

        check(
            "legacy route slug kept in sync on rename",
            synced == "coffee",
            f"route slug is {synced!r}",
        )

        # -- archive / activate ---------------------------------------------
        archived = set_category_status(created, "INACTIVE")

        check(
            "archive sets status INACTIVE",
            archived is not None and archived["status"] == "INACTIVE",
            str(archived),
        )

        activated = set_category_status(created, "ACTIVE")

        check(
            "activate restores status ACTIVE",
            activated is not None and activated["status"] == "ACTIVE",
            str(activated),
        )

        # -- routes: read ---------------------------------------------------
        routes = list_category_routes(1)

        check(
            "seed routes carry account and board detail",
            len(routes) >= 1
            and routes[0]["account_name"]
            and routes[0]["board_name"]
            and routes[0]["is_seed"] is True
            and routes[0]["connection_status"] == "NOT_CONNECTED",
            str(routes),
        )

        check(
            "route detail exposes Pinterest board id field",
            all("pinterest_board_id" in route for route in routes),
            str(routes),
        )

        # -- routes: create + validation ------------------------------------
        wrong_board = False
        try:
            add_category_route(1, account_id=1, board_id=4)
        except ValueError:
            wrong_board = True

        check(
            "board must belong to the selected account",
            wrong_board,
            "expected ValueError for cross-account board",
        )

        duplicate_route = False
        try:
            add_category_route(1, account_id=1, board_id=2)
        except ValueError:
            duplicate_route = True

        check(
            "duplicate route rejected",
            duplicate_route,
            "expected ValueError for duplicate route",
        )

        new_route = add_category_route(1, account_id=2, board_id=4, priority=2)

        check(
            "route added across a second account",
            new_route > 0,
            f"route_id={new_route}",
        )

        # -- routes: edit / archive / restore --------------------------------
        archived_route = update_category_route(new_route, status="INACTIVE")

        check(
            "route archived",
            archived_route is not None
            and archived_route["route_status"] == "INACTIVE",
            str(archived_route),
        )

        restored_route = update_category_route(new_route, status="ACTIVE")

        check(
            "route restored",
            restored_route is not None
            and restored_route["route_status"] == "ACTIVE",
            str(restored_route),
        )

        missing_route = update_category_route(99999, priority=1)

        check(
            "unknown route returns None",
            missing_route is None,
            str(missing_route),
        )

        # -- scale: no hardcoded limits --------------------------------------
        for index in range(5):
            account = sqlite3.connect(db_path)
            account.execute(
                "INSERT INTO pinterest_accounts (account_name, username,"
                " niche_slug, status, is_seed)"
                " VALUES (?, ?, 'home', 'ACTIVE', 0)",
                (f"Account {index}", f"user{index}"),
            )
            account.commit()
            account.close()

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        account_count = conn.execute(
            "SELECT COUNT(*) AS n FROM pinterest_accounts"
        ).fetchone()["n"]
        conn.close()

        check(
            "many accounts supported without schema changes",
            account_count > 6,
            f"got {account_count} accounts",
        )

    finally:
        database_module.DATABASE_PATH = original_path

    print()

    if failures:
        print(f"FAILED ({len(failures)}):")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)

    print("All categories service checks passed.")


if __name__ == "__main__":
    main()
