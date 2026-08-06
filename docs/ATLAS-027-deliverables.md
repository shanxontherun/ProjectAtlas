# ATLAS-027 — AI Studio: Real Backend Content Deliverables Report

## Summary
Replaced the AI Studio mock catalog with real data from the existing
FastAPI backend. The page is pixel-identical to the mock version — same
summary cards, queue, editor, review decisions, preview modal, toolbar
search/status filters, skeletons, dark/light themes — but every item now
comes from the `research_products` × `ai_content` tables via the existing
backend services, wired with TanStack Query through the `/api` dev proxy.

Generate and approve are real backend round-trips: "Generate AI Content"
calls `POST /ai-content/generate` (which reuses the exact generation +
persistence service the AI worker runs), and "Approve" calls
`POST /ai-content/approve` (which flips `ai_content.status` →
`APPROVED`). The UI keeps its transient in-progress states in the browser,
but the backend always wins on refetch, so a reload reflects persisted
state. The old `content/mock-data.ts` was deleted.

## Backend Reuse Audit (requirement)
| Need | Reused (existing) | Extended | New |
|---|---|---|---|
| Content rows | `ai_content` table (sql/007) | — | — |
| Generation | `generate_ai_content`, `create_ai_content`, `ai_content_exists`, `mark_research_generated`, `get_connection` (`services/database.py`) | — | shared `generate_and_save_ai_content` (`services/ai_service.py`) |
| AI call | `AIClient`, `AIValidationError`, prompt builders (`services/ai_client.py`, `services/ai_prompts.py`) | — | — |
| Product lookup | `research_products` table (sql/004) | — | `fetch_research_product_by_id` (`services/database.py`) |
| Fetch | — | `fetch_ai_content` → single LEFT JOIN of `research_products` × `ai_content` (was ai_content-only) | — |
| Approve | `ai_content.status` (GENERATED / APPROVED / REJECTED) | — | `approve_ai_content` (`services/database.py`) |
| Worker | `workers/ai_worker.py` (main loop unchanged) | now calls the shared `generate_and_save_ai_content`; duplicate create/mark logic removed | — |

No new tables, no schema changes, no parallel content services. The only
new endpoints are thin HTTP wrappers over existing DB functions.

## API Endpoints Used / Added
- **GET `/ai-content`** (new) — `services/atlas_api.py` → reuses the
  enriched `fetch_ai_content()`. Returns every research product LEFT JOINed
  to its AI content (waiting products have `ai_content_id: null`). Maps
  `FileNotFoundError` → 503 and other DB failures → 500, matching the
  sibling `/categories` / `/jobs` / `/research-products` handlers.
- **POST `/ai-content/generate`** (new, body `{ research_product_id }`) —
  resolves the product (404 if missing), then calls the shared
  `generate_and_save_ai_content`. Idempotent: if content already exists it
  returns `200 { success: true, ai_content_id: null }` instead of erroring.
  Maps `AIValidationError` → 422, `sqlite3.Error` → 500, any other AI
  failure → 502 (503 only for missing DB).
- **POST `/ai-content/approve`** (new, body `{ research_product_id }`) —
  calls `approve_ai_content`; 404 when no content exists for the product,
  500 on DB errors.
- **Reused (unchanged):** `/api` dev proxy in `next.config.ts` forwards
  `/ai-content` to the backend (pattern established in ATLAS-026).

## Files Created
| File | Purpose |
|---|---|
| `frontend/src/features/content/content-api.ts` | Wire type `AiContentRow`, `mapAiContent` (derives status/priority/draft from backend fields), `fetchAiContent`, `generateAiContent`, `approveAiContent` |
| `frontend/src/features/content/use-content.ts` | `useContent` query (`queryKey: ["content"]`) + `useGenerateContent` / `useApproveContent` mutations that invalidate `["content"]` |
| `frontend/src/features/content/content-empty-state.tsx` | Friendly error state (reuses `EmptyState`) with "Try again" → `refetch` |
| `docs/ATLAS-027-deliverables.md` | This report |
| `frontend/public/screenshots/ai-studio-backend-*.png` | Verification screenshots (loaded light, dark, generated, approved-persisted, error state) |

