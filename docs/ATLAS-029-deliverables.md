# ATLAS-029 — Publishing Center: Real Backend, Persistent Queue/History

## Summary

Completed the first end-to-end Atlas workflow — Research → AI Content →
Creative → Publishing Queue → Published. The Publishing Center keeps its
existing UI (queue, destination selector, schedule/publish-now console,
published history, summary cards, skeletons, dark/light themes) but every
value now comes from the live FastAPI backend through the same TanStack
Query architecture used in ATLAS-027/028. Queueing, scheduling, publishing,
board selection, history and downloads all persist across refresh.

Only APPROVED creatives can enter the queue; queued creatives become
read-only in Creative Studio; removing them from the queue re-enables
editing via the existing Return to Review flow. No new statuses or tables
were introduced — the sprint reuses `creative_assets.status`
(APPROVED/QUEUED) and `pinterest_queue.status`
(PENDING/READY/PUBLISHED/FAILED/CANCELLED).

## Architecture (reference: ATLAS-027/028)

```
SQLite
  ↓
FastAPI (services/atlas_api.py → queue_service.py / creative_service.py / pinterest_boards.py)
  ↓
publishing-api.ts  (fetchPublishing / queueCreative / removeCreative / schedulePin /
                    publishNow / updatePinBoard; mappers mapPublishItem / mapPublication / mapBoard)
  ↓
use-publishing.ts  (usePublishing / useQueueCreative / useRemoveCreative /
                    useSchedulePin / usePublishNow / useUpdatePinBoard)
  ↓
TanStack Query  (["publishing"]; queue/remove/publish also invalidate ["creatives"])
  ↓
Publishing Center (publishing-center.tsx) + Creative Studio (creative-studio.tsx)
```

## Backend Reuse Audit (requirement)

| Need | Reused (existing) | Extended | New |
|---|---|---|---|
| Queue rows | `pinterest_queue` table (sql/006) | `_PUBLISHING_SELECT` now includes `affiliate_url`, `image_url`, `publish_order`, `pinterest_description` | — |
| Board/account lookup | `pinterest_boards`, `pinterest_accounts`, `category_routes` tables | — | `fetch_active_boards()` (`services/pinterest_boards.py`) |
| Creative status transitions | `creative_assets.status` | — | `queue_creative_for_publishing` / `unqueue_creative_from_publishing` (rebuilt in `services/creative_service.py`) |
| Publishing the pin | `workers/publisher_worker.py` + `services/pinterest_client.py` `publish_pin` | — | `POST /publishing/publish-now` orchestration |
| Image download | `creative_assets.creative_image_path` | — | `GET /publishing/download/{creative_id}` (FileResponse, inline) |
| Category → destination routing | `category_routes` + `fetch_routes_by_category` | — | slug derivation + route pick in the queue endpoint |

No new tables, no new statuses. The only schema change is an additive
migration (`sql/016`) that seeds accounts/boards/routes and adds
`pin_count`/`follower_count` display columns to `pinterest_boards`.

## API Endpoints Added

- **GET `/publishing`** — combined read model: `{ queue, history, summary,
  accounts, boards }` in one fetch so the Publishing Center renders live.
- **GET `/publishing/accounts`** — active Pinterest accounts.
- **GET `/publishing/boards`** — every active board across all accounts
  (pin/follower counts included).
- **POST `/publishing/queue`** (`{ research_product_id }`) — validates the
  product + its approved creative, derives `category_slug` from the product
  category, resolves the first `category_routes` destination, guards
  duplicates (409), reuses a CANCELLED `pinterest_queue` row via
  `reactivate_queue_item` (the table's
  `UNIQUE(ai_content_id, account_id, board_id)` blocks a fresh insert), and
  flips the creative QUEUED.
- **POST `/publishing/remove`** (`{ research_product_id, pin_id? }`) —
  `mark_queue_cancelled` + `unqueue_creative_from_publishing` (QUEUED →
  APPROVED), re-enabling editing in Creative Studio.
- **POST `/publishing/schedule`** (`{ pin_id, scheduled_at }`) —
  `mark_queue_scheduled` (status PENDING → READY).
- **POST `/publishing/publish-now`** (`{ pin_id }`) — `fetch_queue_item_details`
  → `publish_pin` → `mark_queue_published` → releases the creative back to
  APPROVED; failure marks FAILED and returns 502.
- **POST `/publishing/board`** (`{ pin_id, board_id }`) —
  `update_queue_board`; `sqlite3.IntegrityError` → 409 "already tied to that
  account and board".
