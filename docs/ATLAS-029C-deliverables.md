# ATLAS-029C — Pinterest OAuth (Real Connect for Accounts)

## Summary

ATLAS-029C implements a **real Pinterest OAuth 2 Authorization Code flow**
for Atlas Accounts. Connecting a Pinterest account now performs a genuine
OAuth round-trip: the frontend requests an authorization URL, the user
authorizes on Pinterest, the backend validates the OAuth state, exchanges
the code for tokens server-side, fetches the authenticated user, persists
safe account/connection metadata plus server-side credentials in 029B's
`connection_credentials`, syncs the user's real boards, and returns to the
Accounts page — **never faking success**.

Every prior-sprint honesty rule is preserved:

- `is_seed` and `connection_status` remain separate. The seed accounts
  (Atlas Home, Atlas Finds) are never converted into real accounts.
- Real non-seed accounts surface only after a verified OAuth exchange.
- Board sync is best-effort; a sync failure yields `status=partial`,
  never a false full success.
- Publishing is **not** implemented: `publish_pin` now raises
  `NotImplementedError` instead of simulating a successful publish, so a
  real, non-seed queue item can never be falsely marked `PUBLISHED`.

## Existing-Implementation Audit (requirement)

Reviewed before writing code (repository state is authoritative):

| Area | Finding |
|---|---|
| 029B accounts model | `account_connections` + `connection_credentials` reused as-is — **no second credential system**. |
| Seed accounts | `pinterest_accounts` rows 1–2 (Atlas Home, Atlas Finds) `is_seed=1`; connections 1–2 `NOT_CONNECTED`, `is_seed=1`. Guarded so OAuth can never touch them. |
| Seed boards | 5 seed boards ACTIVE with no Pinterest board ids; `sync_real_boards` upserts by Pinterest board id and never modifies seed rows. |
| Publishing | `services/pinterest_client.py::publish_pin` previously returned a hardcoded `True`. Now raises `NotImplementedError` — no fake publishes possible. |
| Accounts UI | `accounts-api.ts` / `use-accounts.ts` / `accounts-page.tsx` / `accounts-provider-section.tsx` extended; seed rows keep the "Sample" badge and "Not connected" status; a working "Connect Pinterest" button replaces the disabled placeholder. |
| Frontend patterns | Followed existing conventions: `use client` components, TanStack Query, shadcn `Button`, `SectionCard`, `EmptyState`, lucide icons, `@/` alias, `next.config.ts` `/api/:path*` rewrite to `API_UPSTREAM`. |
| API conventions | FastAPI + pydantic models, `sqlite3.Error` → `HTTPException`, business logic in `services/` modules (not route handlers), callback never returns credentials. |

## Architecture

```
Accounts page
    │  GET /api/accounts/pinterest/connect
    ▼
Backend generates + stores OAuth state (oauth_states)
    │  returns Pinterest authorization_url  (scope: user_accounts:read,
    │   boards:read, pins:read, pins:write)
    ▼
Browser → Pinterest authorize → redirect back to
    GET /api/accounts/pinterest/callback?code=…&state=…
    ▼
Backend validates state (exists / matches / not expired / not replayed)
    │  1. exchange code → access + refresh token   (server-side only)
    │  2. GET /v5/user_accounts (me)               (server-side only)
    │  3. upsert real account + connection (CONNECTED, is_seed=0)
    │  4. store credentials in connection_credentials
    │  5. sync real boards (best-effort)
    ▼
302 → /accounts?pinterest=success|partial|denied|error[&reason=…]
```

Key separation: the browser only ever touches `/accounts` (a safe status
redirect). Authorization codes, tokens, and client secrets never appear in
a browser response, URL, or the DOM.

### OAuth scopes

Configured in `services/constants.py` per the official Pinterest V5 docs:

```
user_accounts:read   # identify the connected user
boards:read          # read the user's boards (for board sync)
pins:read            # read the user's pins
pins:write           # future publishing (scope declared now)
```

### State / CSRF protection

- A `secrets.token_urlsafe(32)` state is generated and stored server-side
  in a new `oauth_states` table (not a signed cookie), so the callback can
  reject missing, mismatched, expired, and **replayed** states.