## Files Modified
| File | Change |
|---|---|
| `frontend/src/features/content/content-view.tsx` | Drop `MOCK_CONTENT_ITEMS`; use `useContent()`; transient in-browser states for generating/approved/queued/needs-changes that the server overwrites on refetch; `effectiveDraft = working ?? selectedItem?.draft`; error state on `isError`; generate/approve call the real mutations |
| `frontend/src/features/content/mock-data.ts` | **Deleted** (the AI Studio mock catalog) |
| `frontend/src/features/content/content-utils.ts` | Removed the now-dead `generateDraft` mock builder |
| `services/database.py` | `fetch_ai_content()` rewritten as a single LEFT JOIN (`research_products rp` × `ai_content ac`, aliased `research_status` / `content_status` / `research_created_at` / `content_created_at` / `content_updated_at`, exposing `ai_content_id`); added `fetch_research_product_by_id()` and `approve_ai_content()` |
| `services/ai_service.py` | Added `AlreadyGeneratedError` and the shared `generate_and_save_ai_content(product)` (idempotency check → `generate_ai_content` → `create_ai_content` → `mark_research_generated`) |
| `services/atlas_api.py` | Added the 3 AI-content endpoints, `AiContentGenerateRequest` / `AiContentApproveRequest` / `AiContentActionResponse` models, and a `sys.path` shim so `services.*` imports resolve when run from `services/` |
| `workers/ai_worker.py` | Now calls the shared `generate_and_save_ai_content` + `AlreadyGeneratedError`; removed its duplicated create/mark logic (external behavior unchanged) |
| `CHANGELOG.md` | Added `[0.8.0]` (ATLAS-027) |
| `JOURNAL.md` | Added 2026-08-06 (ATLAS-027) session log |

## DB Changes
- **Schema:** none — `ai_content` (sql/007) already exists with
  `status` CHECK (GENERATED / APPROVED / REJECTED) and all content fields
  the UI renders. Approve reuses that existing status column.
- **Query:** `fetch_ai_content()` went from ai_content-only rows to a
  LEFT JOIN so the AI Studio queue can render products with no content yet
  ("waiting") in the same payload as generated ones.
- **Data (verification only):** created `database/atlas.db` (gitignored) by
  running `scripts/run_migrations.py`; seeded 10 research products via the
  real `POST /jobs` + `/research-products` endpoints covering NEW /
  GENERATED / QUEUED / PUBLISHED / FAILED, generated content for several
  through the real `/ai-content/generate` endpoint, and approved one.
  Throwaway seed data in a gitignored DB.

## Status Derivation (client-side, in `mapAiContent`)
| Backend fields | UI status | UI badge |
|---|---|---|
| `research_status` = QUEUED or PUBLISHED | queued | Queued |
| `content_status` = APPROVED | approved | Approved |
| `ai_content_id` is not null (content GENERATED) | needs-review | Needs Review |
| no content (`ai_content_id` null) | waiting | Waiting |

Priority comes from `ai_score` (≥85 high / ≥70 medium / else low), falling
back to `rating`, then `medium`. Draft fields map `pinterest_title` →
title, `pinterest_description` → description, `pinterest_keywords` →
hashtags, `ai_score` → seoScore. The `pinterest_*`/`ai_score` fields were
already columns in `ai_content` — the UI's mock draft shape was a superset
the backend already modeled.

## Design Decisions
- **Reuse, don't duplicate:** generation, persistence, validation, and the
  approve status flip all reuse existing DB functions; the AI worker and
  the API share one `generate_and_save_ai_content` service so behavior
  can't drift between background and on-demand generation.
- **One joined endpoint instead of a parallel API:** the AI Studio needed
  products with their content in one fetch; extending `fetch_ai_content`
  with a LEFT JOIN avoids a new research-products-AI endpoint and keeps
  `GET /ai-content` the single source for the page.
- **Derivation stays client-side:** status/priority are presentation
  concepts; the mapper derives them next to the badges they render. Backend
  remains the raw-data authority (`research_status`/`content_status`).
- **Transient UI states never fake persistence:** generating / approved /
  queued / needs-changes are ephemeral in React state; mutations write to
  the DB and the query invalidates, so the server data is what a reload
  shows. Approved and queued states therefore survive a refresh.
- **No redesign:** every presentational component (queue, editor, approval
  bar, preview, toolbar, summary, skeleton, badges) is reused untouched.
  The error state mirrors the `EmptyState` pattern from ATLAS-026.
