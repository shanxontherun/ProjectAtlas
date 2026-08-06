# Project Atlas

An autonomous AI-powered affiliate marketing operating system.

## Tech Stack

- SQLite
- n8n
- OmniRoute
- Cursor
- Git

## Frontend

- Next.js (App Router) · React 19 · TypeScript
- TailwindCSS v4 · shadcn/ui · Lucide
- TanStack Query · Recharts · next-themes

The frontend lives in [`frontend/`](frontend/). It is a self-contained
Next.js application with a responsive App Shell (sidebar, header, main)
and placeholder pages for Products, Dashboard, Content, Creatives,
Publishing, Analytics, Accounts, and Settings.

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

Dev-server API proxy: `/api/*` → `http://127.0.0.1:8000/*` (override
with `API_UPSTREAM`). See `frontend/README.md` for details.

## Status

🚧 Sprint 1 - Foundation
