# MigrateAI Frontend

React + Vite + TypeScript frontend for the MigrateAI code migration platform.

## Stack

- React 19
- Vite 6
- React Router 7
- Tailwind CSS 4
- TanStack Query, Zustand, Axios

## Development

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

App runs at http://localhost:3000

## Environment

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API base URL (default: `http://localhost:8000/api/v1`) |

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## Docker

The Dockerfile builds static assets with Vite and serves them via nginx on port 80.
