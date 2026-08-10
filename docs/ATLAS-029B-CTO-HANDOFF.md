# ATLAS-029B — CTO Handoff / Accounts Foundation Architecture Context

> Handoff for the next engineer. ATLAS-029A (Publishing Stabilization) is
> complete. This document captures the important decisions and discoveries so
> you can start ATLAS-029B **without** access to the previous conversation.
> Read it fully before writing code.

---

## 1. ATLAS-029A Outcome

ATLAS-029 delivered a fully backend-driven Publishing Center (queue, schedule,
publish-now, published history, boards, summary cards, Download Pin) wired to
FastAPI through TanStack Query. ATLAS-029A made that system **honest** about
the difference between real external publishing and development/test data:

- Published / history / summary counts now come **only** from **real**
  (non-seed) Pinterest accounts.
- When no real Pinterest connection exists, the Publishing dashboard shows:
  - Ready to Publish: 0
  - Scheduled: 0
  - Published: 0
  - Published History: "No Pins published yet"
  - Boards: **"Configured boards"** (never "Connected to Pinterest")
- Publish Now is blocked in the UI (button disabled) and the backend returns
  HTTP 409 `"Connect a Pinterest account before publishing."` when the target
  account is a seed account.
- The publisher worker (`workers/publisher_worker.py`) never attempts to
  publish seed-account queue items.
- Download Pin still works (streams the stored creative image).
- Queue / schedule / remove persistence is unchanged and still works.

Deliverables produced: `docs/ATLAS-029-deliverables.md` (029),
`docs/ATLAS-029A-deliverables.md` (029A + final seed-data cleanup).

---

## 2. Seed-Data Discovery

The local database originally contained two **development/test** Pinterest
accounts:

1. **Kitchen Atlas** — `username = kitchenatlas`, `account_id = 1`
2. **Atlas Finds** — `username = atlasfinds`, `account_id = 2`

These were seeded for local UI testing and were **not** real Pinterest
connections. No real Pinterest credentials or OAuth connection ever existed.

---

## 3. Kitchen Atlas Investigation

Kitchen Atlas (`kitchenatlas`) had **historical simulated PUBLISHED queue
records** using:

- `https://example.com`
- `https://example.com/image.jpg`

Evidence it is simulated development data:

- `created_at` of 2026-08-04 predates the real integration work.
- Queue records reference `https://example.com` placeholder URLs.
- Multiple PUBLISHED records share the same timestamp (batch simulation).
- No real Pinterest credentials / OAuth connection exist.

These records were **NOT** real Pinterest publications. **DO NOT delete
them** — they remain useful as development/test data and as regression
fixtures. They are excluded from real publishing counts by the `is_seed`
flag, not by deletion.

---

## 4. Migration 017 Purpose

File: `sql/017_mark_seed_accounts.sql`

```sql
ALTER TABLE pinterest_accounts ADD COLUMN is_seed INTEGER NOT NULL DEFAULT 0;
UPDATE pinterest_accounts SET is_seed = 1 WHERE username IN ('atlashome', 'atlasfinds');
```

- Adds the `is_seed` column to `pinterest_accounts`.
- Marks the original migration-016 seed accounts (`atlashome`, `atlasfinds`)
  as development/test data.
- Additive and idempotent. It does **not** modify or drop migration 016, and
  it does not delete any rows.

---

## 5. Migration 018 Purpose

File: `sql/018_mark_remaining_seed_data.sql`

```sql
UPDATE pinterest_accounts SET is_seed = 1 WHERE username = 'kitchenatlas';
```

- Marks the pre-existing **Kitchen Atlas** dev account as seed data.
- This is what stops its simulated `https://example.com` PUBLISHED queue
  records from appearing as real publishing history/statistics.
- Additive and idempotent; running it where `kitchenatlas` does not exist is a
  safe no-op.
- Do **not** modify migration 017; keep them separate.

Rule of thumb: **any** account that is simulated/development/test data must
have `is_seed = 1`.

---

## 6. Current Pinterest Database Model

There are **four** existing Pinterest tables. Do not create duplicates.

### `pinterest_accounts` (migration 009 + 017)

| column | type | notes |
|---|---|---|
| `account_id` | INTEGER PK AUTOINCREMENT | |
| `account_name` | TEXT NOT NULL | display name |
| `username` | TEXT NOT NULL UNIQUE | e.g. `kitchenatlas` |
| `niche_slug` | TEXT NOT NULL | content niche |
| `daily_limit` | INTEGER NOT NULL DEFAULT 15 | |
| `status` | TEXT NOT NULL DEFAULT 'ACTIVE' | CHECK IN ('ACTIVE','INACTIVE') |
| `is_seed` | INTEGER NOT NULL DEFAULT 0 | added by 017; 1 = dev/test data |
| `created_at` | DATETIME DEFAULT CURRENT_TIMESTAMP | |

