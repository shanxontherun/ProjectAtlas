"""
ATLAS-029 NEXT PHASE: categories API test (Phase 2).

Builds a throwaway database from the real migrations, points the API at it
and exercises the Phase 2 HTTP endpoints with FastAPI TestClient:

  - GET  /categories
  - POST /categories (create, duplicates rejected)
  - GET/PATCH /categories/{id}
  - POST /categories/{id}/archive and /activate
  - GET/POST /categories/{id}/routes, PATCH /categories/{id}/routes/{id}
  - GET /boards (with Pinterest board ids)
  - GET /accounts/{id}/boards

Runs from the repo root:  PYTHONPATH=/workspace python3 tests/test_categories_api.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = PROJECT_ROOT / "services"

# atlas_api imports `from database import ...`, which only resolves when the
# services directory precedes the repo root on sys.path (the documented way
# the backend is started). Insert it first so both the top-level `database`
# module and `services.database` point at the same file.
sys.path.insert(0, str(SERVICES_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

import database as top_level_database  # noqa: E402
import services.database as services_database  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from atlas_api import app  # noqa: E402


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

    tmp = tempfile.mkdtemp(prefix="atlas_categories_api_")
    db_path = Path(tmp) / "atlas.db"

    build_database(db_path)

    original_paths = (
        services_database.DATABASE_PATH,
        top_level_database.DATABASE_PATH,
    )

    services_database.DATABASE_PATH = db_path
    top_level_database.DATABASE_PATH = db_path

    try:
        client = TestClient(app)

        # -- list -----------------------------------------------------------
        response = client.get("/categories")
        categories = response.json()

        check(
            "GET /categories returns 200 with seed categories",
            response.status_code == 200
            and len(categories) >= 2
            and categories[0]["category_name"] == "Kitchen Storage",
            f"status={response.status_code} body={categories}",
        )

        # -- create ---------------------------------------------------------
        created = client.post(
            "/categories",
            json={
                "name": "Outdoor Living",
                "priority": 6,
                "daily_target": 4,
            },
        )
        created_body = created.json()

        check(
            "POST /categories creates with auto-slug",
            created.status_code == 201
            and created_body["category_slug"] == "outdoor_living"
            and created_body["status"] == "ACTIVE",
            f"status={created.status_code} body={created_body}",
        )

        category_id = created_body["category_id"]

        duplicate = client.post(
            "/categories",
            json={"name": "Outdoor Living"},
        )

        check(
            "duplicate category rejected with 409",
            duplicate.status_code == 409,
            f"status={duplicate.status_code} body={duplicate.json()}",
        )

        # -- detail + edit --------------------------------------------------
        detail = client.get(f"/categories/{category_id}")

        check(
            "GET /categories/{id} returns the category",
            detail.status_code == 200
            and detail.json()["category_id"] == category_id,
            f"status={detail.status_code}",
        )

        edited = client.patch(
            f"/categories/{category_id}",
            json={"name": "Outdoor Living & Garden", "priority": 8},
        )

        check(
            "PATCH /categories/{id} edits fields",
            edited.status_code == 200
            and edited.json()["priority"] == 8,
            f"status={edited.status_code} body={edited.json()}",
        )

        missing = client.get("/categories/999999")

        check(
            "unknown category returns 404",
            missing.status_code == 404,
            f"status={missing.status_code}",
        )

        # -- archive / activate ---------------------------------------------
        archived = client.post(f"/categories/{category_id}/archive")

        check(
            "archive returns INACTIVE",
            archived.status_code == 200
            and archived.json()["status"] == "INACTIVE",
            f"status={archived.status_code} body={archived.json()}",
        )

        activated = client.post(f"/categories/{category_id}/activate")

        check(
            "activate returns ACTIVE",
            activated.status_code == 200
            and activated.json()["status"] == "ACTIVE",
            f"status={activated.status_code} body={activated.json()}",
        )

        # -- boards ----------------------------------------------------------
        boards = client.get("/boards")

        check(
            "GET /boards returns boards with account + Pinterest board id",
            boards.status_code == 200
            and len(boards.json()) >= 5
            and all(
                "board_id" in board and "account_name" in board
                for board in boards.json()
            )
            and all("pinterest_board_id" in board for board in boards.json()),
            f"status={boards.status_code} boards={boards.json()[:2]}",
        )

        account_boards = client.get("/accounts/1/boards")

        check(
            "GET /accounts/{id}/boards filters by account",
            account_boards.status_code == 200
            and len(account_boards.json()) >= 1
            and all(
                board["account_id"] == 1 for board in account_boards.json()
            ),
            f"status={account_boards.status_code} boards={account_boards.json()}",
        )

        # -- routes ----------------------------------------------------------
        routes = client.get("/categories/1/routes")

        check(
            "GET /categories/{id}/routes returns seed routes",
            routes.status_code == 200
            and len(routes.json()) >= 1
            and routes.json()[0]["account_name"] == "Atlas Home"
            and routes.json()[0]["is_seed"] is True,
            f"status={routes.status_code} body={routes.json()}",
        )

        wrong_board = client.post(
            "/categories/1/routes",
            json={"account_id": 1, "board_id": 4, "priority": 1},
        )

        check(
            "cross-account board rejected with 409",
            wrong_board.status_code == 409,
            f"status={wrong_board.status_code} body={wrong_board.json()}",
        )

        added = client.post(
            "/categories/1/routes",
            json={"account_id": 2, "board_id": 4, "priority": 3},
        )

        check(
            "POST /categories/{id}/routes adds a route",
            added.status_code == 201
            and added.json()["account_id"] == 2
            and added.json()["board_id"] == 4,
            f"status={added.status_code} body={added.json()}",
        )

        route_id = added.json()["route_id"]

        route_archived = client.patch(
            f"/categories/1/routes/{route_id}",
            json={"status": "INACTIVE"},
        )

        check(
            "PATCH route archives it",
            route_archived.status_code == 200
            and route_archived.json()["route_status"] == "INACTIVE",
            f"status={route_archived.status_code} body={route_archived.json()}",
        )

        # Active-only listing hides the archived route.
        active_routes = client.get("/categories/1/routes").json()

        check(
            "active route listing excludes archived routes",
            all(
                route["route_id"] != route_id
                for route in active_routes
            ),
            f"active routes: {[r['route_id'] for r in active_routes]}",
        )

        # Invalid input is rejected by the API contract.
        bad_priority = client.post(
            "/categories/1/routes",
            json={"account_id": 1, "board_id": 1, "priority": 0},
        )

        check(
            "priority below 1 rejected with 422",
            bad_priority.status_code == 422,
            f"status={bad_priority.status_code}",
        )

    finally:
        services_database.DATABASE_PATH, top_level_database.DATABASE_PATH = (
            original_paths
        )

    print()

    if failures:
        print(f"FAILED ({len(failures)}):")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)

    print("All categories API checks passed.")


if __name__ == "__main__":
    main()
