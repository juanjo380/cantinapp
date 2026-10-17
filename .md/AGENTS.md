# AGENTS.md

CantinAPP: SaaS for small businesses (inventory + demand forecasting). Monorepo:
- `backend/`: FastAPI + async SQLAlchemy on Supabase PostgreSQL. MVP v0.1 complete (9 modules). Deployed on Render at `https://cantinapp.onrender.com`.
- `frontend/`: React + Vite + React Router + Material UI. Being built on top of the deployed API.
- `db/schema.sql`: source of truth for the database schema.

## Read first
- `memoria.md` is the project's technical memory. Before touching the API contract, read section 7 (endpoints, request/response shapes) and section 10 (notes for the frontend). Do not guess endpoint names, fields or status codes.
- `PRODUCT.md` and `DESIGN.md` (created by `/impeccable init`) define product context and visual direction. Read them before any UI work.

## Backend (run from `backend/`)
```powershell
.\venv\Scripts\Activate.ps1        # create the venv outside OneDrive if pip fails
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Must run from `backend/`: `Settings` loads `.env` from the current working directory.
- Requires a reachable Supabase PostgreSQL; `app.main` runs `SELECT 1` at startup and fails fast if it is unreachable.
- Architecture: hexagonal + CQRS, one folder per bounded context under `backend/app/modules/<name>/` with `domain/`, `application/`, `infrastructure/`, `api/`. `get_db` yields one `AsyncSession` per request and does **not** auto-commit; handlers must call `await session.commit()`.
- Multitenancy: every business endpoint filters by the `business_id` of the authenticated user. Never accept `business_id` from the client.
- Stock is a cache of `inventory_movements`; it is never edited directly.
- Do not edit secrets or `.env` files. Never print or commit credentials.

## Frontend (run from `frontend/`)
```powershell
npm install
npm run dev      # http://localhost:5173
npm run lint
npm run build
```
- API base URL comes from `VITE_API_URL` (`frontend/.env`), never hardcoded. All routes are under `/api`.
- Auth: JWT sent as `Authorization: Bearer <token>`. On a `401`, clear the session and redirect to `/login`.
- The first request after inactivity can take 30-60 seconds (Render free tier cold start). Always show a loading state; do not treat it as an error with a short timeout.
- Stack is fixed: React, Vite, React Router, Material UI. Do not add other UI libraries. Add any dependency only with a clear benefit.

## Design
- Establish a distinctive visual direction before coding, following `DESIGN.md`, frontend-design and Impeccable.
- All visual decisions go through a single MUI theme (`src/theme.js`): palette, typography, shape, spacing and component overrides. No loose colors, fonts or border radii inside components.
- Avoid generic AI-generated layouts and repetitive card grids. Do not default to purple gradients, glassmorphism or oversized rounded cards.
- Use intentional typography, spacing, hierarchy and a coherent color system. Override MUI's default look (Roboto, default blue, heavy elevation).
- Every data view must cover loading, empty and error states.
- Layouts must be responsive and accessible (semantic HTML, keyboard support, contrast, `prefers-reduced-motion`).
- Preserve the existing design system when modifying existing screens.

## React
- Reuse existing components before creating new ones. Keep components focused.
- Avoid unnecessary state, effects, re-renders and abstractions (follow Ponytail for logic).
- Prefer lightweight CSS and browser-native capabilities. Lazy-load non-critical code and images.
- Never sacrifice accessibility or correctness for a smaller bundle.

## Workflow
1. Inspect the existing project before editing.
2. Establish the design direction and a short implementation plan.
3. Implement the smallest complete solution.
4. Run `npm run lint` and `npm run build` (frontend) or `python -m pytest` (backend) when relevant.
5. Check responsive layout, accessibility and performance.
6. Report what changed and any remaining issues.