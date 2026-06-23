# PaperMind — Frontend

Production-grade Next.js 14 + Electron frontend for the PaperMind Book Summarizer API.

## Stack

- **Next.js 14** (App Router) + **TypeScript strict**
- **Tailwind CSS** with a custom design system
- **next-intl** for i18n (English + Persian/Farsi, full RTL)
- **next-themes** for light/dark + system detection
- **Zustand** for local UI + recent-jobs persistence
- **TanStack Query** for every backend call (polling-aware)
- **React Flow** for the interactive mind map
- **Sonner** for toasts, **cmdk** for the command palette
- **Electron** desktop wrapper with deep linking

## Quick start (web)

```bash
cp .env.example .env.local
npm install
npm run dev
# → http://localhost:3000
```

## Electron (desktop)

```bash
# Dev (hot reload, talks to Next dev server)
npm run electron:dev

# Build a static export and launch packaged
BUILD_TARGET=electron npm run build:web
npm run electron:start

# Produce installers
BUILD_TARGET=electron npm run build:web
npm run electron:package
```

## Docker

```bash
# From the repo root:
docker compose up --build
# Web → http://localhost:3000
# API → http://localhost:8000
```

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL the **browser** uses |
| `NEXT_PUBLIC_DEFAULT_LOCALE` | `fa` | Default locale (`fa` or `en`) |
| `NEXT_PUBLIC_POLL_INTERVAL_MS` | `2000` | Status polling cadence |
| `NEXT_PUBLIC_APP_NAME` | `PaperMind` | App name (head + footer) |
| `NEXT_PUBLIC_APP_TAGLINE` | `Turn books into summaries…` | OG description |

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `⌘K` / `Ctrl+K` | Command palette / search |
| `⌘B` / `Ctrl+B` | Toggle sidebar |
| `⌘N` / `Ctrl+N` | New book |
| `Enter` | Rename selected mind-map node |
| `Delete` / `Backspace` | Delete selected mind-map node |
