# ATLAS-026 — Products Page: Real Backend Data Deliverables Report

## Summary
Replaced the Products page mock catalog with real data from the existing
FastAPI backend. The page is pixel-identical to the mock version — same
grid/list views, toolbar filters/sort/search, health badges, workflow
progress bars, and detail drawer — but the data now comes from the
`research_products` table via the existing `GET /research-products`
endpoint (through the `/api` dev proxy), wired with TanStack Query.
Skeletons show on load; a friendly error state with "Try again" appears
when the backend is unreachable; the existing no-products / no-results
empty states are preserved. No AI Studio, Creative Studio, Publishing,
Analytics, auth, or Pinterest API changes. Mock data is untouched because
other features import `MOCK_PRODUCTS` for imagery.

## API Endpoints Used / Added
- **Used (reused, unchanged contract):** `GET /api/research-products`
  (`services/atlas_api.py` → `database.fetch_all_research_products`).
  Returns every row from `research_products` ordered by id.
- **Extended (backward-compatible):**
  - `services/database.py` — `fetch_all_research_products` SELECT now also
    returns `asin` (the Products UI renders the ASIN in the drawer). Pure
    additive field; existing consumers unaffected.
  - `services/atlas_api.py` — `GET /research-products` now maps
    `FileNotFoundError` → 503 and other DB failures → 500, matching the
    existing `/categories` / `/jobs` handlers (no stack traces leaked).
- **No new endpoints** — explicitly avoided a parallel products API.

## Files Created
| File | Purpose |
|---|---|
| `frontend/src/features/products/product-api.ts` | Wire type `ResearchProductRow`, `mapResearchProduct` (research_product → `Product`, deriving `progress`/`health` from `status`), and `fetchProducts` (GET `/api/research-products`, throws on non-OK) |
| `frontend/src/features/products/use-products.ts` | `useProducts` TanStack Query hook (`queryKey: ["products"]`, reuses the existing `QueryClient` in `providers.tsx`; staleTime 60s, retry 1) |
| `docs/ATLAS-026-deliverables.md` | This report |
| `frontend/public/screenshots/products-desktop-dark.png`, `products-desktop-light.png`, `products-mobile-dark.png` | Verification screenshots |

## Files Modified
| File | Change |
|---|---|
| `frontend/src/features/products/products-view.tsx` | Drop `MOCK_PRODUCTS` + fake 650ms loading; use `useProducts()`; render skeletons on `isLoading`, `ProductEmptyState variant="error"` on `isError`, existing empty/results states; footer "Showing X of Y" counts from API totals |
| `frontend/src/features/products/product-empty-state.tsx` | New `error` variant (reuses `EmptyState` + `Button`) with "Try again" → `refetch` |
| `frontend/src/features/products/product-image.tsx` | Render fallback icon when `src` is empty (real products may have no `image_url`) |
| `frontend/next.config.ts` | Allow Amazon CDN image hostnames (`m.media-amazon.com`, `images-na.ssl-images-amazon.com`) in `images.remotePatterns` so real product imagery won't fail the optimizer |
| `services/database.py` | `fetch_all_research_products` now selects `asin` |
| `services/atlas_api.py` | Error handling on `GET /research-products` (503/500) |
| `CHANGELOG.md` | Added `[0.7.0]` (ATLAS-026) |
| `JOURNAL.md` | Added 2026-08-06 (ATLAS-026) session log |

## DB Changes
- **Schema:** none — `research_products` already exists (sql/004 + 008/014
  migrations) with all fields the UI needs (`price`, `rating`,
  `review_count`, `image_url`, `ai_summary`, `status`, `created_at`, `asin`).
- **Data (verification only):** created `database/atlas.db` (gitignored)
  by running `scripts/run_migrations.py`, then seeded 8 products via the
  real `POST /research-products` API covering every pipeline status
  (NEW / GENERATED / QUEUED / PUBLISHED / FAILED) to exercise progress and
  health derivation. This is throwaway seed data in a gitignored DB.

## Status → Progress / Health Mapping (design decision)
The backend `research_products.status` (NEW / GENERATED / QUEUED /
PUBLISHED / FAILED) drives the UI's workflow concepts:

| Backend status | progress | health | workflow stage |
|---|---|---|---|
| NEW | 25 | needs-attention | Research Complete |
| GENERATED | 50 | ready | AI Ready |
| QUEUED | 75 | ready | Creative Ready |
| PUBLISHED | 100 | ready | Published |
| FAILED | 25 | blocked | Research Complete |
| (unknown) | 0 | needs-attention | Imported |

