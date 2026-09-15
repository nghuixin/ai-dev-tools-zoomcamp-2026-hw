# Mini Kanban 看板/かんばん

A small Kanban board: React frontend + FastAPI backend. The UI talks to the API at `http://localhost:8091`.

## Project structure

```
frontend/                 React + Vite UI. All API calls go through src/services/
backend/                  FastAPI app: routers, models, SQLAlchemy store, unit tests
tests/integration/        HTTP tests against docker-compose.yml
e2e/                      Playwright two-session tests
docs/                     spec, testing, deployment, release
Dockerfile
docker-compose.yml
.github/workflows/        ci.yml, deploy.yml
openapi.yaml              frontend/backend contract
AGENTS.md
Makefile
```

## Prerequisites

- Node.js (for the frontend)
- [uv](https://docs.astral.sh/uv/) (for the backend)
- Make (optional; commands below also work without it)

## First-time setup

```bash
cd frontend && npm install
cd ../backend && uv sync --group dev
```

## Launch

Use **two terminals**. Start the backend first.

**Backend** (API + Swagger):

```bash
make run
```

or

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8091
```

- App API: http://localhost:8091
- OpenAPI UI: http://localhost:8091/docs

**Frontend** (board):

```bash
make dev
```

or

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**. The client uses `http://localhost:8091` (`VITE_API_URL` to override).

A **Workshop** board is seeded when the database is empty. With `SDIP_DATABASE_URL` / `DATABASE_URL` pointing at Postgres (or Compose), restarts keep data.

**All-in-one (UI + API + Postgres):** `docker compose -f docker-compose.yml up --build` → http://localhost:8091

## Tests

See [docs/testing.md](docs/testing.md).

```bash
make test                 # frontend + backend unit
make test-integration     # docker-compose.yml
make e2e                  # Playwright
```

Deploy and release: [docs/deployment.md](docs/deployment.md), [docs/release-process.md](docs/release-process.md).
