# ATLAS-025 — Publishing Center MVP (UI-only) Deliverables Report

## Summary
Built the ATLAS-025 Publishing Center — a UI-only "mission control" that replaces the Publishing placeholder route. It answers the four publishing questions at a glance: **What is ready to publish?** (Publishing Queue + summary), **Where will it be published?** (Pinterest board picker in the Publish Console), **When will it publish?** (Publish Now / Schedule timing + Scheduled summary), and **What has already been published?** (Published History). It walks the workflow Creative Approved → Publishing Queue → Select Pinterest Board → Choose Publish Time → Publish Now / Schedule → Published History. Pure client-side UI over a typed mock dataset shaped so TanStack Query can replace it later. No backend, API, auth, persistence, or business logic.

## Files Created

### New — feature module (`frontend/src/features/publishing/`)
| File | Purpose |
|---|---|
| `types.ts` | `PublishPriority`, `PublishQueueStatus` (queued/scheduled), `PublicationStatus` (published/scheduled/failed), `PinterestBoard`, `PublishItem`, `Publication`, `PublishTimingMode` |
| `publishing-utils.ts` | `getPublishCounts`, `sortQueue` (ready-first, then priority), `sortPublications` (upcoming first → recent), `formatPublishTime`, `relativeTime`, `formatCount`, `toDatetimeLocal`, `defaultScheduleTime` |
| `mock-data.ts` | 5 typed Pinterest boards (reuse `MOCK_PRODUCTS` for imagery), 5 queue items (4 queued + 1 scheduled), 5 publications (3 published + 1 scheduled + 1 failed); relative timestamps for realistic "live" times; `BOARD_BY_ID` lookup |
| `publishing-status-badge.tsx` | Status dot + pill badge via `PUBLISH_STATUS_META` (mirrors the content `STATUS_META` pattern): queued / scheduled / published / failed |
| `publishing-summary.tsx` | 4 summary cards (Ready to Publish / Scheduled / Published / Boards) reusing dashboard `MetricCard` |
| `publishing-queue.tsx` | `<ol>` of selectable button rows: thumbnail, product, board name, priority dot, status badge; `aria-pressed` selection with primary bar |
| `publish-console.tsx` | Mission-control panel: header, live pin preview (reuses `CreativePin`), 5-selectable board picker, Publish now / Schedule segmented control, `datetime-local` input with future-time validation + inline hint, Publish Now / Schedule actions, feedback line |
| `published-history.tsx` | `SectionCard` list: thumbnail, product, board (LayoutGrid), status badge, relative/formatted timestamp, Copy-link action for published pins |
| `publishing-skeleton.tsx` | 650ms skeleton layout mirroring the page (no spinners) |
| `publishing-center.tsx` | Orchestrator: skeleton → summary/queue/console/history; local-state commit for Publish Now / Schedule with live counts, selection advance, and feedback timers |

## Files Modified
- `frontend/src/app/(app)/publishing/page.tsx` — renders `<PublishingCenter />`; metadata title "Publishing Center".
- `CHANGELOG.md` — added `[0.6.0]` (ATLAS-025).
- `JOURNAL.md` — added 2026-08-06 (ATLAS-025) session log.
- `frontend/public/screenshots/` — added `publishing-desktop-dark.png`, `publishing-desktop-dark_scheduled.png`, `publishing-desktop-light.png`, `publishing-tablet-dark.png`, `publishing-mobile-dark.png`.

## Components Added
10 components/utilities in `features/publishing/` (listed above). **No new UI primitives and no new design tokens.** Reused across features: `MetricCard` + `Metric` (dashboard), `SectionCard` (dashboard), `CreativePin` + `TEMPLATE_BY_ID` (creatives), `makeHeadline` + `DEFAULT_CTA` (creatives), `ProductImage` (products), `CreativeProperties`/`TemplateId` types (creatives), and `Button`, `Input` from `components/ui`.

## Dependencies Added
- **Runtime:** none — existing deps only (next, lucide-react, class-variance-authority, `@/lib/utils` `cn`, radix-ui via `components/ui`).
- **Tooling (dev environment only, not in package.json):** `playwright@1.49.1` + chromium installed globally for DOM/layout/flow checks and screenshots (same approach as ATLAS-021/022/023).

## Commands Executed
```bash
cd frontend && npm install                       # 706 packages, 0 vulnerabilities
cd frontend && npm run lint                      # 0 errors / 0 warnings
cd frontend && npm run build                     # 12 static routes, type-check clean
cd frontend && npm run dev                       # background, port 3000
npm install -g playwright@1.49.1                 # global (dev-only tooling)
npx playwright install --with-deps chromium      # headless browser + system deps
NODE_PATH=/usr/local/lib/node_modules node /tmp/opencode/publishing-check.cjs   # 37/37 checks + screenshots
curl -s -o /dev/null -w "%{http_code}" https://3000-40531c7afdb77a05.monkeycode-ai.live/publishing   # 200
```

