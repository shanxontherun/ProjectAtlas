# ATLAS-029B — Accounts Foundation

## Summary

ATLAS-029B makes **Accounts** Atlas's central source of truth for external
integrations. It replaces the placeholder Accounts page with a fully
backend-driven page that represents three providers — **Pinterest**,
**Amazon Associates**, and **AI Providers** — through an explicit
Account → Connection → Credential model with honest, never-faked
connection statuses.

The sprint deliberately does **not** implement Pinterest OAuth, Amazon
integration, affiliate-link generation, publishing changes, or product
research. Those remain documented future phases.

The critical rule from 029A is preserved and enforced: **`is_seed` and
`connection_status` are separate concepts.** The seed/dev Pinterest
accounts (Atlas Home, Atlas Finds) surface as `is_seed = true` with
`connection_status = NOT_CONNECTED` — never as connected accounts. A
non-seed account is **not** automatically connected.

## Existing-Implementation Audit (requirement)

Reviewed before writing code (repository state is authoritative):

| Area | Finding |
|---|---|
| 029A seed handling | `sql/017` + `sql/018` flag seed accounts; Publishing excludes seed activity, prevents seed publishing, shows "Configured boards", never claims a Pinterest connection. **Untouched and preserved.** |
| `pinterest_accounts` | Existing table reused as Pinterest account identity — **no duplicate Pinterest tables created.** |
| `pinterest_boards` / `category_routes` / `pinterest_queue` | Reused by Publishing; **not modified.** |
| AI configuration | `services/ai_service.py` + `services/ai_client.py` already read `AI_BASE_URL` / `AI_API_KEY` / `AI_MODEL`. Reused via existence checks — **no second credential system, no AI Studio redesign.** |
| Existing Accounts UI | `frontend/src/app/(app)/accounts/page.tsx` was a static `PlaceholderPage`. Replaced with the backend-driven feature. |
| Frontend patterns | API client → TanStack Query → React (as in Publishing / Creatives); `MetricCard`, `SectionCard`, `EmptyState`, `Button`, skeletons reused. |
| API conventions | FastAPI + pydantic, `sqlite3.Error` → HTTPException, backend as single source of truth. Followed. |

## Architecture

```
Accounts (source of truth for external integrations)
    │
    ├── Account      → an integration identity (provider + display name)
    ├── Connection   → the external connection state for that account
    │                  (NOT_CONFIGURED / NOT_CONNECTED / CONNECTING /
    │                   CONNECTED / ERROR / DISCONNECTED / CONFIGURED)
    └── Credential   → server-side only secrets, never serialized to the API
```

Per-provider shape (matching the CTO handoff):

```
Pinterest Account           Amazon Associates Account      AI Provider
    ↓                              ↓                          ↓
Connection                   Configuration               Connection
    ↓                              ↓                          ↓
OAuth credentials/tokens       Associate Tag             API credential
```

### Account / Connection / Credential model

- **Account** and **Connection** live in one additive table,
  `account_connections`, with safe metadata only:
  `provider`, `display_name`, `username`, `marketplace`,
  `connection_status`, `connected_at`, `is_seed`, and an optional
  `pinterest_account_id` FK that **reuses** `pinterest_accounts`
  (no parallel Pinterest table).
- **Credential** lives in a separate, server-only table,
  `connection_credentials` (type + value), which the Accounts API never
  queries. This keeps an accidental `SELECT *` from leaking a token.
- **Pinterest** identity is reused from `pinterest_accounts`; seed
  accounts are auto-represented as `NOT_CONNECTED` connections.
- **Amazon Associates** currently has no rows → the section honestly shows
  "Not configured". Associate Tag/credentials stay server-side in 029D.
- **AI Providers** are synthesized (not DB-backed) from the existing
  environment configuration, so no second credential system is created.

### Connection statuses

Explicit states only; nothing is ever faked as `CONNECTED`:

| Status | Meaning |
|---|---|
| `NOT_CONFIGURED` | No configuration exists (Amazon, AI without env config) |
| `NOT_CONNECTED` | Account exists but no external connection (all Pinterest today) |
| `CONNECTING` | Connection in progress (future) |
| `CONNECTED` | Verified external connection (future, real only) |
| `ERROR` | Connection error (future) |
| `DISCONNECTED` | Previously connected, now disconnected (future) |
| `CONFIGURED` | Configuration present but not verified live (AI with env config) |

### Multiple accounts

Supported per provider and modeled in the data:

- **Pinterest**: multiple accounts (Atlas Home, Atlas Finds today; Tiny
  Smart Finds etc. in future) — each its own connection row.
- **Amazon**: multiple marketplaces/accounts (US/UK) as future rows.
- **AI**: OpenRouter, Gemini, OpenAI (and a generic label for unknown
  gateways) listed simultaneously.

## Database Changes

New migration **`sql/019_create_accounts_foundation.sql`** (additive and
idempotent; old migrations untouched):

