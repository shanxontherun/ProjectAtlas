# Atlas Engineering Journal

---

# 2026-08-06 (ATLAS-027)

## Goal

Replace the AI Studio mock catalog with real FastAPI backend data —
keeping the page pixel-identical (skeletons, summary cards, queue, editor,
review decisions, preview modal, toolbar filters, dark/light themes).
Reuse the existing `ai_content` table, generation/validation services, and
worker logic before creating anything new; the UI must reflect DB state on
reload. This was the reference backend-integration sprint.

## Accomplished

- **Backend reuse audit** (documented in `docs/ATLAS-027-deliverables.md`):
  reused `ai_content` (sql/007), `generate_ai_content`,
  `create_ai_content`, `ai_content_exists`, `mark_research_generated`,
  `get_connection`, `AIClient`/`AIValidationError`/prompt builders, and the
  AI worker — no new tables, no schema changes
- `services/database.py`: rewrote `fetch_ai_content()` as a single LEFT
  JOIN of `research_products rp` × `ai_content ac` (aliased
  `research_status` / `content_status` / `content_created_at` /
  `content_updated_at`, exposes `ai_content_id`); added
  `fetch_research_product_by_id()` and `approve_ai_content()` (flips the
  existing `ai_content.status` → APPROVED, reusing the status column)
- `services/ai_service.py`: added `AlreadyGeneratedError` and the shared
  `generate_and_save_ai_content(product)` (idempotency check →
  generate → create → mark-research-generated), now used by BOTH the AI
  worker and the API so behavior can't drift
- `services/atlas_api.py`: added `GET /ai-content` (503/500 mapping) and
  `POST /ai-content/generate` (404/422/500/502, idempotent 200) /
  `POST /ai-content/approve` (404 when no content), with typed request/
  response models; `sys.path` shim so `services.*` imports work from
  `services/`
- `workers/ai_worker.py`: refactored onto the shared service; removed
  duplicated create/mark logic (external behavior unchanged)
- Frontend: added `content-api.ts` (`mapAiContent` deriving status:
  QUEUED/PUBLISHED→queued, APPROVED→approved, GENERATED content→needs-
  review, no content→waiting), `use-content.ts` (query + generate/approve
  mutations invalidating `["content"]`), and `content-empty-state.tsx`;
  `content-view.tsx` rewritten to the hooks with transient in-browser
  states that the server overwrites on refetch; deleted `mock-data.ts`;
  removed dead `generateDraft` from `content-utils.ts`
- Verified backend round-trips on the seeded DB: `/ai-content` 10 rows (6
  with content), idempotent regenerate, 404s for missing product/approve
- Verified UI with Playwright on the preview URL: **19/19** checks —
  skeleton, queue from backend, status derivation + summary counts,
  editor loads backend draft, Improve, search/status filters, preview
  dialog, dark↔light toggle, Generate round-trip (waiting→needs-review),
  Approve round-trip (→approved), persistence across reload, `/products`
  unaffected, no page errors; plus error-state (backend down) and
  Try-again recovery (1/1 each)
- `npm run lint` 0/0, `npm run build` clean (12 static routes),
  `npx tsc --noEmit` clean after build
- Added CHANGELOG 0.8.0 entry, this journal entry, and
  `docs/ATLAS-027-deliverables.md`; screenshots in
  `frontend/public/screenshots/ai-studio-backend-*.png`

## Lessons

- Client-side status derivation in the mapper keeps the backend raw-data
  authority while the UI owns presentation; matching the queue ordering to
  `filterContentItems`' sort rank is what keeps waiting/needs-review in
  the right visual order.
- Idempotent generate returning `ai_content_id: null` on an existing
  product is a clean contract for "already done", but the UI must only
  offer generate for waiting items or it will look like a silent no-op.
- Transient UI states + `patch.status === "generating" && item.draft`
  skip in the memo is a clean way to keep in-flight feedback without ever
  persisting it; server refetch is the single source of truth.
- Playwright selectors: `role="combobox"` (Radix Select trigger) is not a
  `button`; queue buttons are `button[aria-label$=" in the editor"]`;
  next-themes `defaultTheme="dark"` means the theme toggle flips dark→
  light on first click, not the other way around.
- Real AI gateway is unavailable locally (no `AI_BASE_URL`/`AI_API_KEY`/
  `AI_MODEL`); a stub OpenAI-compatible server on the `AIClient` default
  port (20128) proved the wiring end-to-end.

## Next Session

- Wire Creative Studio and Publishing to real backend data using this
  pattern once their workers write statuses; AI Studio is now the
  reference for generate→review→approve.
- Re-run verification against real AI output once the gateway is
  configured in the runtime.
- Decide whether "Needs Changes"/"Queue" should persist server-side, and
  consolidate the duplicate `fetch_all_research_products`
  (`database.py` vs `services/research_products.py`).

---

# 2026-08-06 (ATLAS-026)

## Goal

Replace the Products page mock catalog with real FastAPI backend data —
keeping the page pixel-identical (skeletons on load, friendly error/empty
states, no spinners). Products module only; no AI Studio, Creative Studio,
Publishing, Analytics, or Pinterest API changes.