- **Schema untouched:** approve flips the existing `ai_content.status`
  column; no new status column or table was introduced.

## Assumptions
- `ai_content.pinterest_*` + `ai_score` are the canonical "Pinterest-ready
  content" fields and map 1:1 to the mock draft (title / description /
  hashtags / CTA / SEO score). `cta` is a fixed "Shop on Amazon" constant
  (the table has no CTA column); the client editor can still edit it.
- `board_name`, `instagram_caption`, `blog_summary`, `seo_title` stay in
  the payload (backward compatible) but are not rendered by the current
  AI Studio UI.
- All research products appear in the queue (including FAILED → waiting),
  matching the mock behavior where products without content sit in Waiting.
- Real AI generation works when `AI_BASE_URL` / `AI_API_KEY` / `AI_MODEL`
  are configured in the runtime environment; local verification used a
  stub OpenAI-compatible server on the `AIClient` default port.

## Risks
- **Stale statuses:** the queue ordering relies on `research_products.status`
  being advanced (QUEUED/PUBLISHED) by workers for the queued badge; if
  workers don't yet write those statuses, products will show as
  needs-review/waiting. Same caveat as ATLAS-026.
- **Generate is now an upsert:** `POST /ai-content/generate` regenerates an
  existing product (updates the row in place) and returns the updated
  content; the UI's Regenerate button drives this flow. The worker path
  remains idempotent via `generate_and_save_ai_content`.
- **Approve has no undo:** `approve_ai_content` only moves GENERATED →
  APPROVED; there is no UI to move APPROVED back to GENERATED yet. The
  "Needs Changes" / "Queue" actions are client-side presentation today.
- **Full-table fetch:** `GET /ai-content` returns every research product;
  fine at current scale, a paginated endpoint may be needed later.
- **Pre-existing import duplication:** `services/research_products.py` also
  defines `fetch_all_research_products`; the new code follows the
  `services.database` import path used by `atlas_api.py`. Left as-is but
  still flagged for consolidation.

## Verification
- Backend (real endpoints against seeded DB):
  - `GET /ai-content` → 200, all 10 rows, 6 with `ai_content_id`, 4 with
    `ai_content_id: null`; queued items carry QUEUED/PUBLISHED research
    status.
  - `POST /ai-content/generate` → 200 + `ai_content_id` for a waiting
    product; repeat call → 200 + `ai_content_id: null` (idempotent).
  - `POST /ai-content/generate` missing product → 404.
  - `POST /ai-content/approve` → 200; approve a product with no content →
    404.
- Frontend static checks: `npm run lint` → 0 errors / 0 warnings;
  `npx tsc --noEmit` → clean after `npm run build`; `npm run build` →
  compiled + type-checked clean (12 static routes). (Pre-existing
  `LayoutProps` errors resolve after build generates `.next/types` — Next 16
  behavior, unrelated to ATLAS-027.)
- Playwright (preview URL, `content-check.cjs`): **19/19** checks pass —
  skeleton, 10 queue items from backend, status derivation per row
  (waiting/needs-review/approved/queued), summary metric cards match
  backend counts, editor loads the backend draft, Improve client action,
  search filter, status filter, preview dialog, dark→light→dark toggle,
  Generate AI Content round-trip (waiting → needs-review, persisted),
  Approve round-trip (→ approved), status persists after reload, `/products`
  unaffected, zero page errors.
- Error state: backend killed → "Unable to load AI content" + Try again
  renders; backend restarted (and first-request-failure simulated via
  request interception) → Try again reloads all 10 items.
- No references to `content/mock-data` or `MOCK_CONTENT_ITEMS` remain
  (other features keep their own out-of-scope mocks).
- Screenshots captured in `frontend/public/screenshots/`
  (`ai-studio-backend-*`: loaded light, desktop dark, generated, approved
  persisted, error state).

## Commands Executed
```bash
cd /workspace && python3 scripts/run_migrations.py        # create gitignored atlas.db
python3 /tmp/opencode/stub_ai.py                          # local OpenAI-compatible stub for verification
cd /workspace/services && python3 -m uvicorn atlas_api:app --host 127.0.0.1 --port 8000
cd /workspace/frontend && npm run lint                    # 0/0
cd /workspace/frontend && npm run build                   # 12 static routes
cd /workspace/frontend && npm run dev                     # port 3000 (Turbopack)
node /tmp/opencode/content-check.cjs                      # 19/19
node /tmp/opencode/content-error-check.cjs                # 1/1 (backend down)
node /tmp/opencode/content-recover-check.cjs              # 1/1 (Try again recovery)
```

