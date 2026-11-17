# frontend — Vue 3 app

Vue 3 + TypeScript (strict) + Vite + Vue Router. No state library unless a step asks for it.
Consumes the API described in `api/CLAUDE.md` (the contract is the source of truth).

## Commands (run inside `frontend/`)
```bash
npm run dev          # Vite on :5173, proxies /api -> http://localhost:5000
npm run build        # vue-tsc --build && vite build
npm run lint         # eslint .
npm run format       # prettier --write src/
npm run format:check # prettier --check src/
npm run type-check   # vue-tsc --build
npm run test:unit    # vitest run --coverage
```

## Layout
```
frontend/
  Dockerfile           # stage 1: node build; stage 2: nginx serving dist/
  nginx.conf           # SPA fallback + location /api/ { proxy_pass http://api:5000/; }
  vite.config.ts       # server.proxy['/api'] with rewrite that strips /api
  src/
    api/types.ts       # Species, Iris, ListResponse, PageResponse, ApiError (mirror the contract)
    api/iris.ts        # listIris(species, filters, pagination?), getIris(species, id)
    composables/useIrisList.ts   # loading / error / data state, keeps filters in the URL query
    components/        # SpeciesTabs, IrisTable, IrisFilters, PaginationControls, ErrorBanner
    views/             # SpeciesListView (/:species), IrisDetailView (/:species/:id)
    router/index.ts    # / redirects to /setosa; unknown species -> NotFoundView
  src/**/__tests__/    # *.spec.ts next to the code they test
```

## UI requirements
- Tabs for the three species; each tab is a route.
- Table with all columns; clicking a row opens the detail view.
- Filter form: min/max inputs for every numeric column plus exact `id`; "Apply" and "Clear".
- "Paginate" toggle. When on: per-page select (10 default, 25, 50, 100) and previous/next with "page X of Y".
- Filters and pagination are stored in the URL query, so reload/back/forward keep the state.
- Loading, empty and error states are visible (error shows the API `error.message`).

## Rules
- `<script setup lang="ts">` + Composition API only. No `any`.
- All HTTP goes through `src/api/iris.ts`; components never call `fetch` directly.
- Base URL is `/api` (relative), so the same build works behind nginx and the Vite proxy.
- Tests: API client (URL building, error mapping), `useIrisList`, and each component's main behaviour.
- ESLint (flat config, `eslint-plugin-vue` + `typescript-eslint`) and Prettier must pass with zero warnings.
