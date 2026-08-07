# Changelog

All notable changes to Project Atlas will be documented in this file.

This project follows semantic versioning.

---

## [0.9.0] - 2026-08-07

### Changed
- ATLAS-028: Creative Studio now loads real backend content instead of the
  mock catalog; the workflow mirrors ATLAS-027 (AI Studio)
- `GET /creatives` is the single source for Creative Studio; TanStack Query
  (`useCreatives`) fetches it through the existing `/api` dev proxy
- Added `creative-api.ts` (`mapCreative` + `fetchCreatives`): maps joined
  `research_products` × `ai_content` × `creative_assets` rows → `CreativeItem`,
  deriving status on the client: APPROVED→approved, FAILED→waiting,
  creative exists→needs-review, no creative→waiting
- Generate and approve are real backend round-trips
  (`POST /creatives/generate`, `POST /creatives/approve`); the API path
  reuses the creative worker's rendering pipeline via the shared
  `generate_and_save_creative`; the worker stays idempotent and untouched
- Creative Studio keeps its exact UI: skeleton, summary cards, queue,
  preview, template/variant galleries, properties panel, readiness
  checklist, approval panel, dark/light themes; added a friendly error
  state with "Try again" (reuses `EmptyState`)
- `services/creative_service.py`: creative assets data layer +
  `fetch_creatives_workflow` (single joined read model) + idempotent
  `generate_and_save_creative`
- `services/atlas_api.py`: added `GET /creatives` (503/500 mapping) and
  `POST /creatives/generate` / `POST /creatives/approve`
  (404/500/502 mapping) with typed request/response models
- Stabilization: theme-toggle mounted guard removes the pre-existing
  next-themes hydration-mismatch console error on every page; removed the
  dead `buildCreativeItem` mock builder from `creative-utils.ts`

### Added
- `frontend/src/features/creatives/use-creatives.ts`: `useCreatives`,
  `useGenerateCreative`, `useApproveCreative` with shared
  `["creatives"]` query-key invalidation
- Creative Studio screenshots (desktop light/dark, generated, approved
  persisted) captured during verification in `frontend/public/screenshots/`

---

## [0.8.0] - 2026-08-06

### Changed
- ATLAS-027: AI Studio now loads real backend content instead of the mock
  catalog; the mock file was removed (`content/mock-data.ts`)
- `GET /ai-content` is the single source for AI Studio; TanStack Query
  (`useContent`) fetches it through the existing `/api` dev proxy
- Added `content-api.ts` (`mapAiContent` + `fetchAiContent`): maps joined
  `research_products` × `ai_content` rows → `ContentItem`, deriving
  status on the client: GENERATED→needs-review, APPROVED→approved,
  QUEUED/PUBLISHED→queued, no content→waiting
- Generate and approve are real backend round-trips
  (`POST /ai-content/generate`, `POST /ai-content/approve`); UI keeps the
  transient in-progress states, the backend always wins on refetch
- AI Studio keeps its exact UI: skeleton, summary cards, search/status
  filters, queue, editor, review decisions, preview, dark/light themes;
  added a friendly error state with "Try again" (reuses `EmptyState`)
- `services/database.py`: `fetch_ai_content()` now LEFT JOINs
  `research_products rp` with `ai_content ac` (single query, exposes
  `research_status`/`content_status`/`ai_content_id`); added
  `fetch_research_product_by_id()` and `approve_ai_content()`
- `services/ai_service.py`: shared `generate_and_save_ai_content()` reused
  by both the AI worker and the API (idempotent, raises
  `AlreadyGeneratedError`); worker no longer duplicates create/mark logic
- `services/atlas_api.py`: added `GET /ai-content` (503/500 mapping) and
  `POST /ai-content/generate` / `POST /ai-content/approve`
  (404/422/500/502 mapping) with typed request/response models

### Added
- `frontend/src/features/content/use-content.ts`: `useContent`,
  `useGenerateContent`, `useApproveContent` with shared
  `["content"]` query-key invalidation
- AI Studio screenshots (desktop light/dark, error state) captured during
  verification in `frontend/public/screenshots/`

---

### Changed
- ATLAS-026: Products page now loads real backend data instead of the mock
  catalog
- `GET /research-products` is the single source for the Products page;
  TanStack Query (`useProducts`) fetches it through the existing `/api`
  dev proxy
- Added `product-api.ts` (`mapResearchProduct` + `fetchProducts`):
  maps `research_products` rows → `Product`, deriving workflow `progress`
  and `health` from backend status (NEW→25/needs-attention, GENERATED→50/
  ready, QUEUED→75/ready, PUBLISHED→100/ready, FAILED→25/blocked)
