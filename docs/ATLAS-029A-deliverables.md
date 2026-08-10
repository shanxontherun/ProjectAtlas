# ATLAS-029A — Publishing Center Stability: Real vs Seed Publishing Data

## Summary

ATLAS-029 delivered a fully backend-driven Publishing Center. ATLAS-029A
stabilizes it by removing the one misleading signal left behind: the
migration-016 seed accounts (Atlas Home, Atlas Finds) and their seeded
boards presented themselves as real connected Pinterest accounts, and the
simulation-based `publish_pin` marked queue items as PUBLISHED — so the UI
reported "Published 9" (local: 3) and a history of fake live Pins even
though no real Pinterest account is connected and no real Pinterest Pin was
ever published.

The fix makes the Publishing Center honest about the distinction between
real external publishing activity and development/seed data without
redesigning the UI, rewriting working code, deleting migration 016, or
dropping any existing data:

- Seed accounts are now explicitly flagged (`pinterest_accounts.is_seed`),
  but remain available for local UI testing.
- Published / history / summary counts come only from **real** (non-seed)
  account records — `published` is now 0 and the history shows
  "No Pins published yet" when no real records exist.
- Queue / schedule / remove persistence, board selection, and Download Pin
  are unchanged and still work.
- Publishing behaves safely with no real Pinterest connection: Publish Now
  is blocked in the UI and the backend returns
  "Connect a Pinterest account before publishing." instead of claiming a
  simulated success.

A final cleanup pass (migration 018) flagged the pre-existing "Kitchen Atlas"
dev account (`kitchenatlas`) as seed too, so its simulated PUBLISHED records
are excluded from real publishing counts and history. The Boards card always
reads "Configured boards" and never claims a Pinterest connection.

## Existing-Implementation Audit (requirement)

### What the current implementation already does well

| Area | Finding |
|---|---|
| Queue / remove / schedule persistence | All four mutations (`POST /publishing/{queue,remove,schedule,publish-now}`) persist to `pinterest_queue`; re-queue reuses CANCELLED rows via `reactivate_queue_item` (UNIQUE constraint), schedule flips PENDING→READY, remove flips QUEUED→APPROVED via `mark_queue_cancelled` + `unqueue_creative_from_publishing`. Verified working. |
| Summary source of truth | `fetch_publishing_summary` and the UI `getPublishCounts` derive counts from `pinterest_queue` statuses — **not** from `pinterest_boards.pin_count` — so board pin/follower counts were never actually used as the Published metric. |
| Download Pin | `GET /publishing/download/{creative_id}` streams the stored `creative_assets.image_path` (200, `image/png`, 828305 bytes for creative 1). Works and is reused by the frontend `creativeImageUrl`. |
| Queue only-APPROVED | `queue_creative_for_publishing` raises `CreativeLockedError` unless the creative is APPROVED; publish releases the lock back to APPROVED. |
| TanStack Query | Backend is the single source of truth; mutations invalidate `["publishing"]` (+ `["creatives"]` for queue/remove/publish-now). |
| Error handling | Backend unavailable → Publishing Center error state with "Try again"; queue empty → "Select a pin from the queue"; 409 conflicts surface details. |

### Root cause of the misleading Published count

| # | Finding |
|---|---|
| 1 | Migration `sql/016_seed_publishing_tables.sql` seeds 2 accounts and 5 boards with pin/follower counts **plus** 5 `category_routes`, and every queue item in the demo DB references account 1 or 2. |
| 2 | `pinterest_accounts` (migration 009) had **no** `is_seed` / connected marker — `fetch_active_accounts()` returned every ACTIVE account as if it were a real connected Pinterest account. |
| 3 | `services/pinterest_client.py::publish_pin` is a simulation stub returning `True`; both `publish-now` and `workers/publisher_worker.py` use it, so seed-tied queue items were marked PUBLISHED and appeared as real published Pins ("Published 9"). |
| 4 | `published-history.tsx::pinLink()` fabricated `https://pin.it/atlas-{id}` — a fake live-Pin link (removed in 029A). |
| 5 | `publishing-summary.tsx` deltas claimed "Connected to Pinterest" (boards) and "Across your boards" (published) even when every account was a seed account. |

## Files Modified

