# Atlas Engineering Journal

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