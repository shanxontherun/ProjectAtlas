# ATLAS-028 — Creative Studio: Real Backend Content Deliverables Report

## Summary

Wired Creative Studio to the real FastAPI backend, following the exact
architecture of ATLAS-027 (AI Studio). The page keeps its existing UI —
summary cards, queue, preview, template gallery, variant gallery,
properties panel, readiness checklist, approval panel, skeletons, and
dark/light themes — but every queue item now comes from the
`research_products` × `ai_content` × `creative_assets` tables through a
single joined read model, fetched with TanStack Query through the `/api`
dev proxy.

Generate and approve are real backend round-trips: "Generate Creatives"
calls `POST /creatives/generate` (which reuses the exact rendering +
persistence pipeline the creative worker runs — image resolution, content
mapping, `RenderingEngine`), and "Approve" calls `POST /creatives/approve`
(which flips `creative_assets.status` → `APPROVED`). The UI keeps its
transient in-progress states in the browser, but the backend always wins on
refetch, so a reload reflects persisted state.

## Architecture (reference: ATLAS-027)

```
SQLite
  ↓
FastAPI (services/atlas_api.py → services/creative_service.py)
  ↓
creative-api.ts  (mapCreative + fetchCreatives / generateCreative / approveCreative)
  ↓
use-creatives.ts (useCreatives / useGenerateCreative / useApproveCreative)
  ↓
TanStack Query
  ↓
Creative Studio (creative-studio.tsx)
```

## Backend Reuse Audit (requirement)

| Need | Reused (existing) | Extended | New |
|---|---|---|---|
| Creative rows | `creative_assets` table (sql/013) | — | — |
| Rendering | `RenderingEngine`, `TemplateRegistry`, `layout_text`, `FontResolver` (`creative/`) | — | — |
| Image resolution | per-ASIN product images under `storage/products/amazon/<asin>/original.jpg` | — | `resolve_local_product_image` (`services/creative_service.py`) |
| AI content source | `ai_content` + `research_products` tables | — | `fetch_creatives_workflow` (single joined read model) |
| Generate (API) | creative worker building blocks | — | shared `generate_and_save_creative` (idempotent, used by the API path) |
| Generate (worker) | `workers/creative_worker.py` (unchanged) | — | — |
| Approve | `creative_assets.status` (GENERATED / APPROVED / FAILED) | — | `mark_creative_approved` / `approve_creative_for_product` |
| Fetch | — | — | `fetch_creatives_workflow(research_product_id=None)` |

No new tables, no schema changes, no parallel creative services, and the
worker's external behaviour is untouched. The only new endpoints are thin
HTTP wrappers over the creative-service + rendering pipeline.

## API Endpoints Used / Added

- **GET `/creatives`** (new) — `services/atlas_api.py` → reuses
  `fetch_creatives_workflow()`. Returns every research product with AI
  content, LEFT JOINed to its creative (waiting items have
  `creative_id: null`). Maps `FileNotFoundError` → 503 and other DB
  failures → 500, matching the sibling `/ai-content` handler.
- **POST `/creatives/generate`** (new, body `{ research_product_id }`) —
  resolves the product's AI content (404 if none), resolves the local
  product image, maps content, renders via `RenderingEngine`, and persists
  a `creative_assets` row in `GENERATED` state. Idempotent: an existing
  non-FAILED creative is returned unchanged and never rendered twice; a
  FAILED creative is replaced so manual retry produces a fresh render.
  Maps `CreativeContentNotFoundError` → 404, `sqlite3.Error` → 500, other
  render/IO failures → 502 (503 only for missing DB).
- **POST `/creatives/approve`** (new, body `{ research_product_id }`) —
  flips the product's latest `creative_assets.status` → `APPROVED`; 404
  when no creative exists.
- **Reused (unchanged):** `/api` dev proxy in `next.config.ts` forwards
  `/creatives` to the backend (pattern established in ATLAS-026/027).

## Status Derivation (client-side, in `mapCreative`)

| Backend fields | UI status | UI badge |
|---|---|---|
| `creative_status` = APPROVED | approved | Approved |
| `creative_status` = QUEUED | queued | Queued |
| `creative_id` is not null and `creative_status` = FAILED | waiting | Waiting (retryable) |
| `creative_id` is not null | needs-review | Needs Review |
| no creative (`creative_id` null) | waiting | Waiting |