## Design Decisions
- **Layout order matches the workflow spec**: Header (title + subtitle + "Review Creatives" handoff link) → Summary (4 questions) → two-column workspace (Queue LEFT, Console RIGHT, stacks on mobile) → Published History (full width). Skeleton-only loading (650ms), same convention as ATLAS-021/022/023.
- **Four summary cards map 1:1 to the four questions**: Ready to Publish (queued items), Scheduled (scheduled queue + scheduled history), Published (published history), Boards (connected boards). Deltas carry the tone (attention when items are waiting).
- **Status grammar mirrors existing features**: `PUBLISH_STATUS_META` record → `PublishingStatusBadge` (dot + pill). Queued = muted, Scheduled = `chart-4` (gold), Published = emerald, Failed = red — reusing the established tonal language.
- **Publish Console reuses the Creative Studio pin renderer**: `CreativePin` + `TEMPLATE_BY_ID` render the exact approved creative, so the operator approves what will actually go live. `PublishItem` carries `templateId` + `properties` for this purpose.
- **Board picker is a visual grid, not a dropdown**: five selectable board cards (name + pins/followers) with `aria-pressed`, mission-control feel, no scroll needed.
- **Timing is a segmented control** (Publish now / Schedule) mirroring the `TabsList` styling. Scheduling reveals a `datetime-local` input; the Schedule action is disabled for past/empty times with an inline "Choose a time in the future." hint.
- **Actions are local-state commits (no persistence)**: Publish Now → queue item removed, a `published` Publication (now) prepended to history; Schedule → a `scheduled` Publication at the chosen time. Selection auto-advances to the next queue item; summary + queue + history counts update live. Reuses the `feedbackTimer` pattern for transient confirmations.
- **History ordering is opinionated**: upcoming scheduled pins first (soonest → latest), then published/failed most-recent-first — so "what's next" is at the top rather than a far-future pin burying the latest publish.
- **Scheduled items in the queue (mock) pre-fill the console** in Schedule mode with their plan, so the operator sees and can override the existing plan.
- **Mock data isolation**: publishing defines its own boards/queue/history, importing only `MOCK_PRODUCTS` imagery and the creative template/copy constants (no duplicated creative data). Timestamps are relative to load time so the "live" feel holds on any date.
- **Accessibility**: semantic `<header>/<section>/<ol>/<li>/<dl>` structure, `aria-pressed` on queue rows/board cards/timing segments, `aria-invalid` on invalid time, `aria-label`s on icon/action buttons, `sr-only` priority labels, `tabular-nums` counts, `focus-visible` rings.
- **Responsive**: summary 4/2/1 cols; workspace two columns at `lg+` (380px queue + fluid console), single column below; board grid 2 cols always; verified at 1440 / 768 / 390 px, dark and light.
- **Strict TS / lint workarounds**: the `react-hooks/purity` rule flags `Date.now()` during render but accepts `new Date()` (the dashboard `welcome-header` precedent) — schedule validation uses a render-time `new Date()`, and timestamps are minted inside event handlers only.

## Assumptions & Risks
- **Mock data only** — boards, queue, and history are demo values; types shape a plausible API payload so a real hook is a drop-in change.
- **No persistence** — reloading resets to mock state (by design, UI-only). "Copy link" writes a fabricated `pin.it/atlas-*` URL to the clipboard.
- **Scheduled pins never actually fire** — scheduling only adds a history row; there is no scheduler, timer, or Pinterest API.
- **No retry flow for failed pins** — a failed history row is display-only (no "Retry" action) to avoid overbuilding the MVP.
- **`CreativePin` reuse couples publishing to the creatives feature's template map** — intentional reuse; if creatives ever ships its own rendering service, swap the import, not the data.
- **Pre-existing shell hydration mismatch** — the App Shell `ThemeToggle` (`theme-toggle.tsx`) logs a React hydration-mismatch warning on every route (dashboard, products, publishing all affected). It predates ATLAS-025, is cosmetic, and is out of scope (shell code, not this feature); flagged for the team.
- **Playwright/chromium** installed globally for this session only; not a project dependency.

## Recommendations (future)
1. Wire `PublishingCenter` to a real hook (TanStack Query + `/api/publishing`); `PublishItem`/`Publication` types already match a plausible API shape.
2. Replace the mock board picker with real Pinterest boards sourced from Accounts.
3. Add a "Retry" action for failed pins once a real publish path exists.
4. Surface per-pin analytics (impressions/clicks) from the Published state into Analytics.
5. Consider a per-item board preference persisted to localStorage until the backend lands.
6. Fix the pre-existing `ThemeToggle` hydration mismatch (gate `resolvedTheme` behind a `mounted` check) in a shell cleanup pass.

## Screenshots
Saved in `frontend/public/screenshots/`:
`publishing-desktop-dark.png`, `publishing-desktop-dark_scheduled.png`, `publishing-desktop-light.png`, `publishing-tablet-dark.png`, `publishing-mobile-dark.png`.

DOM/layout/flow verification (Playwright, headless chromium — 37/37 checks):
- Heading "Publishing Center" + subtitle; summary `[Ready 4, Scheduled 2, Published 3, Boards 5]`; queue 5 items (1 scheduled badge); console shows pin preview + selected product + 5 boards + 2 timing options (defaults to Publish now); history 5 rows with statuses 3 published / 1 scheduled / 1 failed and 3 Copy-link buttons.
- Publish flow: selecting Foldable Laundry Bag → console updates; selecting Amazon Home Finds board updates `aria-pressed`; Publish Now → queue 5→4, history 5→6, Published 3→4, feedback "Published to Amazon Home Finds".
- Schedule flow: toggling Schedule shows the datetime input; a future time enables the Schedule action → queue →3, history →7, Scheduled summary →3; a past time disables Schedule and shows "Choose a time in the future."
- Copy link flips to "Copied" transiently.
- No console/page errors from the feature (only the pre-existing shell ThemeToggle hydration warning, present on every route).
- Responsive: summary 4-col (1440), 2-col (768), 1-col (390); queue + console visible on mobile; light theme applies correctly.

## Verification Results
- `npm run lint`: 0 errors / 0 warnings.
- `npm run build`: all 12 routes static, compiled + type-checked clean.
- Live preview: `https://3000-40531c7afdb77a05.monkeycode-ai.live/publishing` returns 200 with the rendered Publishing Center.
- Responsive + theme checks pass at 1440 / 768 / 390 px, dark and light.