## Recommendations
- Wire Creative Studio and Publishing to real backend data with the same
  `useQuery` + mapper pattern once their workers write statuses; AI Studio
  is now the reference for a full generate→review→approve loop.
- When the AI gateway is configured in the runtime, re-run verification
  against real generations (the local stub only proves the wiring).
- Move `cta` and any approval/undo semantics into the backend contract if
  "Needs Changes"/"Queue" should persist across sessions rather than being
  presentation-only.
- Consolidate the duplicate `fetch_all_research_products` implementations
  (`database.py` vs `services/research_products.py`).

## Engineering Handoff Completion (Stabilization)

Completion of the engineering handoff. The existing architecture was
preserved end to end: Products → TanStack Query → Backend API → SQLite.
No services, workers, worker scheduling, or UI components were renamed,
redesigned, or replaced. The AI worker remains idempotent — it still only
generates content for products that have no AI content. Manual regeneration
is a separate user action that goes through the HTTP API, not the worker.

### QA Fixes

| # | Issue | Fix |
|---|---|---|
| 1 | Regenerate appended text to the description (client-side mock `regenerateDraft` used `appendSentence`) | Regenerate is now a real backend round-trip. The editor's Regenerate button calls `POST /ai-content/generate`; the backend regenerates content and **replaces** the existing `ai_content` row in place. The dead client-side `regenerateDraft` append mock was removed. |
| 2 | Persistence after refresh | Generation/regeneration write to SQLite inside the shared service (INSERT or UPDATE + commit). `GET /ai-content` is the single source, so a browser refresh always shows the latest persisted row. Regeneration now actually persists a change (it previously returned a silent no-op). |
| 3 | Manual regenerate must UPDATE the existing row (no duplicates / no extra rows / no appended text) | New `update_ai_content` (`services/database.py`) UPDATEs the single existing row, overwriting every content field and resetting `status` → `GENERATED`, `validation_status` → `PENDING`. `POST /ai-content/generate` upserts: content exists → update; no content → insert. Verified: the same `ai_content_id` survives repeated regenerate calls; `ai_content` row count stays 1 per product. |
| 4 | Repetitive AI output | Root cause: the local OpenAI-compatible stub returned static canned content on every call. Atlas prompt building and payload flow are correct (see Root Cause Analysis). No engineering effort spent "improving" the temporary stub. |
| 5 | Product mismatch (Laundry Bag → "Kitchen Drawer Ideas") | Root cause: the same static stub ignored the prompt and returned fixed "Kitchen Drawer Ideas" JSON regardless of product. Not an Atlas mapping/payload bug — `build_prompt` correctly injects `product_name`/`category`/etc., and `fetch_research_product_by_id` returns the right row. Confirmed with a dynamic stub that derives content from the prompt. |

### Root Cause Analysis

- **Regenerate appending (Issue 1).** The editor's `regenerate` action was a
  pure client-side mock (`regenerateDraft` in `content-utils.ts`) that called
  `appendSentence`, so each click appended a closer sentence to the existing
  description. Independently, the backend `POST /ai-content/generate` was
  idempotent: when content already existed it returned
  `{ success: true, ai_content_id: null }` and did nothing. The two combined
  meant "Regenerate" never touched the database and only visually appended
  text in the browser.
- **Silent no-op (Issue 2/3).** The idempotent generate could not update an
  existing row, so a refresh "restored" the previous content. The fix gives
  the endpoint upsert semantics while keeping the worker's idempotent
  `generate_and_save_ai_content` untouched.
- **Repetitive output (Issue 4).** Reproduced with a static stub: identical
  content returned for every request. The Atlas path (prompt → AIClient →
  `parse_json_response` → validation → persistence) carries the correct
  product context in the prompt. A dynamic stub that varies the response
  produced unique, product-specific content per call. Conclusion: temporary
  stub behaviour, not Atlas logic.
- **Product mismatch (Issue 5).** Reproduced exactly: selecting Storage Bins /
  Shelf Liner with the static stub returned "Kitchen Drawer Ideas" content.
  The stub never reads the prompt. The same products generated correct
  content with the dynamic stub. Conclusion: temporary stub behaviour.

