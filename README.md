# Mini Kanban 看板/かんばん

A small Kanban board: React frontend + FastAPI backend. The UI talks to the API at `http://localhost:8091`.

## Project structure

```
frontend/        React + Vite UI. All API calls go through src/services/
backend/         FastAPI app: routers, models, in-memory store, tests
docs/            spec, design tasks, AI usage report
openapi.yaml     frontend/backend contract
AGENTS.md        instructions for coding agents
Makefile         make run / make dev / make test
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

The store is in-memory. Restarting the backend resets data; a **Workshop** board is seeded on startup.

## Tests

```bash
make test
```

or

```bash
cd frontend && npm test
cd backend && uv run pytest
```