### `pinterest_boards` (migration 010 + 016)

| column | type | notes |
|---|---|---|
| `board_id` | INTEGER PK AUTOINCREMENT | |
| `account_id` | INTEGER NOT NULL | FK → `pinterest_accounts` ON DELETE CASCADE |
| `board_name` | TEXT NOT NULL | |
| `category_slug` | TEXT NOT NULL | |
| `status` | TEXT NOT NULL DEFAULT 'ACTIVE' | CHECK IN ('ACTIVE','INACTIVE') |
| `pin_count` | INTEGER NOT NULL DEFAULT 0 | added by 016 (dev metadata) |
| `follower_count` | INTEGER NOT NULL DEFAULT 0 | added by 016 (dev metadata) |
| `created_at` | DATETIME DEFAULT CURRENT_TIMESTAMP | |

### `category_routes` (migration 011 + 016)

Routes a product category to a destination (account + board).

| column | type | notes |
|---|---|---|
| `route_id` | INTEGER PK AUTOINCREMENT | |
| `category_slug` | TEXT NOT NULL | |
| `account_id` | INTEGER NOT NULL | FK → pinterest_accounts |
| `board_id` | INTEGER NOT NULL | FK → pinterest_boards |
| `priority` | INTEGER NOT NULL DEFAULT 1 | |
| `status` | TEXT NOT NULL DEFAULT 'ACTIVE' | |
| `created_at` | DATETIME DEFAULT CURRENT_TIMESTAMP | |
| — | — | UNIQUE (category_slug, account_id, board_id) |

### `pinterest_queue` (migration 006)

| column | type | notes |
|---|---|---|
| `pin_id` | INTEGER PK AUTOINCREMENT | |
| `ai_content_id` | INTEGER NOT NULL | FK → ai_content |
| `account_id` | INTEGER NOT NULL | FK → pinterest_accounts |
| `board_id` | INTEGER NOT NULL | FK → pinterest_boards |
| `affiliate_url` | TEXT NULL | |
| `image_url` | TEXT NULL | |
| `publish_order` | INTEGER NOT NULL DEFAULT 1 | |
| `status` | TEXT NOT NULL DEFAULT 'PENDING' | CHECK IN ('PENDING','READY','PUBLISHED','FAILED','CANCELLED') |
| `scheduled_at` | DATETIME NULL | |
| `published_at` | DATETIME NULL | |
| `retry_count` | INTEGER NOT NULL DEFAULT 0 | |
| `last_error` | TEXT NULL | |
| `created_at` | DATETIME DEFAULT CURRENT_TIMESTAMP | |
| — | — | UNIQUE (ai_content_id, account_id, board_id) |

### Related services (backend data access)

- `services/pinterest_accounts.py` — `create_pinterest_account`,
  `fetch_active_accounts` (`SELECT *` includes `is_seed`), `fetch_account`.
- `services/pinterest_boards.py` — `fetch_active_boards`.
- `services/queue_service.py` — publishing read model `_PUBLISHING_SELECT`
  (joins account `pa.is_seed`), `fetch_publishing_rows(..., real_accounts_only)`,
  `fetch_publishing_summary` (real-only PUBLISHED/FAILED),
  `fetch_next_pending_queue` (worker, filters `pa.is_seed = 0`).
- `services/atlas_api.py` — `GET /publishing`, `GET /publishing/accounts`,
  `GET /publishing/boards`, `POST /publishing/{queue,remove,schedule,publish-now,board}`,
  `GET /publishing/download/{creative_id}`.

### Related frontend (publishing)

- `frontend/src/features/publishing/publishing-api.ts` —
  `PinterestAccountRow` includes `is_seed?`; `postAction` parses FastAPI
  `detail`.
- `frontend/src/features/publishing/publishing-center.tsx` — computes
  `hasRealAccount` from `data.accounts.some((a) => !a.is_seed)`.
- `frontend/src/features/publishing/publishing-summary.tsx` — Boards card
  always shows "Configured boards".
- `frontend/src/features/publishing/publish-console.tsx` — Publish Now
  disabled when `!hasRealAccount`.

---

## 7. Why `is_seed` Must NOT Equal Connection Status

**NEVER interpret `is_seed = 0` as proof that an external account is
connected.**

These are two separate concepts:

- **`is_seed`** = "This is development/test data."
- **Connection state** = "Atlas has an actual valid connection to the
  external provider."

Conflating them produced the original bug: the UI claimed "Published 9" and
"Connected to Pinterest" purely because seeded accounts/boards existed.