### Logging

Structured development logging added around AI generation
(`services/ai_service.py`), gated by `ATLAS_DEV_LOG` (default on in dev,
off with `ATLAS_DEV_LOG=0`). One JSON line per event:
- `ai_generate_start` — research product id, product name, mode (`create`/`update`)
- `ai_generate_request` — the prompt sent to the model
- `ai_generate_response` — raw model response + duration ms
- `ai_db_update` — research product id, `ai_content_id`, mode, duration ms

### Files Modified

| File | Change |
|---|---|
| `services/database.py` | Added `update_ai_content` (in-place replace, status reset); `fetch_ai_content` gained an optional `research_product_id` filter so the API can return the updated row after generate/regenerate |
| `services/ai_service.py` | Added `regenerate_and_save_ai_content` (manual update path, worker untouched); structured dev logging helper + events |
| `services/atlas_api.py` | `POST /ai-content/generate` is now an upsert (update existing row / create new row) and returns the updated `content` row; `AiContentActionResponse` gained an optional `content` field |
| `frontend/src/features/content/content-view.tsx` | Editor "Regenerate" calls the backend generate mutation, applies the returned content to the editor buffer, invalidates the query; editor is read-only while a generation is pending |
| `frontend/src/features/content/content-api.ts` | `generateAiContent` / `approveAiContent` now return the typed `AiContentAction` (including the updated content row) |
| `frontend/src/features/content/content-utils.ts` | Removed the dead client-side `regenerateDraft` append mock |
| `docs/ATLAS-027-deliverables.md` | This report |

### Verification

- Backend (real endpoints, dynamic stub, `database/atlas.db`):
  - `POST /ai-content/generate` on a waiting product → 200, row created,
    `ai_content_id` returned, content reflects the product.
  - Repeat `POST /ai-content/generate` on the same product ×2 → 200, **same**
    `ai_content_id`, content replaced (`version 1` → `2` → `3`), description
    is exactly the latest version (no appended text), `created_at` unchanged
    while `updated_at` advanced.
  - DB: `ai_content` holds exactly one row per product; no duplicate rows.
  - `POST /ai-content/approve` → 200, `status` → `APPROVED`; refresh
    (`GET /ai-content`) returns APPROVED (persistence).
  - `POST /ai-content/generate` missing product → 404; approve with no
    content → 404.
  - Static stub reproduced both original issues (repetitive + mismatched
    output); dynamic stub produced correct per-product content.
- Structured logs confirmed in the API server output (start/request/
  response/db-update with duration).
- Frontend:
  - `npm run lint` → 0 errors / 0 warnings.
  - `npx tsc --noEmit` → clean (after build; the two `LayoutProps` errors are
    pre-existing Next 16 behaviour that resolves once `.next/types` is
    generated).
  - `npm run build` → compiled + type-checked clean, 12 static routes.
  - `/content` and `/products` pages return 200; `/api/ai-content` proxy
    forwards to the backend (3 rows, statuses APPROVED / GENERATED /
    GENERATED).
- Preview: https://3000-986d15586d0e92b4.monkeycode-ai.live (dev server +
  API + stub running).

### Remaining Limitations

- **Regenerate resets review state.** Replacing content also resets the
  `ai_content` status to GENERATED (and validation to PENDING) so the new
  content must be re-reviewed; a previously APPROVED product returns to
  "Needs Review" after regeneration. This is intended behaviour for a
  content replacement.
- **Local AI stub.** The verification stub returns deterministic canned or
  template-derived content. Real generation quality (and the actual
  "repetitive output"/"mismatch" reports) must be re-validated against the
  real AI gateway with `AI_BASE_URL` / `AI_API_KEY` / `AI_MODEL` configured.
  No effort was spent improving the temporary stub.
- **Approve has no undo.** `approve_ai_content` only moves GENERATED →
  APPROVED; there is still no API to move APPROVED back to GENERATED.
  "Needs Changes" / "Queue" remain client-side presentation only.
- **No worker involvement in regeneration.** Manual regenerate only writes
  through the API path; if a worker is mid-flight for the same product the
  two writes can race (last writer wins, no duplicate rows because of the
  single-row upsert).
- **Full-table fetch.** `GET /ai-content` returns every research product; a
  paginated endpoint may be needed at scale.
