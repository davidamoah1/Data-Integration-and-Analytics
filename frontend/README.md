# DataFlow Frontend

Enterprise Next.js frontend for the DataFlow Data Intelligence Platform.

## Quick Start

```bash
cd frontend
npm install --legacy-peer-deps
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Tech Stack

- **Next.js 14** (App Router, TypeScript)
- **Tailwind CSS** + custom design system
- **Zustand** (state management)
- **Lucide React** (icons)
- **Sonner** (toasts)
- **Recharts** (charts)
- **Vitest** + **Testing Library** (tests)

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── (app)/             # Protected routes (with AppShell)
│   │   ├── dashboard/     # Main dashboard
│   │   ├── datasets/      # Dataset management
│   │   ├── analytics/     # Analytics & dashboards
│   │   ├── ai/            # AI Copilot
│   │   ├── reports/       # Reports
│   │   ├── scheduler/     # Scheduled reports
│   │   ├── notifications/ # Notifications
│   │   ├── admin/         # Administration
│   │   └── settings/      # User settings
│   ├── login/             # Login page (public)
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Root redirect
├── components/
│   ├── ui/                # Reusable UI components
│   └── layout/            # App shell, sidebar, top nav
├── features/              # Feature-specific components
├── lib/                   # Utilities
├── providers/             # Theme, Auth providers
├── services/              # API service layer
│   ├── api/               # Centralized API client
│   ├── auth/              # Auth service
│   ├── datasets/          # Dataset service
│   ├── dashboard/         # Dashboard service
│   └── ai/                # AI service
├── stores/                # Zustand stores
├── types/                 # TypeScript types
└── tests/                 # Vitest tests
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | FastAPI backend URL | `http://localhost:8000` |
| `NEXT_PUBLIC_APP_NAME` | App name shown in UI | `DataFlow` |

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run test` | Run tests (watch) |
| `npm run test:run` | Run tests (once) |
| `npm run type-check` | TypeScript check |

## Backend Integration

See `docs/frontend-api-map.md` for the complete API reference.

The API client (`services/api/client.ts`) handles:
- JWT Bearer token authentication
- Automatic token refresh on 401
- Typed responses
- Error normalization
- Request timeout & retries
- FormData uploads

## Deployment

### Vercel
1. Import the `frontend/` folder in Vercel
2. Set `NEXT_PUBLIC_API_URL` env var
3. Deploy

### Manual
```bash
npm run build
npm run start
```

## Security

- No secrets in frontend code
- JWT tokens stored in localStorage (httpOnly cookies recommended for production)
- Security headers set in `next.config.js`
- RBAC enforced via `useAuthStore.hasPermission()`
- Protected routes via `AppShell` wrapper