- Products page keeps its skeleton, filters, sorting, grid/list views, and
  detail drawer; added a friendly error state with "Try again" (reuses the
  empty-state pattern) and the existing empty/results states
- `ProductImage` renders its fallback icon when a product has no image URL
- `next.config.ts` allows Amazon CDN image hostnames (`m.media-amazon.com`,
  `images-na.ssl-images-amazon.com`) for real product imagery

### Added
- `GET /research-products` response now includes `asin`
  (`services/database.py`) and maps DB failures to 503/500 like sibling
  endpoints (`services/atlas_api.py`)
- Products screenshots (desktop dark/light, mobile dark) in
  `frontend/public/screenshots/`

---

## [0.6.0] - 2026-08-06

### Added
- ATLAS-025: Publishing Center MVP
  (`frontend/src/features/publishing/`, UI-only)
- Four-question mission-control summary (reuses dashboard `MetricCard`):
  Ready to Publish / Scheduled / Published / Boards
- Publishing Queue of approved creatives with board + status badges
- Publish Console: live pin preview (reuses Creative Studio `CreativePin`),
  Pinterest board picker, Publish Now / Schedule timing, and
  Publish Now / Schedule actions with future-time validation
- Published History: upcoming scheduled pins first, then recent published
  and failed pins, with board, timestamp, and copy-link action
- Status flow: queued → published now / scheduled; history grows live,
  summary counts update live, empty states for queue and history
- Skeleton loading (650ms), responsive 2-column workspace stacking on
  tablet/mobile, dark/light themes
- Publishing page now renders the Publishing Center instead of placeholder

---

## [0.5.0] - 2026-08-06

### Added
- ATLAS-023: AI Studio — Content review/approval workflow
  (`frontend/src/features/content/`, UI-only)
- Header with subtitle, "Generate AI Content" primary action and
  "Bulk Generate" secondary action
- Summary cards: Waiting / Generating / Needs Review / Approved
  (reuses dashboard MetricCard)
- Toolbar with search and status filter; two-column workspace
  (Queue left, Editor right) that stacks on tablet/mobile
- Content queue with image, product name, category, priority dot,
  status badge, and Eye preview button
- Content editor: Pinterest Title / Description / Hashtags / CTA with
  live character counts (100/500), mock SEO Score, and
  Copy / Improve / Regenerate / Shorten / Expand / Reset actions
- Approval panel: Approve / Needs Changes / Queue for Creative Studio
  with live summary + queue updates
- Status flow: Waiting → Generating → Needs Review → Approved / Queued;
  simulate generation timer, skeleton editor, changes-requested banner,
  read-only queued items, empty states
- Content page now renders the AI Studio instead of placeholder

---

## [0.4.0] - 2026-08-06

### Added
- ATLAS-022: Executive Dashboard (`frontend/src/features/dashboard/`)
- Welcome Header with time-based greeting and long-form date
- Executive Metrics: Products, AI Content, Creatives, Published,
  Success Rate, Ready Today
- Today's Focus list with priority indicators and action links
- Recent Activity feed with pipeline event timeline
- Pipeline Overview stepper (Imported → Research → AI → Creative →
  Publishing → Live)
- Category Performance cards with ready-to-publish progress bars
- Quick Actions, System Health panel, skeleton + empty states
- Dashboard page now renders the live dashboard instead of placeholder

---

## [0.3.0] - 2026-08-06

### Added
- ATLAS-021: Products module (UI-only)
- Product grid/list views, toolbar (search/filter/sort/view), health
  badges, workflow progress bars
- Product detail drawer with 6 tabs, skeleton loading, empty states
- Typed mock catalog with Unsplash imagery
- Unsplash image remote pattern in `next.config.ts`

---

## [0.2.0] - 2026-08-06

### Added
- ATLAS-020: Next.js frontend foundation (`frontend/`)
- Responsive App Shell (sidebar, header, main)
- Placeholder pages: Products, Dashboard, Content, Creatives,
  Publishing, Analytics, Accounts, Settings
- Dark/light theme support (dark default)
- ⌘K command palette, notifications, user menu placeholders
- Dev-server API proxy `/api/*` → backend (FastAPI)
- TanStack Query, Recharts, Lucide, shadcn/ui integration

---

## [0.1.0] - 2026-07-31

### Added
- Initial Project Atlas folder structure
- Git repository
- SQLite database
- n8n setup
- OmniRoute integration
- README.md
- Initial documentation structure
- Frozen Version 1 database architecture

### Planned
- Create production database schema
- General Manager workflow
- Research Department