Unknown statuses degrade gracefully (progress 0, health needs-attention)
so legacy rows can never crash the UI.

## Design Decisions
- **Reuse, don't duplicate:** the existing `GET /research-products`
  endpoint is the single data source; mapping to the frontend `Product`
  type lives in one place (`mapResearchProduct`). No parallel API, no
  duplicate models beyond the minimal wire type.
- **Derivation stays client-side:** `progress`/`health` are presentation
  concepts (the UI owns `WORKFLOW_STAGES` + `getCurrentStage`); deriving
  them from `status` in the mapper keeps them next to the stages they
  render. Backend remains the raw-data authority.
- **Mock data preserved:** `MOCK_PRODUCTS` stays — content/creatives/
  publishing mock-data import it for imagery. Only the Products page
  swapped to the API.
- **No redesign:** all presentational components (grid, list, toolbar,
  skeleton, drawer, badges, progress bar, empty states) are reused as-is.
  The error state mirrors the established `EmptyState` pattern.
- **Image fallbacks:** `imageUrl` maps `image_url ?? ""` and
  `ProductImage` renders its existing icon fallback for empty/invalid
  sources, so products without images still look intentional.

## Assumptions
- `research_products` is the correct source of truth for the Products
  page (it carries all displayed fields: price, rating, reviews, image,
  ASIN, summary); `product_registry` has no price/rating/image and was not
  used.
- `ai_summary` is the closest real field to the mock `description` and is
  shown in the drawer Overview tab.
- ASIN comes from `research_products.asin` (sql/014); rows with NULL ASIN
  render empty in the drawer until the discovery pipeline populates it.
- All products (including FAILED) appear on the page, matching the mock's
  "blocked" products.

## Risks
- **Stale statuses:** the derivation assumes workers keep
  `research_products.status` in sync as products advance. Today the seeded
  data was advanced manually; if workers don't set QUEUED/PUBLISHED, most
  products will sit at NEW (25%, needs-attention). Revisit once the
  pipeline writes statuses.
- **Image loading:** next/image optimizes images server-side; if the
  runtime has no internet access, Amazon/Unsplash images fail to load and
  `ProductImage` falls back to its icon. Cosmetic only.
- **Large catalogs:** `GET /research-products` returns all rows; the UI
  filters/sorts client-side (fine at current scale). A paginated endpoint
  may be needed later.
- **Pre-existing import duplication:** `services/research_products.py`
  also defines `fetch_all_research_products` (imports
  `services.database`); `atlas_api.py` uses the `database.py` one. Left
  as-is (out of scope) but flagged for consolidation.

## Verification
- Backend: `python3 -c "from database import fetch_all_research_products"` —
  8 rows, all keys incl. `asin`; `GET /health` 200; `GET /research-products`
  200 with `asin`; `POST /research-products` 201.
- Frontend lint: `npm run lint` → 0 errors / 0 warnings.
- Frontend build: `npm run build` → compiled + type-checked clean,
  12 static routes.
- Live proxy: `/api/research-products` via the dev server and the preview
  URL both return the 8 seeded products.
- Playwright (preview URL, `products-check.cjs`): **13/13** checks pass —
  skeleton on load, grid rendered from API, "Showing 8 of 8 products",
  category filter → 4, search → 1, health badges (ready /
  needs-attention / blocked), drawer opens and shows backend ASIN, list
  view, error state on API failure, empty state on `[]`.
- Screenshots captured: desktop dark/light, mobile dark.

## Commands Executed
```bash
cd /workspace && python3 scripts/run_migrations.py        # create gitignored atlas.db
cd /workspace/services && python3 -m uvicorn atlas_api:app --port 8000
cd /workspace/frontend && npm run lint                   # 0/0
cd /workspace/frontend && npm run build                  # 12 static routes
cd /workspace/frontend && npm run dev                    # port 3000
NODE_PATH=/usr/local/lib/node_modules node /tmp/opencode/products-check.cjs   # 13/13
NODE_PATH=/usr/local/lib/node_modules node /tmp/opencode/products-shots.cjs   # screenshots
```

## Recommendations
- Next: wire Content (AI Studio) and Dashboard to real data using the same
  `useQuery` + mapper pattern (`product-api.ts` as the reference), so the
  whole app reflects the backend.
- When the workers begin writing QUEUED/PUBLISHED statuses, re-verify the
  derivation; consider moving it server-side if the stage mapping grows
  beyond a lookup table.
- Consolidate the duplicate `fetch_all_research_products` implementations
  (`database.py` vs `services/research_products.py`).
