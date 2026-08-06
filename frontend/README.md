# Atlas Frontend — ATLAS-020

The Atlas web application. Next.js (App Router) + TypeScript +
TailwindCSS v4 + shadcn/ui. Foundation only — no backend integration,
authentication, or business logic.

## Requirements

- Node.js >= 20 (developed against Node 22)

## Getting Started

```bash
npm install
npm run dev
```

The app is served at `http://localhost:3000`. `/` redirects to
`/dashboard`.

## Scripts

| Command            | Description                          |
| ------------------ | ------------------------------------ |
| `npm run dev`      | Start the development server         |
| `npm run build`    | Production build (type-checked)      |
| `npm run start`    | Serve the production build           |
| `npm run lint`     | Run ESLint                           |

## API Proxy

The dev server proxies backend requests so the frontend can call the
FastAPI backend without CORS:

```
/api/* → ${API_UPSTREAM}/*     (API_UPSTREAM defaults to http://127.0.0.1:8000)
```

The `/api` prefix is stripped before forwarding. ATLAS-020 ships the
proxy only; no API calls are wired yet. Copy `.env.example` to
`.env.local` to override `API_UPSTREAM`.

The preview host `*.monkeycode-ai.live` is allowed by
`allowedDevOrigins` in `next.config.ts`.

## Project Structure

```
frontend/
  next.config.ts            # proxy rewrite + allowedDevOrigins
  src/
    app/
      layout.tsx            # root layout (fonts, providers)
      page.tsx              # "/" -> redirect to /dashboard
      globals.css           # Tailwind v4 + shadcn design tokens
      (app)/
        layout.tsx          # AppShell (sidebar + header + main)
        dashboard/page.tsx  # + products, content, creatives,
        ...                 #   publishing, analytics, accounts,
                            #   settings (placeholder pages)
    components/
      ui/                   # shadcn/ui components
      layout/
        app-shell.tsx       # responsive shell
        sidebar.tsx         # desktop sidebar (collapsible rail)
        sidebar-nav.tsx     # shared nav list (also used in mobile sheet)
        mobile-sidebar.tsx  # sheet drawer for < lg
        header.tsx          # top bar
        search-command.tsx  # ⌘K command palette
        notifications-dropdown.tsx
        theme-toggle.tsx
        user-menu.tsx
      page-header.tsx       # title + subtitle
      empty-state.tsx       # professional empty state
      placeholder-page.tsx  # shared placeholder page layout
      providers.tsx         # next-themes + TanStack Query
    lib/
      navigation.ts         # nav config (routes, icons, copy)
      utils.ts              # cn() helper
```

## Design

- Dark theme by default; light/dark toggle via `next-themes` (class
  strategy, no system resolution).
- Minimal, premium aesthetic — neutral palette, tight radius, Geist
  sans. Inspired by Linear / Stripe Dashboard / GitHub (not copied).
- Responsive: sidebar collapses to an icon rail on desktop, becomes a
  sheet drawer on mobile.