Priority comes from `ai_score` (≥85 high / ≥70 medium / else low), falling
back to `rating`, then `medium`. Headline maps `pinterest_title` (falling
back to a product-name-derived headline); the other preview properties
(CTA/brand/logo/overlay) stay at the UI defaults.

## Files Created

| File | Purpose |
|---|---|
| `frontend/src/features/creatives/creative-api.ts` | Wire type `CreativeWorkflowRow`, `mapCreative` (derives status/priority/headline from backend fields), `fetchCreatives`, `generateCreative`, `approveCreative` |
| `frontend/src/features/creatives/use-creatives.ts` | `useCreatives` query (`queryKey: ["creatives"]`) + `useGenerateCreative` / `useApproveCreative` mutations that invalidate `["creatives"]` |
| `frontend/src/features/creatives/creative-empty-state.tsx` | Friendly error state (reuses `EmptyState`) with "Try again" → `refetch` |
| `docs/ATLAS-028-deliverables.md` | This report |
| `frontend/public/screenshots/creative-studio-backend-*.png` | Verification screenshots (loaded light, dark, generated, approved persisted) |

## Files Modified

| File | Change |
|---|---|
| `frontend/src/features/creatives/creative-studio.tsx` | Drop mock item source; use `useCreatives()`; transient in-browser states for generating/approved/queued that the server overwrites on refetch; `generateWaiting` and `approve` call the real mutations; error state on `isError` |
| `frontend/src/components/layout/theme-toggle.tsx` | Stabilization: mounted-guard (via `useSyncExternalStore`) so the aria-label no longer differs between SSR and client, eliminating the pre-existing next-themes hydration-mismatch console error on every page |
| `frontend/src/features/creatives/creative-utils.ts` | Removed the now-dead `buildCreativeItem` mock builder and its `DEFAULT_PROPERTIES` constant (same cleanup ATLAS-027 did for `generateDraft`) |
| `CHANGELOG.md` | Added `[0.9.0]` (ATLAS-028) |
| `JOURNAL.md` | Added 2026-08-07 (ATLAS-028) session log |

## Backend Implementation (verified, completed by the sprint)

- `services/creative_service.py` — creative assets data layer: `create_creative`,
  `fetch_creative`, `fetch_creatives_by_ai_content`, `fetch_creatives_workflow`,
  `fetch_creative_content_for_product`, `fetch_pending_creative_content`,
  `resolve_local_product_image`, `build_render_content`,
  `mark_creative_generated/approved/failed`, `record_creative_failure`,
  `delete_creative`, and the shared `generate_and_save_creative`
  (idempotent single entry point for the manual API path).
- `services/atlas_api.py` — the three `/creatives` endpoints above plus
  `CreativeGenerateRequest` / `CreativeApproveRequest` /
  `CreativeActionResponse` models; reuses the existing `sys.path` shim.
- `workers/creative_worker.py` — unchanged; still idempotent (only renders
  validated AI content with no existing creative) — reuses
  `fetch_pending_creative_content` + `creative_exists`.
- `sql/013_create_creative_assets.sql` — `creative_assets` table (already
  in the migration set; no schema change this sprint).

## Verification

- Backend (real endpoints against the seeded, gitignored `database/atlas.db`):
  - `GET /creatives` → 200, 6 rows (products with AI content): 2 APPROVED,
    3 GENERATED, 1 waiting (`creative_id: null` / FAILED).
  - `POST /creatives/generate` on a waiting product → 200 + `creative_id`,
    `creative_assets` row in GENERATED, rendered PNG written to
    `creative/generated/`. Repeat call → 200 with the **same** `creative_id`
    (idempotent, never re-renders).
  - `POST /creatives/generate` on a product with no AI content → 404;
    unknown product → 404.
  - `POST /creatives/approve` → 200, `creative_assets.status` → APPROVED;
    refresh (`GET /creatives`) returns APPROVED (persistence); product with
    no creative → 404.
- Frontend static checks: `npm run lint` → 0 errors / 0 warnings;
  `npx tsc --noEmit` → clean (after `npm run build` generates `.next/types`;
  the two pre-existing `LayoutProps` errors resolve exactly as documented in
  ATLAS-027); `npm run build` → compiled + type-checked clean (12 static
  routes including `/creatives`).