- TTL is 600 seconds (`PINTEREST_STATE_TTL_SECONDS`); expired rows are
  cleaned and ignored.
- `validate_oauth_state` consumes the row inside the check, so a given
  state can be used exactly once.

### Credential storage

- Access + refresh tokens are written only to `connection_credentials`
  (`PINTEREST_ACCESS_TOKEN`, `PINTEREST_REFRESH_TOKEN`), keyed by
  `connection_id`. Upserts use `ON CONFLICT(connection_id, credential_type)`.
- The Accounts read model never queries `connection_credentials` and never
  includes a credential field. The automated test suite asserts no
  token-shaped or secret-shaped strings appear in `/accounts` responses or
  in the rendered DOM.

### Token refresh

- `refresh_access_token` exchanges the stored refresh token for a fresh
  access token (`refresh_token` grant, re-declaring scopes).
- `refresh_stored_pinterest_credentials` persists the rotated tokens
  server-side. If no token is stored (e.g., never connected), it fails
  safely instead of inventing a credential.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/accounts/pinterest/connect` | Start flow; returns `{"authorization_url": …}`. `503` with a clear message when `PINTEREST_CLIENT_ID`/`PINTEREST_CLIENT_SECRET`/`PINTEREST_REDIRECT_URI` are missing. |
| `GET` | `/accounts/pinterest/callback` | OAuth redirect target. Validates state, exchanges code, fetches user, persists connection + credentials, syncs boards. Always `302 → /accounts?pinterest=…`; never returns credentials. |
| `POST` | `/accounts/pinterest/disconnect` | `{"connection_id": N}` → removes stored credentials, marks `DISCONNECTED`, clears `connected_at`, preserves safe metadata. `404` unknown, `409` seed. |

Frontend hits all three through the Next.js `/api/:path*` rewrite.

## Database Changes

New additive migration **`sql/020_pinterest_oauth.sql`**:

| Object | Purpose |
|---|---|
| `oauth_states` | Server-side CSRF/state store: `state` (unique), `expires_at`, `consumed_at`; expiry index |
| `pinterest_accounts.pinterest_user_id` | Real Pinterest user id, unique where not null (partial index) — identity for reconnect |
| `pinterest_boards.pinterest_board_id` | Real board id, unique where not null (partial index) — identity for board upsert |
| `pinterest_boards.privacy` | Board privacy ("PUBLIC"/"SECRET") mirrored from Pinterest |

All additions are `ADD COLUMN`/`CREATE TABLE` only — no destructive change,
no touched seed rows.

## Account / Board Mapping

- **Account upsert** (`upsert_real_pinterest_account`): matches first by
  `pinterest_user_id`, then by username; creates only if no match.
  Refuses to convert a seed account. Real accounts are `is_seed=0` with
  `niche_slug='uncategorized'` and **no invented stats**.
- **Connection create/update** (`create_or_update_pinterest_connection`):
  reuses an existing row via `provider + pinterest_account_id`, marks
  `CONNECTED`, sets `connected_at`. Reconnect updates the same connection —
  no duplicates.
- **Board sync** (`sync_real_boards`): bookmarked pagination (page size
  100, up to 20 pages), upserts by `pinterest_board_id`, marks previously
  synced boards that vanished on Pinterest as `INACTIVE`, and never touches
  seed boards. Boards use `category_slug='uncategorized'` and leave
  `pin_count`/`follower_count` at schema defaults (0) — no invented stats.

## Frontend

- `accounts-api.ts`: `AccountRow.profileUrl`, `startPinterestConnect()`
  (typed `PinterestConnectError`), `disconnectPinterestConnection()`.
- `accounts-provider-section.tsx`: enabled **Connect Pinterest** button
  (loading state, inline config error on 503, never navigates to Pinterest
  unless a real URL was returned) and a per-row **Disconnect** button for
  non-seed connected accounts.
- `accounts-oauth-banner.tsx`: reads `?pinterest=` / `reason`, renders
  dismissible success / partial / denied / config-missing / generic-error
  banners, and cleans the query string from the URL after capture (the
  banner keeps its status in local state, so it is never lost to the URL
  cleanup).
- `accounts-page.tsx`: renders the banner inside a `Suspense` boundary
  (required for `useSearchParams` prerendering).
- `accounts-account-row.tsx`: shows a "Sample" badge on seed rows (no
  disconnect), a Disconnect action + profile link on real rows.

## Configuration

Environment variables (server-side; never committed):

| Variable | Purpose |
|---|---|
| `PINTEREST_CLIENT_ID` | Pinterest V5 app client id |
| `PINTEREST_CLIENT_SECRET` | Pinterest V5 app client secret |
| `PINTEREST_REDIRECT_URI` | Must match the Pinterest app's registered redirect URI, e.g. `https://<host>/api/accounts/pinterest/callback` |