| Object | Purpose |
|---|---|
| `account_connections` | Account + connection safe metadata; CHECK on provider and connection_status; `UNIQUE (provider, pinterest_account_id)` for idempotent reseeding; indexes on provider and status |
| `connection_credentials` | Server-side-only credential store (never returned); FK cascade to connections |
| Seed | Represents every existing `pinterest_accounts` row as a `PINTEREST` connection with `NOT_CONNECTED` and `is_seed` copied from the account |

The migration runner (`scripts/run_migrations.py`) re-applies every
`sql/*.sql` file in order on each run, and migration 001's seed inserts are
not idempotent, so (as the handoff notes) the new migration was applied to
the dev DB individually. A fresh database built from all migrations 001–019
is fully valid; the rebuilt dev DB matches it.

Local dev DB after 019 (2 Pinterest connections):

| connection_id | provider | display_name | username | connection_status | is_seed |
|---|---|---|---|---|---|
| 1 | PINTEREST | Atlas Home | atlashome | NOT_CONNECTED | 1 |
| 2 | PINTEREST | Atlas Finds | atlasfinds | NOT_CONNECTED | 1 |

## API Changes

New read-only endpoint in `services/atlas_api.py` (no mutations required
for the foundation; backend stays the single source of truth):

**`GET /accounts`** → provider-grouped read model:

```json
[
  {
    "provider": "PINTEREST",
    "label": "Pinterest",
    "accounts": [
      {
        "connection_id": 1,
        "provider": "PINTEREST",
        "display_name": "Atlas Home",
        "username": "atlashome",
        "marketplace": null,
        "connection_status": "NOT_CONNECTED",
        "connected_at": null,
        "is_seed": true
      }
    ]
  },
  {
    "provider": "AMAZON_ASSOCIATES",
    "label": "Amazon Associates",
    "accounts": []
  },
  {
    "provider": "AI",
    "label": "AI Providers",
    "accounts": [
      { "provider": "AI", "display_name": "OpenRouter", "connection_status": "NOT_CONFIGURED", "is_seed": false, "connection_id": null }
    ]
  }
]
```

Only **safe metadata** is returned. When `AI_BASE_URL` + `AI_API_KEY` +
`AI_MODEL` exist, the matching AI provider reports `CONFIGURED` (presence
only — the base URL is inspected for a label, the values are never read,
logged, or returned).

New/changed backend files:

| File | Change |
|---|---|
| `sql/019_create_accounts_foundation.sql` | new tables + seed (above) |
| `services/constants.py` | provider + connection-status + AI provider constants |
| `services/accounts_service.py` | `fetch_accounts`, `fetch_pinterest_accounts`, `fetch_amazon_accounts`, `fetch_ai_providers`; safe-column SELECT only |
| `services/atlas_api.py` | `GET /accounts` endpoint + import |

## Frontend Changes

New feature folder `frontend/src/features/accounts/`, following the
existing API client → TanStack Query → React pattern (mirrors Publishing):

| File | Purpose |
|---|---|
| `accounts-api.ts` | types + `mapAccount` / `mapProviderGroup` mappers + `fetchAccounts`; validates status/provider values (defensive) |
| `use-accounts.ts` | `useAccounts` TanStack Query hook + `ACCOUNTS_QUERY_KEY` |
| `accounts-page.tsx` | page: loading skeleton, error state with Try again (invalidate + refetch), Refresh button (invalidate → preserves state), empty state, provider sections |
| `accounts-provider-section.tsx` | `SectionCard` per provider with honest status badge, account list or `EmptyState`, seed note, disabled CTA (Pinterest / Amazon) |
| `accounts-account-row.tsx` | account row: provider icon, display name, username/marketplace meta, status badge, "Sample" tag for seed accounts |
| `accounts-status-badge.tsx` | status → label + tone (Connected / Connecting / Configured / Not connected / Not configured / Error / Disconnected) |
| `accounts-skeleton.tsx` | loading skeleton |

`frontend/src/app/(app)/accounts/page.tsx` now renders `<AccountsPage />`
(client component) instead of the static `PlaceholderPage`.

No mock account data anywhere — the frontend renders only what
`GET /accounts` returns. Loading, error, empty, retry, refresh, and dark/
light themes are handled.

## Security

- `GET /accounts` returns **safe metadata only**: provider, display name,
  username, marketplace, status, connected_at, is_seed.
- **Never returned:** OAuth access/refresh tokens, API keys, Amazon
  secrets, Associate Tag, credential values. The Accounts service selects
  explicit safe columns and never queries `connection_credentials`.
- Credentials are stored server-side only (separate table) and are never
  logged or echoed in error messages.
- AI env values are existence-checked only; no value is read, logged, or
  serialized.
- QA verified **zero credential-shaped strings** (bearer/sk-/access_token/
  refresh_token/associate_tag/api_key) in the rendered DOM.

## Seed Handling

- Seed/dev Pinterest accounts (Atlas Home, Atlas Finds) are represented as
  connections with `is_seed = true` and `connection_status =
  NOT_CONNECTED`. The UI tags them "Sample" and explains none are connected.
