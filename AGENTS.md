# AGENTS.md

CantinAPP: backend-only (no frontend). FastAPI + async SQLAlchemy on Supabase PostgreSQL.

## Current state (read before assuming anything)
- Early scaffold. Only these Python files contain code:
  - `backend/app/main.py` (app + `/health`, `/health/db`)
  - `backend/app/core/config.py` (pydantic-settings)
  - `backend/app/shared/infrastructure/database.py` (engine/session)
- Every file under `backend/app/modules/<name>/` and most of `backend/app/shared/` is an **empty stub**. Do not assume endpoints, entities, or CQRS handlers exist.
- No tests/lint/typecheck are configured: `pyproject.toml`, `requirements-dev.txt`, `tests/conftest.py` are empty; pytest is not installed. Don't invent commands.
- `backend/package.json` pulls Supabase JS SDKs but there is **no JS/TS source** in the repo; it is unrelated to the Python backend.

## Commands (Windows PowerShell)
Run from `backend/`:
```powershell
py -m venv venv                         # README says .venv; actual dir is venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Must run from `backend/`: `Settings` loads `.env` from the current working directory.
- Health checks: `http://127.0.0.1:8000/health` and `/health/db`. Swagger at `/docs`.

## Setup requirements / gotchas
- Requires a reachable Supabase PostgreSQL. Run `db/schema.sql` in the Supabase SQL Editor first.
- `app.main` lifespan runs `SELECT 1` at startup and **fails fast** if the DB is unreachable.
- Create `backend/.env` from the template in the root `README.md` (`.env.example` is empty). `db_*` fields are required except those with defaults.
- `backend/scripts/check_db.py` is **broken**: it imports `app.infrastructure.database`, but the real module is `app.shared.infrastructure.database`.
- `db/schema.sql` is the source of truth for the schema: multitenancy via `business_id` + composite FKs, `products.stock_quantity` is a cache changed only through `inventory_movements`, inventory status is a view (`v_inventory`), products use soft delete (`is_active`).

## Architecture intent
- Hexagonal + CQRS, one folder per bounded context under `backend/app/modules/<name>/` with `domain/`, `application/`, `infrastructure/`, `api/`. Shared base pieces live in `backend/app/shared/`.
- Modules: `auth, products, inventory, sales, forecasting, recommendations, dashboard, analytics, alerts`.
- `get_db` yields one `AsyncSession` per request and does **not** auto-commit; application handlers must call `await session.commit()` explicitly.