| File | Change |
|---|---|
| `sql/017_mark_seed_accounts.sql` (new) | `ALTER TABLE pinterest_accounts ADD COLUMN is_seed INTEGER NOT NULL DEFAULT 0`; marks `atlashome` / `atlasfinds` as `is_seed = 1`. |
| `sql/018_mark_remaining_seed_data.sql` (new) | Marks the simulated "Kitchen Atlas" dev account (`kitchenatlas`) as `is_seed = 1`. Additive and idempotent — applies cleanly whether or not the account exists locally. |
| `services/queue_service.py` | `_PUBLISHING_SELECT` now selects `pa.is_seed`; `fetch_publishing_rows(statuses, real_accounts_only=False)` filters `pa.is_seed = 0` when requested; `fetch_publishing_summary` counts PUBLISHED/FAILED from non-seed accounts only; `fetch_next_pending_queue` excludes seed accounts so the worker never "publishes" seed items. |
| `services/atlas_api.py` | `GET /publishing` requests history with `real_accounts_only=True`; `POST /publishing/publish-now` rejects queue items on seed accounts with `409` + "Connect a Pinterest account before publishing." |
| `frontend/src/features/publishing/publishing-api.ts` | `PinterestAccountRow` gains `is_seed?`; `postAction` parses the FastAPI `detail` JSON so backend messages reach the UI verbatim. |
| `frontend/src/features/publishing/publishing-center.tsx` | Computes `hasRealAccount` from `data.accounts`; passes it to summary + console; publish failure surfaces `error.message` (the actionable detail) instead of a generic "Couldn't publish this pin". |
| `frontend/src/features/publishing/publishing-summary.tsx` | Deltas are honest: Boards always reads "Configured boards" (never claims a Pinterest connection), and without a real account Published = "Connect a Pinterest account to publish" (neutral tone instead of positive). |
| `frontend/src/features/publishing/publish-console.tsx` | New `hasRealAccount` prop; Publish Now is disabled (with explanatory title) and a "Connect a Pinterest account before publishing." hint renders when no real account is connected. Schedule and Download Pin remain enabled. |
| `frontend/src/features/publishing/published-history.tsx` | Empty state is now "No Pins published yet"; removed the fabricated `pinLink()` and the "Copy link" button (a fake pin.it URL is a fabricated external claim). |
| `frontend/src/features/publishing/publishing-utils.ts` | `getPublishCounts` no longer counts `cancelled` publications as failed. |

No new tables. The only schema changes are the additive migrations 017 and 018.

## Database Changes

Applied to `database/atlas.db`:

```sql
ALTER TABLE pinterest_accounts ADD COLUMN is_seed INTEGER NOT NULL DEFAULT 0;
UPDATE pinterest_accounts SET is_seed = 1 WHERE username IN ('atlashome', 'atlasfinds');
```

Rationale for a new migration over editing 016: the runner applies every
`sql/*.sql` file in order on each run; editing 016 to drop the seed rows
would change the seed contract retroactively and the 016 ALTERs are not
idempotent. 017 is additive and idempotent, leaves the seeded boards and
their pin/follower metadata intact for local UI testing, and simply marks
the two sample accounts so real publishing logic can exclude them.

### Final seed-data finding (migration 018)

Local QA later identified that the pre-existing "Kitchen Atlas" account is
also development/test data even though its `is_seed` was still 0:

| account_id | account_name | username | created_at |
|---|---|---|---|
| 1 | Kitchen Atlas | kitchenatlas | 2026-08-04 |

Evidence it is simulated: queue records reference
`https://example.com` / `https://example.com/image.jpg`, multiple PUBLISHED
records share the same timestamp, and no real Pinterest credentials or OAuth
connection exist. `sql/018_mark_remaining_seed_data.sql` marks it seed:

```sql
UPDATE pinterest_accounts SET is_seed = 1 WHERE username = 'kitchenatlas';
```

It is additive and idempotent — running it on a database that does not
contain `kitchenatlas` (e.g. the local demo DB) is a safe no-op, while on a
database that does contain it, the account is now correctly excluded from
real publishing counts. No historical records are deleted.

Current local state:

| account_id | account_name | username | is_seed |
|---|---|---|---|
| 1 | Atlas Home | atlashome | 1 |
| 2 | Atlas Finds | atlasfinds | 1 |

## Publishing State Model (after 029A)