- `is_seed` is never interpreted as "connected". A non-seed account is not
  automatically connected (verified by a test that inserts a non-seed
  account and asserts it still reads `NOT_CONNECTED`).
- Publishing's 029A behavior (seed exclusions, Publish Now block, honest
  boards wording) is untouched and re-verified.

## Verification

### Static checks (all pass)

```
npm run lint          → 0 errors
npx tsc --noEmit      → clean
npm run build         → clean, 12 static routes
```

### Backend

```
GET /accounts → providers [PINTEREST, AMAZON_ASSOCIATES, AI];
               Pinterest: 2 seed accounts NOT_CONNECTED (never CONNECTED);
               Amazon: []; AI: OpenRouter/Gemini/OpenAI NOT_CONFIGURED
PYTHONPATH=/workspace python3 tests/test_accounts_foundation.py → 12/12 ok
```

`tests/test_accounts_foundation.py` builds a throwaway DB from the real
migrations and asserts: provider grouping, multiple accounts, seed =
NOT_CONNECTED, no CONNECTED claims, Amazon empty, non-seed account not
auto-connected, AI env-driven status, no credential fields in the read
model, and the server-only credentials table exists.

### Browser QA (Playwright, preview host, zero console errors)

- `/accounts`: heading, three provider sections, seed accounts listed with
  "Not connected" + "Sample", AI providers "Not configured", disabled
  "Connect Pinterest" / "Configure Amazon Associates" buttons, Refresh
  button, no credential-shaped strings in the DOM.
- Light + dark themes render and screenshot.
- Refresh preserves state (accounts still visible after refetch).
- Error state (backend down) shows "Try again"; recovery after the backend
  returns (polled retry) re-renders the accounts.
- Regression: `/`, `/products`, `/content`, `/creatives`, `/publishing`
  all load with **zero console errors**.

### Screenshots

- `frontend/public/screenshots/accounts-backend-light.png`
- `frontend/public/screenshots/accounts-backend-dark.png`
- `frontend/public/screenshots/accounts-backend-error-state.png`

## Files Changed

| Area | Files |
|---|---|
| Backend | `services/accounts_service.py` (new), `services/atlas_api.py`, `services/constants.py` |
| Migration | `sql/019_create_accounts_foundation.sql` (new) |
| Frontend | `frontend/src/features/accounts/` (new), `frontend/src/app/(app)/accounts/page.tsx` |
| Tests | `tests/test_accounts_foundation.py` (new) |
| Docs | `docs/ATLAS-029B-deliverables.md` (this file), CHANGELOG + JOURNAL entries |
| Screenshots | `frontend/public/screenshots/accounts-backend-*.png` (new) |

Work tree left **uncommitted** for CTO review (per sprint instruction).

## Known Limitations

- No real Pinterest connection exists, so Pinterest shows only
  NOT_CONNECTED sample accounts; the disabled "Connect Pinterest" CTA
  explains OAuth is a later sprint.
- Amazon Associates is "Not configured" with no account rows; Associate Tag
  and credential plumbing beyond safe metadata are deliberately not built
  (029D).
- AI status is derived from env-variable *presence* (`AI_BASE_URL` /
  `AI_API_KEY` / `AI_MODEL`); `CONFIGURED` means "config present", not a
  verified live connection, and the provider label is guessed from the base
  URL hostname.
- `account_connections` status values are constrained by a CHECK; adding
  new statuses later needs an additive migration (SQLite cannot alter a
  CHECK in place).
- The migration runner re-applies every `sql/*.sql` file on each run; 019
  is idempotent, but older migrations (e.g. 001's category inserts) are not,
  so migrations must be applied individually to an existing DB.
- The dev DB (`database/atlas.db`) was rebuilt from migrations 001–019 and
  contains only migration-seeded data (no user data existed). A pre-029B
  backup was kept at `database/atlas.db.pre-029B`.

## Out of Scope (documented, not implemented)

- Pinterest OAuth / API integration → **029C** (depends on this foundation:
  a real connected Pinterest account whose boards feed Publishing; replaces
  `services/pinterest_client.py::publish_pin`).
- Amazon API/scraping and affiliate-link generation → **029D** (depends on
  the Amazon account/Associate Tag metadata shape established here).
- Product research, campaigns, publishing changes, creative redesign,
  multi-platform publishing.

## Recommended 029C

1. Pinterest OAuth flow that creates a real `account_connections` row
   (is_seed = 0, status CONNECTED after a token exchange) and stores OAuth
   tokens in `connection_credentials` server-side only.
2. A `GET /accounts` status refresh that verifies a live connection (token
   validity) before reporting `CONNECTED`.
3. Feed connected Pinterest accounts/boards into Publishing (boards already
   read `pinterest_accounts`; join through the connection's
   `pinterest_account_id`).
4. Replace `services/pinterest_client.py::publish_pin` with the real
   Pinterest API using stored credentials.
5. Add `PINTEREST` connection actions (connect / disconnect / error
   states) as mutations only when genuinely needed.