A future account model should explicitly distinguish concepts such as:

- seed/test status
- configured account
- connection status
- provider
- account metadata
- credentials/token state

Example (target shape):

| account | is_seed | connection_status |
|---|---|---|
| Kitchen Atlas | true | NOT_CONNECTED |
| My Pinterest (future real) | false | CONNECTED |

The system must never claim Pinterest is connected merely because
development boards/accounts exist.

---

## 8. Recommended Accounts Architecture

Make **Accounts** the central place for managing external integrations,
becoming the source of truth for external integration configuration consumed
by Products, AI Studio, Creative Studio, and Publishing.

Keep these concepts separate:

```
Account            e.g. "Kitchen Atlas" (a configured integration)
  ↓
Connection         e.g. "Pinterest connection for Kitchen Atlas"
  ↓
Credential         e.g. OAuth access/refresh token, API key, Associate Tag
```

Per-provider shape:

```
Pinterest Account        Amazon Associates Account        AI Provider
    ↓                            ↓                            ↓
Connection              Configuration                  Connection
    ↓                            ↓                            ↓
OAuth credentials/tokens      Associate Tag              API credential
```

**Secrets must NEVER be exposed to frontend API responses.**

Recommended layering:

- **Provider registry**: an enum/lookup of providers (PINTEREST, AMAZON_ASSOCIATES, AI).
- **Account** (provider-agnostic identity + safe metadata).
- **Connection** (per-account connection state: NOT_CONNECTED / CONNECTING / CONNECTED / ERROR / DISCONNECTED).
- **Credential storage** (server-side only, never serialized to the frontend).

Recommended future flow (documented, not implemented in 029B):

```
Accounts
  ↓
Pinterest connection
  ↓
Real connected Pinterest account
  ↓
Boards
  ↓
Publishing

Accounts
  ↓
Amazon Associates configuration
  ↓
Affiliate URL generation
  ↓
Products
  ↓
Creative
  ↓
Publishing
```

---

## 9. Recommended 029B Schema Direction

Do not create duplicate Pinterest account/board tables. Audit existing schema
first (see section 6). Direction (subject to your review):

- Prefer **reusing `pinterest_accounts`** as the Pinterest account source and
  adding connection-state metadata, OR introduce a small set of new tables if
  reusing causes awkward coupling. Do not create a parallel `pinterest_*`
  duplicate set.
- Consider a new **`integration_providers`**-style lookup (or an enum) for
  provider identity.
- Consider a **`connections`** (or `account_connections`) table with:
  - `account_id` / integration reference
  - `provider`
  - `connection_status` (NOT_CONNECTED / CONNECTING / CONNECTED / ERROR / DISCONNECTED)
  - `connected_at`
  - safe metadata (username/display identifier, provider account id, etc.)
- Credentials belong in a **separate, server-only** table or column (token
  columns, encrypted or flagged), never returned by the API.
- Migration numbering continues from 018 → 019+. New migrations must be
  additive and idempotent (the runner applies every `sql/*.sql` file in
  filename order on each run; older ALTER statements are not idempotent, so
  prefer additive changes and apply new migrations individually when needed).
- Do not manually mutate the DB without a migration.

**029B schema scope**: enough to represent providers, accounts, connection
status, and safe metadata. Do not build Amazon credential plumbing beyond a
safe `Associate Tag` metadata representation if the Accounts Foundation
requires it; full Amazon affiliate-link generation is out of scope (029D).

---

## 10. Recommended 029B API Direction

- Keep the backend as the single source of truth; the frontend reads via
  TanStack Query (same pattern as ATLAS-027/028/029).
- Add an Accounts read endpoint, e.g. `GET /accounts`, returning only **safe
  metadata**:
  - `provider`
  - `display_name`
  - `status` / `connection_status`
  - `username` / display identifier where appropriate
- Add account management actions as needed (e.g. `POST /accounts/...` for
  create/configure/remove states), but **do not** implement OAuth flows.
- Follow existing FastAPI conventions in `services/atlas_api.py` (pydantic
  request/response models, `HTTPException` mapping, `sqlite3.Error` →
  HTTPException 500/409/404 pattern).
- **Never return** OAuth access tokens, refresh tokens, API keys, Amazon
  secrets, or private credentials in any response.
- Reuse `services/pinterest_accounts.py` where appropriate rather than
  duplicating Pinterest account logic.

---

## 11. Recommended 029B Frontend Structure

- Mirror the existing feature-folder pattern under
  `frontend/src/features/` (e.g. `frontend/src/features/accounts/`).