- **GET `/publishing/download/{creative_id}`** — FileResponse of
  `creative_image_path`, served inline (no `filename=` attachment header so
  Next `<Image>` can consume the same URL); 404 for missing path/file.
- **Restored `POST /creatives/reopen`** — its handler body had been left
  dangling at the end of `atlas_api.py` by an earlier edit; reassembled.

## Status Mapping (in `mapPublishItem` / `mapPublication`)

| Backend `pinterest_queue.status` | UI row | Badge |
|---|---|---|
| PENDING | queued (Ready to Publish) | Queued |
| READY | scheduled (Scheduled for date) | Scheduled |
| PUBLISHED / FAILED / CANCELLED | history entry | Published / Failed / Cancelled |

Priority derives from `ai_score` (high/medium/low) with `rating` fallback;
`eventAt` = `published_at ?? scheduled_at ?? queued_at`. The scheduled time
(`scheduled_at`) and selected board (`board_id`) come straight from the DB,
so both survive a refresh.

## Files Created

| File | Purpose |
|---|---|
| `sql/016_seed_publishing_tables.sql` | Seeds 2 accounts (Atlas Home / Atlas Finds), 5 boards with pin/follower counts, 5 `category_routes` (kitchen→(1,2), home→(1,1), pantry→(1,1), bathroom→(2,4), closet→(1,3)) |
| `frontend/src/features/publishing/publishing-api.ts` | `PublishingData` / `PublishingRow` / `PublishingAction` types, `fetchPublishing`, `queueCreative`, `removeCreative`, `schedulePin`, `publishNow`, `updatePinBoard`; mappers `mapPublishItem` / `mapPublication` / `mapBoard`; `creativeImageUrl` via the download endpoint |
| `frontend/src/features/publishing/use-publishing.ts` | `usePublishing` query + 5 mutations; queue/remove/publish-now also invalidate `CREATIVES_QUERY_KEY` so Creative Studio reflects the lock |
| `docs/ATLAS-029-deliverables.md` | This report |

## Files Modified

| File | Change |
|---|---|
| `services/creative_service.py` | Rebuilt `queue_creative_for_publishing` (APPROVED→QUEUED, raises `CreativeLockedError` otherwise), `unqueue_creative_from_publishing` (QUEUED→APPROVED, early-return when not QUEUED), restored `reopen_creative_for_review` (APPROVED→GENERATED, `CreativeLockedError` if QUEUED), added shared `_update_creative_status` + `fetch_creative_image_path` |
| `services/queue_service.py` | `find_cancelled_queue_item`, `reactivate_queue_item` (re-queue reuses CANCELLED rows because of the UNIQUE constraint); `_PUBLISHING_SELECT` extended with affiliate_url/image_url/publish_order/pinterest_description |
| `services/pinterest_boards.py` | `fetch_active_boards()` (all ACTIVE boards across accounts) |
| `services/atlas_api.py` | All `/publishing/*` endpoints above, `GET /publishing` aggregate, restored `/creatives/reopen`; new pydantic models (`PublishingQueueRequest`, `PublishingRemoveRequest`, `PublishingScheduleRequest`, `PublishingPublishNowRequest`, `PublishingBoardRequest`, `PublishingActionResponse`) |
| `frontend/src/features/publishing/publishing-center.tsx` | Rewritten: live data via `usePublishing`, mutations for schedule/publish/board, downloadPin blob handler, loading skeleton + error states, all MOCK_ imports removed |
| `frontend/src/features/publishing/publish-console.tsx` | `onDownload` prop + "Download Pin" ghost button (disabled when `creativeId === null`) |
| `frontend/src/features/publishing/publishing-queue.tsx` | Uses `item.boardName` (dropped BOARD_BY_ID mock import) |
| `frontend/src/features/publishing/publishing-status-badge.tsx` | Added `cancelled` meta (Cancelled, muted) |
| `frontend/src/features/publishing/types.ts` | Added `"cancelled"` PublicationStatus, `boardName`, `creativeId` on PublishItem |
| `frontend/src/features/publishing/mock-data.ts` | Patched with boardName/creativeId purely so `tsc` passes; no longer imported by any live page |
| `frontend/src/features/creatives/creative-studio.tsx` | `queueForPublishing` / `removeFromQueue` now call backend mutations (useQueueCreative / useRemoveCreative) with transient status patch + clearTransient on success/failure |
| `frontend/src/features/creatives/approval-panel.tsx` | "Queue for Publishing" shown only for approved; new "Remove from Queue" button for queued; `onRemoveFromQueue` prop |