## Accomplished

- Verified backend: ran migrations to create `database/atlas.db` (gitignored),
  started `services/atlas_api.py` (uvicorn, port 8000), and seeded 8 research
  products through the real `POST /research-products` API across every
  pipeline status (NEW / GENERATED / QUEUED / PUBLISHED / FAILED)
- Reused the existing `GET /research-products` endpoint — no parallel API.
  Extended it minimally: added `asin` to `fetch_all_research_products`
  (the Products UI renders ASIN) and added 503/500 error mapping consistent
  with `/categories`
- Frontend: added `product-api.ts` (typed `ResearchProductRow`,
  `mapResearchProduct`, `fetchProducts`) and `use-products.ts` (TanStack
  Query `useProducts`, reusing the existing QueryClient)
- `products-view.tsx` now renders skeletons from `isLoading`, a friendly
  error state with "Try again" (new `error` variant of `ProductEmptyState`
  reusing `EmptyState`), and keeps the existing empty/results states;
  filtering/sorting/grid/list/drawer untouched. Mock `MOCK_PRODUCTS` kept —
  content/creatives/publishing still import it for imagery
- `ProductImage` renders its icon fallback when `image_url` is null;
  `next.config.ts` allows Amazon CDN hostnames so real product images work
- Verified: `npm run lint` 0/0, `npm run build` (12 static routes) clean,
  API payloads, and Playwright 13/13 DOM/layout/flow/state checks
  (skeleton → grid, 8-of-8 footer, category/search filters, health badges,
  drawer with backend ASIN, list view, error state, empty state); saved
  screenshots (desktop dark/light, mobile dark)
- Added CHANGELOG 0.7.0 entry, this journal entry, and
  `docs/ATLAS-026-deliverables.md`

## Lessons

- Next.js dev (16.x) enforces `allowedDevOrigins`: a browser requesting
  `127.0.0.1:3000` directly sends an `Origin` header and gets 403 on JS
  chunks (curl passes because it sends none). Verify through the
  `*.monkeycode-ai.live` preview URL, matching the ATLAS-025 workflow.
- TanStack Query resolves so fast against a local backend that the skeleton
  state is invisible; delay the API route in Playwright to assert it.
- `aria-hidden` root + `animate-pulse` live on different elements in
  `ProductSkeleton`; match `div.animate-pulse`, not the combined selector.

## Next Session

- Wire Content (AI Studio) and Dashboard to real backend data via TanStack
  Query, following the `product-api.ts` pattern.
- Decide product source-of-truth once research → ai → creative → publishing
  workers update `research_products.status`; progress/health derivation can
  then move server-side if the UI stage mapping grows.
- Reconcile the duplicate `fetch_all_research_products` in
  `services/research_products.py` vs `services/database.py`.

---

# 2026-08-06 (ATLAS-025)

## Goal

Deliver the ATLAS-025 Publishing Center MVP — a UI-only "mission control"
that answers what is ready to publish, where it will go, when it publishes,
and what has already been published. Replaces the Publishing placeholder.

## Accomplished

- Reviewed the ATLAS-023 AI Studio / ATLAS-024 Creative Studio as quality
  benchmarks; reused `MetricCard`, `SectionCard`, `ProductImage`,
  `CreativePin` + `TEMPLATE_BY_ID`, `ContentStatusBadge` conventions, and
  existing UI primitives (no new primitives, no new dependencies)
- Built `frontend/src/features/publishing/`: types + publishing-utils +
  isolated mock data (5 boards, 5 queue items, 5 history items) that reuse
  `MOCK_PRODUCTS` for imagery and creative template data for pin previews
- Header + "Review Creatives" deep-link back to `/creatives` (handoff)
- Four summary cards map 1:1 to the four questions
- Publishing Queue (left): ready/scheduled items with board + status badge
- Publish Console (right): pin preview, board picker (5 selectable cards),
  Publish now / Schedule segmented control, `datetime-local` picker with
  future-time validation, and Publish Now / Schedule actions
- Published History: upcoming scheduled pins first, then recent
  published/failed; relative timestamps, board names, copy-link action
- Publish Now moves the item to history as "Published"; Schedule as
  "Scheduled"; queue count, history, and summary counts update live
- Skeleton (650ms), empty states, responsive (2-col on lg+, stack below),
  dark/light themes; `npm run lint` + `npm run build` clean
- Playwright: 37/37 DOM/layout/flow/responsive checks pass; screenshots
  saved (desktop dark, scheduled state, light, tablet, mobile)
- Added CHANGELOG 0.6.0 entry, this journal entry, and
  `docs/ATLAS-025-deliverables.md`

## Lessons