When any is missing, `GET /accounts/pinterest/connect` returns `503` with a
clear message and the frontend shows an inline "Pinterest isn't configured"
error. No code path hardcodes or logs a secret.

## Tests

- `tests/test_pinterest_oauth.py` — new suite (58 checks) covering: state
  generation/validation (replay, expiry, missing), authorization URL shape
  (client_id, redirect_uri, response_type, scope, state), config-missing
  behavior, token exchange + failure, full flow (user persisted `is_seed=0`,
  connection `CONNECTED`, `connected_at` set), board sync (upsert,
  no-duplicate re-sync, INACTIVE on removal, seed untouched), partial-sync
  failure reporting, reconnect reusing one connection, disconnect
  (credentials removed, seed refused), token refresh + rotation, endpoint
  behavior via TestClient (redirects, `503`, `404`, `409`), and the
  **no-credentials-in-responses/DOM** guarantee.
- `tests/test_accounts_foundation.py` — still passes (029B regression).
- Pre-existing suites that need a GUI display or a live mock LLM
  (`test_bestsellers`, `test_discovery`, `test_parser`, `test_ai_client`)
  could not run in this headless environment; they fail before reaching any
  029C code and are unrelated to this change.

## Browser QA

Ran headless Playwright against the live dev stack via the preview URL
(`frontend/public/screenshots/qa/`). All 25 checks passed:

- Regression: `/`, `/products`, `/content`, `/creatives`, `/publishing`
  load with zero console errors.
- `/accounts` initial state: seed rows show "Sample" + "Not connected";
  Connect Pinterest enabled; sample-data note shown.
- Connect with missing config: inline error appears, no navigation away.
- OAuth banners for `success`, `partial`, `denied`, `error`,
  `error&reason=config`; URL cleaned after capture; banner dismissible.
- A mocked real (non-seed) connected account renders "Connected" + profile
  link + Disconnect; seed rows show no Disconnect; disconnect updates the
  badge to "Disconnected" and removes stored credentials server-side.

Screenshots: `frontend/public/screenshots/qa/accounts_initial.png`,
`accounts_connect_config_error.png`, `accounts_real_connected.png`,
`accounts_after_disconnect.png`, `banner_success.png`,
`banner_partial.png`, `banner_denied.png`, `banner_error.png`,
`banner_error_config.png`, plus `regression_*.png` for each page.

## Local Setup

```
# 1. Backend (from services/)
PINTEREST_CLIENT_ID=… PINTEREST_CLIENT_SECRET=… \
PINTEREST_REDIRECT_URI=https://<host>/api/accounts/pinterest/callback \
python3 -m uvicorn atlas_api:app --host 127.0.0.1 --port 8000

# 2. Frontend
cd frontend && npm run dev

# 3. Open /accounts → Connect Pinterest → authorize → return
```

The dev database is rebuilt from migrations 001–020 (additive; seed state
is identical to a 001–019 build plus the empty `oauth_states` table).

## Limitations

- End-to-end OAuth against live Pinterest was not exercised here (no real
  app credentials); the full flow is covered by mocked tests and the UI by
  browser QA. To validate live: set the env vars and complete one connect.
- Publishing real pins is intentionally not implemented (029C scope); real
  non-seed accounts and boards are surfaced and synced, and `publish_pin`
  refuses to fake success. Seed boards remain un-publishable.
- Disconnect removes local credentials and marks the connection
  `DISCONNECTED`; it does not revoke the Pinterest app's access server-side
  (revocation would require a separate Pinterest API call and is not
  implemented).
- `profile_url` for seed accounts is derived from their username (as for
  real accounts) and links to the corresponding sample Pinterest URL.