## Key Design Decisions

- **Re-queue reuses the CANCELLED row.** `pinterest_queue` has
  `UNIQUE(ai_content_id, account_id, board_id)`, so after "Remove from
  Queue" a fresh insert would violate the constraint. `reactivate_queue_item`
  resets the row to PENDING and clears scheduled/published timestamps.
- **Publish releases the creative lock.** After `mark_queue_published`,
  `unqueue_creative_from_publishing` flips QUEUED → APPROVED so the creative
  becomes editable again once published.
- **Download is inline and reusable.** The download endpoint omits
  `filename=` so there is no `Content-Disposition: attachment` header;
  the frontend "Download Pin" fetches the blob and triggers the anchor
  download client-side.
- **Board conflicts surface as 409** (IntegrityError caught explicitly)
  instead of 500.
- **Future-ready destinations.** Every queued item carries `account_id` +
  `board_id`; nothing is hardcoded to a single account. Category routing
  (`category_routes`) maps each product category to its destination.
- **No redesign.** Every presentational component is reused untouched;
  only data sources and mutation wiring changed.

## Verification

- **Static checks:** `py_compile` clean on all touched services; `npm run
  lint` → 0 errors / 0 warnings; `npx tsc --noEmit` clean; `npm run build`
  → 12 static routes including `/publishing`.
- **Backend live checks** (uvicorn on :8000, seeded gitignored
  `database/atlas.db`):
  - `GET /publishing` → queue + history + summary
    (`{ready: 0, scheduled: 1, published: 3, failed: 0, boards: 5}`) +
    2 accounts + 5 boards.
  - Queue duplicate → 409; schedule unknown pin → 404; publish-now → 200 +
    status PUBLISHED + row moved to history + creative released to APPROVED;
    board change → 200 (and 409 for an account/board collision);
    remove → CANCELLED + creative back to APPROVED.
  - `GET /publishing/download/{1,2}` → 200 `image/png`
    (828305 bytes for creative 1); missing file → 404.
- **Playwright browser QA** (preview URL):
  - Publishing Center renders live data — Scheduled item with board name +
    time, Published History entries, board selector (pin/follower counts),
    Publish Now / Schedule / Download Pin all present; **zero console
    errors**.
  - Board selection round-trip → "Destination set" feedback + persisted
    board; Publish Now round-trip → row moves to history, summary updates,
    **survives reload** (refresh persistence).
  - Download Pin button visible and enabled on queued/scheduled items.
  - Regression: `/`, `/products`, `/content`, `/creatives`, `/publishing`
    all render real content with **zero console errors**.
- **Demo DB state restored** after interactive testing (pin 5 back to
  READY/scheduled, creative 1 back to QUEUED).

## Commands Executed

```bash
cd /workspace/services && python3 -m py_compile atlas_api.py queue_service.py creative_service.py pinterest_boards.py
cd /workspace/frontend && npm run lint
cd /workspace/frontend && npm run build
cd /workspace/frontend && npx tsc --noEmit
cd /workspace/services && python3 -m uvicorn atlas_api:app --port 8000   # background terminal
python3 /tmp/opencode/qa_*.py   # Playwright interaction + persistence + regression suites
```

## Risks / Remaining Limitations

- **`publish_pin` is a simulation stub.** `services/pinterest_client.py`
  returns `True` without calling the Pinterest API; publishing is a real
  persisted state transition but not a real platform write. Wiring the real
  Pinterest API is a follow-up.
- **Full-table fetches.** `/publishing` returns all queue + history rows;
  pagination may be needed at scale (same caveat as ATLAS-027/028).
- **Category routing picks the first route.** The queue endpoint uses
  `routes[0]` (highest priority); manual board override happens afterwards
  via `POST /publishing/board`.
- **Pre-existing test environment limits** (`test_parser.py`,
  `test_bestsellers.py`, `test_discovery.py` need a headful X11 browser,
  and TestClient needs the unavailable `httpx2`) are unchanged and unrelated
  to this sprint.

## Recommendations

- Wire the real Pinterest API into `publish_pin` and add a failure/retry
  path for genuinely failed publishes (the FAILED state + `retry_count`
  column are already in place).
- Consider paginating `/publishing` once history grows.
- Surface `retry_count` / `last_error` on FAILED history entries so the
  user can see why a publish failed.