- React's `react-hooks/purity` lint flags `Date.now()` during render but
  accepts `new Date()` (the dashboard's `welcome-header` precedent). Used a
  render-time `new Date()` for schedule validation; actions call `Date.now()`
  only inside handlers.
- Mock data isolation + reuse: importing `TEMPLATE_BY_ID` (template styling)
  and `makeHeadline` (creative copy) from the creatives feature is the same
  cross-feature reuse the codebase already applies with `MOCK_PRODUCTS`; no
  creative/template data was duplicated.
- History ordering: a single `eventAt`-desc sort put a far-future scheduled
  pin above the just-published pin. Sorting upcoming scheduled pins (soonest
  first) before recent published pins reads better for mission control.
- `getByRole('button', { name: 'Schedule', exact: true })` is ambiguous —
  the timing segmented control and the action button both match. Scoped to
  `[data-slot="button"]` (the ui Button) to target the action.

## Next Session

- Wire Publishing Center to a real hook (TanStack Query + `/api/publishing`);
  `PublishItem`/`Publication` types already shape a plausible API payload.
- Replace the mock board picker with real Pinterest boards from Accounts.
- Surface per-pin analytics from the Live/Published state into Analytics.

---

# 2026-08-06 (ATLAS-023)

## Goal

Deliver the ATLAS-023 AI Studio — a UI-only Pinterest content
review/approval workflow replacing the Content placeholder route.

## Accomplished

- Reviewed the ATLAS-022 dashboard as the quality benchmark, reused
  `MetricCard`, `ProgressBar`, `ProductImage`, and existing UI primitives
- Built `frontend/src/features/content/`: types + content-utils +
  realistic mock data (8 items spanning all statuses)
- Header with subtitle and Generate / Bulk Generate actions
- Summary cards (Waiting / Generating / Needs Review / Approved),
  toolbar (search + status filter), two-column workspace
- Queue: image, name, category, priority dot, status badge, Eye preview
- Editor: title/description/hashtags/CTA with live character counts,
  mock SEO Score, six actions, dirty-tracking Reset, read-only queued
- Approval panel: Approve / Needs Changes / Queue for Creative Studio,
  live summary + queue updates
- Generate flow: waiting → generating → needs-review with generated
  draft via timer; skeleton editor, changes-requested banner, empty states
- Replaced the content placeholder route; `npm run lint` + `npm run build`
  clean (12 static routes); Playwright DOM/layout/flow checks pass;
  captured screenshots (desktop dark/light, tablet, mobile, preview dialog)
- Added CHANGELOG 0.5.0 entry, this journal entry, and
  `docs/ATLAS-023-deliverables.md`

## Lessons

- Playwright `:has-text()` is a substring match, so `button:has-text("Approve")`
  also matched the "…Approved" queue row; use `getByRole(name, { exact })`
  for precise action targeting.
- Strict TS + React 19 updater narrowings forced small workarounds:
  non-null assertion on the generated draft and direct `setWorking(...)`
  calls instead of updater functions.

## Next Session

- Wire Content to real data via TanStack Query once the backend APIs are
  stable (remove the mock import).
- Connect the AI generate actions to a real generation backend.

---

# 2026-08-06 (ATLAS-022)

## Goal

Deliver the ATLAS-022 Executive Dashboard (UI-only).

## Accomplished

- Reviewed the ATLAS-021 Products module as the quality benchmark
- Built `frontend/src/features/dashboard/`: types + realistic mock data
- Welcome Header with time-based greeting + long-form date (client-side)
- Executive Metrics (6 cards), Today's Focus (priority dots + actions)
- Recent Activity feed, Pipeline Overview stepper (6 stages)
- Category Performance (progress bars), Quick Actions, System Health
- Skeleton loading + empty state; responsive and accessible
- Replaced the dashboard placeholder route; `npm run lint` + `npm run
  build` clean (12 static routes); captured screenshots
- Added CHANGELOG 0.3.0/0.4.0 entries and this journal entry

## Lessons

- Lint enforces `react-hooks/set-state-in-effect`; render-time `new
  Date()` is safe here because the dashboard mounts after the skeleton
  (client-only), so no hydration mismatch occurs.
- Cross-feature reuse (`ProgressBar` from products) beats duplicating UI.

## Next Session

- Wire the dashboard to real data via TanStack Query once the backend
  APIs are stable (remove the mock import).
- Connect Products and Dashboard to the FastAPI backend.

---

# 2026-08-06

## Goal

Deliver the ATLAS-020 frontend foundation.

## Accomplished

- Reviewed the repository (Phase 1) and got architecture approval
- Scaffolded a self-contained Next.js app in `frontend/`
- Built a responsive App Shell: collapsible sidebar, header, main
- Added 8 placeholder pages with professional empty states
- Shipped dark/light theming (dark default) via next-themes
- Configured the dev-server API proxy and preview host allowlist
- Verified `npm run build`, `npm run lint`, and live routing

## Lessons

Frontend work can stay fully decoupled from the Python backend.

## Next Session

- Connect the frontend to the FastAPI backend (ATLAS-021)
- Implement Products list/table with TanStack Query

---

# 2026-07-31

## Goal

Establish the foundation of Project Atlas.

## Accomplished

- Designed project architecture
- Installed SQLite
- Installed n8n
- Installed OmniRoute
- Created project structure
- Initialized Git repository
- Designed Version 1 database
- Established documentation standards

## Lessons

A strong foundation reduces future complexity.

## Next Session

- Write production SQL
- Build the General Manager workflow