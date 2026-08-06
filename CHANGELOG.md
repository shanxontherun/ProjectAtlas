# Changelog

All notable changes to Project Atlas will be documented in this file.

This project follows semantic versioning.

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