- Playwright (preview URL, `creative-check.py`): **27/27** checks pass —
  queue populated from the backend (6 items), summary metric cards match
  backend counts (Waiting=1 / Generating=0 / Needs Review=3 / Approved=2 /
  Queued=0), per-row status derivation, preview renders the backend
  headline, Generate Creatives round-trip (waiting → needs-review),
  Approve round-trip (→ approved), status persists after reload, `/products`
  and `/content` unaffected, **zero console errors** on `/creatives`,
  `/products`, and `/content` (after the theme-toggle hydration fix).
- Error state: backend killed → "Unable to load creatives" + "Try again"
  renders; backend restarted → queue renders again (2/2 recovery checks).
- Regression: `/publishing` and `/dashboard` render with zero console
  errors (the dashboard's first h1 is the time-based "Good morning"
  greeting by design).
- Backend smoke tests: `tests/test_creative_worker.py` and
  `tests/test_creative_rendering.py` → **all checks passed** (worker
  idempotency, failure recording, deterministic rendering). `test_ai_client.py`
  passes against the local stub. `test_parser.py` / `test_bestsellers.py` /
  `test_discovery.py` require an X11 browser and cannot run headless —
  pre-existing environment limitation, unrelated to ATLAS-028.
- Screenshots captured in `frontend/public/screenshots/`
  (`creative-studio-backend-*`: loaded light, dark, generated, approved).

## Commands Executed

```bash
cd /workspace && python3 scripts/run_migrations.py            # create gitignored atlas.db
python3 /tmp/opencode/stub_ai.py                              # local OpenAI-compatible stub (port 20128)
cd /workspace/services && python3 -m uvicorn atlas_api:app --host 127.0.0.1 --port 8000
cd /workspace && python3 /tmp/opencode/seed_creatives.py      # seed products + AI content via real API
cd /workspace && python3 /tmp/opencode/seed_creatives2.py     # set ASINs + generate/approve creatives via real API
cd /workspace/frontend && npm run lint                        # 0/0
cd /workspace/frontend && npm run build                       # 12 static routes
cd /workspace/frontend && npx tsc --noEmit                    # clean after build
cd /workspace/frontend && npm run dev                         # port 3000 (Turbopack)
python3 /tmp/opencode/creative-check.py <preview-url>         # 27/27
python3 /tmp/opencode/creative-error-check.py <preview-url>   # error state (backend down)
python3 /tmp/opencode/creative-recover-check.py <preview-url> # recovery after backend restart
python3 /tmp/opencode/creative-regression-check.py <preview-url>  # publishing/dashboard
python3 tests/test_creative_worker.py && python3 tests/test_creative_rendering.py  # smoke tests
```

## Design Decisions

