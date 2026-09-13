# AGENTS.md

Mini Kanban is spec-driven and frontend-first. Keep interfaces stable; replace the mock service, then the in-memory store, one layer at a time.

## Layout

```
/backend     FastAPI app: app/routers, app/models, app/store, tests
/docs        spec.md, tasks.md
/frontend    React + TypeScript (Vite)
AGENTS.md
openapi.yaml
Makefile
```

`docs/spec.md` is the product source of truth. `openapi.yaml` is the frontend/backend contract.

## Commands

Backend uses **uv**:

```
uv sync
uv add <PACKAGE-NAME>
uv run python <PYTHON-FILE>
uv run uvicorn app.main:app --reload --port 8091
uv run pytest
```

Run from `backend/` for uv commands.

```
make backend   # API on http://localhost:8091  (docs at /docs)
make dev       # frontend on http://localhost:5173
make test      # frontend Vitest + backend pytest
```

Frontend: `cd frontend && npm i && npm run dev` / `npm test`.

## Rules

- All backend calls go through `frontend/src/services`. Do not call `fetch` elsewhere.
- JSON is camelCase (`createdAt`, `columnId`, `wipLimit`) to match the frontend client.
- No authentication in v1.
- New boards seed To Do / In Progress / Done. The server re-indexes 0-based `position` on move/delete.
- Errors are `{ "detail": string }`.
- Keep `openapi.yaml` in sync when adding or changing endpoints.
- Run `make test` before committing. Commit regularly.