| Signal | Source (real external activity only) | Seed/dev behavior |
|---|---|---|
| Ready to Publish | PENDING `pinterest_queue` rows created via `/publishing/queue` | Still listed — queue persistence is a real workflow record |
| Scheduled | READY rows with `scheduled_at` | Still listed — scheduling persists |
| Published | PUBLISHED rows joined to **non-seed** accounts | 0 — seed-account PUBLISHED rows are excluded from summary + history |
| Failed | FAILED rows joined to **non-seed** accounts | Excluded |
| Published History | PUBLISHED/FAILED/CANCELLED rows on non-seed accounts | Empty → "No Pins published yet" |
| Boards | All ACTIVE `pinterest_boards` (configured boards) | 5 — shown as "Configured boards", not "Connected" |
| Real connection | Presence of an account with `is_seed = 0` | None today → Publish Now blocked, backend returns "Connect a Pinterest account before publishing." |
| Publisher worker | `fetch_next_pending_queue` now `AND pa.is_seed = 0` | Never attempts seed items |

Seed accounts/boards remain in the DB for local UI testing; they are simply
never presented as real external publishing.

## Verification

### Backend (direct service calls via curl)

```
GET  /publishing          → summary {ready:0, scheduled:1, published:0, failed:0, boards:5}
                          → queue len 1 (real queued creative, persists)
                          → history len 0 (seed PUBLISHED/FAILED/CANCELLED excluded)
                          → accounts [(Atlas Finds, is_seed=1), (Atlas Home, is_seed=1)]
POST /publishing/publish-now pin 5
                          → 409 {"detail":"Connect a Pinterest account before publishing. ..."}
POST /publishing/schedule pin 5 → 200, persisted (READY, scheduled_at updated) — restored after test
GET  /publishing/download/1 → 200 image/png, 828305 bytes
python3 workers/publisher_worker.py → "No pending queue items found." (seed items skipped)
```

### Migration 018 verification (Kitchen Atlas simulation)

Verified in a throwaway DB copy (`/tmp/opencode/atlas_018test.db`) that
reproduces the QA finding: a `kitchenatlas` account with `is_seed = 0`,
two PUBLISHED queue rows sharing one timestamp, and `https://example.com`
URLs.

- Before migration 018: `kitchenatlas.is_seed = 0`.
- After migration 018: `kitchenatlas.is_seed = 1`.
- Real-account summary query now returns `{}` — the simulated PUBLISHED
  records are excluded (Published = 0).
- Worker's pending-queue query (`status='PENDING' AND pa.is_seed = 0`)
  returns none for a pending item on `kitchenatlas` — seed accounts cannot
  be published through the worker.

### Frontend

- `npm run lint` — 0 errors.
- `npx tsc --noEmit` — clean.
- `npm run build` — compiled successfully, 12 static routes.
- Playwright (preview URL) — `/publishing`: Ready 0, Scheduled 1, Published 0,
  Boards 5 **"Configured boards"** (no "Connected to Pinterest" claim), queue
  item + console still functional, Publish Now disabled with title,
  "Connect a Pinterest account before publishing." hint, Published History
  "No Pins published yet", **zero console errors**. Regression on `/`,
  `/products`, `/content`, `/creatives`, `/publishing` — all load with zero
  console errors.

### Screenshots

- `frontend/public/screenshots/publishing-center-seed-honesty.png`
- `frontend/public/screenshots/publishing-center-configured-boards.png`
  (final: Boards 5 / "Configured boards")

## Known Limitations

- `services/pinterest_client.py::publish_pin` remains a simulation stub that
  returns `True`; real Pinterest publishing is out of scope for 029A (029B+
  sprint). Until a real (non-seed) account exists, `publish-now` is blocked,
  so the stub cannot produce a fake "published" record through the UI.
- The publisher worker skips seed-account queue items; with only seed
  accounts present it finds nothing to do, which is the safe behavior.
- Boards metric still counts all 5 seeded ACTIVE boards as "configured"
  boards; label reflects this ("Configured boards") rather than claiming a
  Pinterest connection.
- Migration 016's seed rows are intentionally retained; a future real-account
  sprint will connect genuine Pinterest accounts (is_seed = 0), at which
  point published/history/summary become populated from real records without
  any further schema change. Migration 018 additionally flags the pre-existing
  "Kitchen Atlas" dev account (`kitchenatlas`) so it is treated as seed too;
  its simulated `https://example.com` PUBLISHED records are excluded from the
  real Published count and history without deleting them.

## Out of Scope (not started — as instructed)

ATLAS-029B (Accounts Foundation), 029C (Pinterest OAuth), 029D (Amazon
affiliate-link generation). Work tree left uncommitted for CTO review.