- **Reuse, don't duplicate:** rendering, image resolution, content mapping
  and persistence all reuse the creative engine + repository layer; the
  creative worker and the API share the same building blocks via
  `generate_and_save_creative`, so behaviour can't drift between batch and
  on-demand generation (mirrors ATLAS-027's `generate_and_save_ai_content`).
- **One joined endpoint instead of a parallel API:** the Creative Studio
  needed products with their AI content and creative in one fetch;
  `fetch_creatives_workflow` (INNER `research_products`→`ai_content`, LEFT
  `ai_content`→`creative_assets`) keeps `GET /creatives` the single source
  for the page.
- **Derivation stays client-side:** status/priority are presentation
  concepts; the mapper derives them next to the badges they render. Backend
  remains the raw-data authority (`creative_status` / `ai_status`).
- **Transient UI states never fake persistence:** generating / approved /
  queued are ephemeral in React state; mutations write to the DB and the
  query invalidates, so the server data is what a reload shows. Approved
  and queued states therefore survive a refresh.
- **No redesign:** every presentational component (queue, preview, template
  gallery, variant gallery, properties panel, score, recommendation,
  readiness checklist, approval panel, summary, skeleton) is reused
  untouched. The error state mirrors the `EmptyState` pattern.
- **Worker untouched and idempotent:** `workers/creative_worker.py` still
  renders only validated AI content with no creative yet. Manual
  generation/retry is a separate user action through the HTTP API.
- **Schema untouched:** approve flips the existing `creative_assets.status`
  column; no new table or status column was introduced.
- **Stabilization only:** the theme-toggle hydration guard and dead-code
  removal in `creative-utils.ts` are the only code edits this sprint; both
  were required to hit the "zero console errors" and lint-clean criteria.

## Assumptions

- A creative can only be generated for a product that has already produced
  AI content (Creative Studio consumes AI Studio output). Products without
  AI content do not appear in the queue.
- Products carry an ASIN in the DB (populated by the discovery worker via
  `services/research_products.py`) and have a local image at
  `storage/products/amazon/<asin>/original.jpg`; the API's legacy
  `POST /research-products` path does not set ASINs (seeding mirrors the
  discovery worker by writing ASINs directly).
- The preview is a CSS-composed pin using the backend product image +
  backend headline; the rendered PNG path is persisted on the backend but
  not yet surfaced in the UI (template/variant switching stays a client
  presentation concept).
- Real rendering works headless because `FontResolver` falls back to the
  Pillow default font when bundled fonts are absent.
- Real AI generation works when `AI_BASE_URL` / `AI_API_KEY` / `AI_MODEL`
  are configured in the runtime environment; local verification used the
  OpenAI-compatible stub on the `AIClient` default port (20128).

## Risks / Remaining Limitations

- **Preview still CSS-composed.** The queue, generate, approve, refresh and
  persistence flows are fully backend-driven, but the preview canvas renders
  a CSS pin from the product image + backend headline rather than the
  backend-rendered PNG (`creative_image_path`). Surfacing the rendered asset
  is a natural follow-up.
- **Approve has no undo.** `approve_creative_for_product` only moves
  GENERATED/FAILED → APPROVED; there is no API to move APPROVED back to
  GENERATED. "Queue" remains client-side presentation today.
- **Retry replaces the FAILED row.** Generating over a FAILED creative
  deletes the failed row and inserts a fresh one (new `creative_id`); the
  failure message is lost on retry. This keeps one row per AI content and
  matches the worker's idempotency contract.
- **Race on manual regenerate.** If the worker is mid-flight for the same
  AI content, the API generate and worker can both write (last writer wins);
  the single-row-per-AI-content contract avoids duplicates.
- **Full-table fetch.** `GET /creatives` returns every product with AI
  content; a paginated endpoint may be needed at scale (same caveat as
  ATLAS-027).
- **Stray migration file.** `database/migrations/017_create_creative_assets.sql`
  duplicates `sql/013` and is not run by `scripts/run_migrations.py` (which
  reads only `sql/`). Harmless leftover, flagged for cleanup.
- **Pre-existing test environment limits.** `test_parser.py`,
  `test_bestsellers.py` and `test_discovery.py` require a headful X11
  browser and cannot run headless; unrelated to ATLAS-028.

## Recommendations

- Surface the backend-rendered PNG (`creative_image_path`) in the preview
  once a product's creative is generated, keeping the CSS composition as
  the pre-generation design mock.
- Add an API to move an APPROVED creative back to GENERATED (undo), and
  persist the "Queue" action if it should survive a refresh.
- Re-run verification against the real AI gateway and real product imagery
  when `AI_BASE_URL` / `AI_API_KEY` / `AI_MODEL` and downloaded product
  images are available (the local stub + test.jpg only prove the wiring).
- Remove the stray `database/migrations/017_create_creative_assets.sql`
  duplicate.

## QA Stabilization

Local QA surfaced workflow-integrity bugs around approval persistence and
editing. This stabilization sprint fixed them with minimal, surgical
changes (no redesign, no schema duplication).

### Root Cause

- **Approved creatives stayed editable.** The editor's read-only flag was
  driven only by `status === "queued"`, so approved creatives could still
  change headline, template, variant, properties, regenerate and re-approve.
- **Variant/template selection was frontend-only.** `CreativeItem` carried
  `selectedVariant` / `templateId` as browser state; `mapCreative` always
  fell back to Variant A / Minimal. The backend persisted neither selection,
  so any refresh (including after approve) reset the editor to defaults.
- **Editorial decisions were not persisted.** `creative_assets` had no
  columns for the selected template, variant, or lightweight properties, so
  the backend could not be the source of truth for what was approved.

### Files Modified

- `sql/015_add_creative_presentation.sql` — additive migration extending
  `creative_assets` (no duplicate table).
- `services/creative_service.py`:
  - `CreativeLockedError` — server-side guard for editing approved/queued.
  - `update_creative_presentation` / `save_creative_presentation` — persist
    template, variant, headline and properties; reject edits to approved or
    queued creatives (HTTP 409).
  - `approve_creative_for_product` now persists the approved presentation
    before flipping status to `APPROVED`.
  - `generate_and_save_creative` accepts an optional presentation payload.
  - `fetch_creatives_workflow` now returns `creative_headline`,
    `selected_template`, `selected_variant`, `creative_properties`.
- `services/atlas_api.py`:
  - `CreativePresentation` request model shared by generate / approve / save.
  - New `POST /creatives/save` endpoint for pre-approval Studio edits.
  - `POST /creatives/generate` and `POST /creatives/approve` accept an
    optional `presentation` payload.
- `frontend/src/features/creatives/creative-api.ts` — `CreativeWorkflowRow`
  gains the persisted fields; `mapCreative` restores template/variant/
  properties from the backend and never falls back to a hardcoded default
  when backend state exists; adds `saveCreative` + `buildPresentationPayload`.
- `frontend/src/features/creatives/use-creatives.ts` — adds `useSaveCreative`;
  generate/approve mutations pass the presentation payload.
- `frontend/src/features/creatives/creative-studio.tsx` — persists template,
  variant and property edits via a debounced save (600 ms); carries the
  current presentation into approve; clears transient state after a
  successful approve so the backend row drives the restored UI; guards all
  editors against locked items.
- `frontend/src/features/creatives/approval-panel.tsx` — Regenerate,
  Generate Variants and Approve are now disabled for approved creatives;
  Queue for Publishing stays enabled; approved hint reads "queue it for
  publishing".
- `frontend/src/features/creatives/properties-panel.tsx` — read-only mode now
  covers approved creatives (headline, CTA, brand, logo position, overlay).
- `frontend/src/features/creatives/template-gallery.tsx` / `variant-gallery.tsx`
  — buttons disabled for approved and queued creatives.

### Database Changes

- `creative_assets` extended with three nullable columns (additive, no new
  tables, no data migration needed):
  - `selected_template TEXT`
  - `selected_variant TEXT`
  - `properties_json TEXT` — JSON-encoded `cta`, `brand`, `logoPosition`,
    `overlayStyle`.
- `headline` already existed; it is now treated as the persisted editorial
  headline and restored as such.
- Existing rows keep NULL presentation columns; the frontend restores
  defaults only when the backend genuinely has no saved state.

### Verification

- `npm run lint` — clean.
- `npx tsc --noEmit` — clean.
- `npm run build` — clean (12 routes).
- Backend API round-trips (via `curl`):
  - `POST /creatives/save` persists template/variant/properties and GET
    `/creatives` returns them.
  - `POST /creatives/approve` with a presentation persists status + state;
    a subsequent GET restores exactly.
  - `POST /creatives/save` on an approved creative returns `409`.
- Playwright browser QA (`creative-persistence-check.py`, preview URL):
  25/25 passed covering:
  - needs-review item: edit Variant C → refresh → Variant C + Lifestyle
    restored (pre-approval persistence).
  - approve with Variant C → refresh → still Approved, Variant C active,
    headline value restored exactly, headline/template/variant/regenerate/
    generate-variants/approve all locked, Queue for Publishing enabled,
    zero console errors.
  - pre-approved item (Variant C / Lifestyle): same read-only restore
    verified.
- Playwright regression (`creative-regression-final.py`): 12/12 — queue
  counts match the canonical seed (Waiting=1, Needs Review=3, Approved=2,
  Queued=0) and `/products`, `/content`, `/publishing` render with zero
  console errors.

### Remaining Limitations

- **Queue action is still client-side.** "Queue for Publishing" updates the
  UI transiently; the backend has no QUEUED transition yet. Approved items
  are now immutable, so queue-publishing an approved creative is the
  documented next workflow step.
- **Preview canvas still CSS-composed.** The read-only and restore logic is
  fully backend-driven, but the preview renders a CSS pin rather than the
  rendered PNG (`creative_image_path`); unchanged from the prior sprint.

## ATLAS-028A — Editorial Workflow Enhancement

Approved creatives can now be safely returned to review before they are
queued or published, so an accidental approval is no longer a dead end.

### Root Cause

Approval was a one-way trap. Once `status` moved to `APPROVED` the creative
became immutable with no way to resume editing, forcing a user to lose the
approval (and their editorial decisions) if they clicked Approve by mistake.

### Workflow Changes

- Approved creatives remain read-only and show the new **Return to Review**
  action alongside **Queue for Publishing**.
- The stale disabled Regenerate / Generate Variants / Approve buttons are
  no longer rendered for approved creatives — the action area reflects the
  current workflow state instead.
- **Return to Review** opens a confirmation dialog ("Return creative to
  review?") explaining that the creative will be unlocked and must be
  approved again before publishing.
- Confirming transitions the creative back to the editable review state
  (`APPROVED -> GENERATED`, the existing review status) with **all editorial
  decisions preserved** — headline, description, CTA, template, variant,
  overlay, logo position, properties. Only the workflow status changes.
- Once reverted, the editor fully unlocks (headline, CTA, template, variant,
  overlay, logo position, properties) and Regenerate / Generate Variants /
  Approve are enabled again; the creative can be re-approved.
- **Restriction:** creatives that have already been queued for publishing
  cannot be returned to review. The UI hides the action and displays "This
  creative has already been queued for publishing. Remove it from the
  publishing queue before editing." Published creatives remain immutable.

### Files Modified

- `services/creative_service.py`:
  - `_latest_creative_for_product` — shared lookup for the creative workflow
    transitions (replaces the duplicated join query in save/approve).
  - `reopen_creative_for_review` — flips `APPROVED -> GENERATED` only,
    preserving all presentation data; raises `CreativeLockedError` for
    queued creatives.
  - `save_creative_presentation` / `approve_creative_for_product`
    refactored to use the shared lookup (no logic change).
- `services/atlas_api.py`:
  - `CreativeReopenRequest` request model.
  - New `POST /creatives/reopen` endpoint (409 for queued, 404 when no
    creative exists).
- `frontend/src/features/creatives/creative-api.ts` — `reopenCreative`.
- `frontend/src/features/creatives/use-creatives.ts` — `useReopenCreative`.
- `frontend/src/features/creatives/creative-studio.tsx` — reopen handler,
  confirmation dialog state, and the `onReturnToReview` wiring.
- `frontend/src/features/creatives/approval-panel.tsx` — state-aware action
  area: needs-review shows Regenerate / Generate Variants / Approve /
  Queue; approved shows Return to Review / Queue; queued shows the
  publishing-queue message and no actions.

### Database Changes

None. The enhancement reuses the existing `creative_assets.status` model
(`GENERATED` / `APPROVED` / `QUEUED` / `FAILED`) and existing presentation
columns. No new tables, no schema changes.

### Verification

- `npm run lint` — clean.
- `npx tsc --noEmit` — clean.
- `npm run build` — clean (12 routes).
- Backend API round-trips (via `curl`):
  - `POST /creatives/reopen` moves `APPROVED -> GENERATED` and preserves
    `selected_template`, `selected_variant`, `properties_json` and
    `headline` exactly.
  - Reopening an already-reviewable creative is idempotent.
  - Reopening a queued creative returns `409` with the publishing-queue
    message.
- Playwright browser QA (`creative-reopen-check.py`, preview URL): 35/35
  passing, covering the approved (locked) state with Return to Review +
  hidden stale buttons, the confirmation dialog (title + message + Cancel),
  reopen -> editable with all selections preserved, refresh persistence,
  re-approve -> locked again, the queued restriction, and zero console
  errors.
- Playwright regression (`creative-regression-final.py`): 12/12 — queue
  counts match the canonical seed and `/products`, `/content`,
  `/publishing` render with zero console errors.

### Screenshots

- `frontend/public/screenshots/creative-studio-reopen-approved.png` —
  approved creative, locked, with Return to Review + Queue for Publishing.
- `frontend/public/screenshots/creative-studio-reopen-confirm.png` —
  "Return creative to review?" confirmation dialog.
- `frontend/public/screenshots/creative-studio-reopen-editable.png` —
  creative returned to review, editable again with selections preserved.