- Components: `accounts-api.ts` (types + fetch/mutations + safe mappers),
  `use-accounts.ts` (TanStack Query hooks), `accounts-page.tsx`,
  `accounts-list.tsx` / row components, loading skeleton, error + empty
  states.
- Use existing UI primitives: `MetricCard`, `SectionCard`, `EmptyState`,
  `Button`, `Input`, skeletons (see `frontend/src/features/dashboard/` and
  `frontend/src/features/publishing/publishing-skeleton.tsx`).
- Route already exists for `/accounts` (static route in the build output);
  wire it to the backend-driven feature.
- Follow existing dark/light theme support and the `.ai-ready` lint rules
  (React 19: no synchronous `setState` in effects — wrap in
  `window.setTimeout(..., 0)`; no function-use-before-declaration).
- Provide loading / error / empty states as required by 029B scope.

---

## 12. Security Requirements

- **Never** return to the frontend: OAuth access tokens, refresh tokens, API
  keys, Amazon secrets, private credentials.
- Frontend receives **only safe metadata**: `provider`, `display_name`,
  `status`/`connection_status`, `username`/display identifier where
  appropriate.
- Store credentials server-side only; never log them; never echo them in
  error messages.
- Keep the `is_seed` concept separate from connection status (section 7).
- Do not commit secrets, keys, or tokens to the repository.

---

## 13. Existing Files the Next Engineer Should Inspect

Backend:
- `sql/001`...`sql/018` — migrations (Pinterest model: 006, 009, 010, 011; seed data: 016, 017, 018)
- `services/database.py` — `get_connection()` (sqlite3.Row, PRAGMA foreign_keys=ON, timeout 30)
- `services/pinterest_accounts.py` — account data access
- `services/pinterest_boards.py` — board data access
- `services/queue_service.py` — publishing read model + `is_seed` filtering
- `services/atlas_api.py` — all endpoints + pydantic models + HTTPException patterns
- `services/pinterest_client.py` — `publish_pin` simulation stub (029C will replace with real API)
- `workers/publisher_worker.py` — worker (skips seed accounts)
- `scripts/run_migrations.py` — migration runner

Frontend:
- `frontend/src/features/publishing/publishing-api.ts` — safe `is_seed` handling + detail parsing pattern
- `frontend/src/features/publishing/use-publishing.ts` — TanStack Query hook pattern
- `frontend/src/features/publishing/publishing-center.tsx` — `hasRealAccount` derivation
- `frontend/src/features/publishing/publishing-summary.tsx` — honest Boards wording
- `frontend/src/features/dashboard/` — MetricCard / SectionCard / EmptyState / skeletons / types
- `frontend/src/features/creatives/use-creatives.ts` — query-key + mutation pattern

Docs:
- `docs/ATLAS-029-deliverables.md` — Publishing Center architecture
- `docs/ATLAS-029A-deliverables.md` — stabilization + seed-data finding

---

## 14. Explicit 029B Scope Boundaries

**029B SHOULD:**
- create a backend-driven Accounts page
- establish the account/integration architecture (Account / Connection / Credential separation)
- reuse existing Pinterest account infrastructure where appropriate
- establish safe account metadata
- establish connection-status representation
- support multiple accounts conceptually
- expose safe account information to the frontend
- provide loading / error / empty states
- follow existing Atlas UI patterns
- document schema/API decisions

**029B SHOULD NOT:**
- implement Pinterest OAuth
- connect a real Pinterest account
- implement Amazon affiliate-link generation
- scrape Amazon
- implement publishing
- implement product research
- redesign the Publishing Center
- implement campaigns
- add unrelated providers

Also for this handoff: do **not** modify application source code, do **not**
modify the database schema, do **not** create migrations, do **not** implement
OAuth, do **not** implement Amazon Associates, and do **not** commit.

---

## 15. Future 029C / 029D Dependencies

- **029C (Pinterest OAuth + real publishing)**: will depend on the Accounts
  Foundation from 029B — a real connected Pinterest account (connection status
  CONNECTED) whose boards feed Publishing. `services/pinterest_client.py::publish_pin`
  (currently a simulation stub returning `True`) will be replaced with a real
  Pinterest API call using stored credentials. Publishing is already
  architected to consume real accounts (`is_seed = 0` + connection status).
- **029D (Amazon Associates affiliate-link generation)**: depends on 029B's
  Accounts Foundation for an Amazon Associates account/configuration (safe
  Associate Tag metadata) and will produce affiliate URLs consumed by
  Products → Creative → Publishing. 029B should not build the affiliate-link
  generation itself.

The `is_seed` flag and connection-status model from 029A/B are the seam that
makes both future sprints possible without further schema churn.

---

*End of handoff. Written for a new engineer without access to the previous
conversation. Work tree left uncommitted.*
