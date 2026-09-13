**Tools.** Cursor for all code and docs in the repo. The spec (`docs/spec.md`) was first drafted and trimmed in ChatGPT, then pasted into Cursor and built from there.

**Workflow.** Spec-first, in the order the spec laid out: mock UI → OpenAPI → FastAPI in-memory → real HTTP client (SQLite still pending). Concretely: React/Vite frontend with a single service layer and `createMockBoardService()` (memory + `localStorage`) so the UX could be exercised with no server; `openapi.yaml` derived from that service interface (12 endpoints, camelCase JSON, `{ "detail": string }` errors, no auth, port 8091); FastAPI backend split into `models` / `store` / `routers` with a seeded Workshop board; default client switched to `createHttpBoardService()` (`VITE_API_URL`, default `http://localhost:8091`); then reconciling `/docs` with the contract.

**Prompts that drove the work.**

- Create a Mini Kanban with one services layer and a mock client behind it.
- Derive an OpenAPI spec from that client interface.
- Implement the FastAPI backend as `routers` / `models` / `store`, in-memory, with tests.
- Switch the frontend default to the real HTTP client.
- Document 400/404 with an `Error` schema instead of FastAPI's default 422.
- Record decisions in `docs/tasks.md`; add `.gitignore`, `AGENTS.md`, and `make` targets.

**What I kept as-is.** camelCase JSON matching the frontend types; no auth; `make run` / `make backend` on 8091, `make dev` for the frontend, `make test` for both suites; mock service used only in tests; `docs/tasks.md` as a decision log ("chose not to build" vs "forgot to build"); `AGENTS.md` as the conventions file (uv, make, service-layer rule, keep OpenAPI in sync).

**Where the AI missed or needed correcting.**

- Didn't produce `AGENTS.md` until explicitly asked.
- Treated `localhost:8091/` as the spec surface; the spec surface is `/docs`.
- Generated `/docs` advertised 422 and FastAPI validation schemas while the running app already returned 400/404 — contract and docs drifted. Paths, methods, and `operationId`s did match.

**Verified by hand.** `make test` (frontend and backend); loading the seeded Workshop board in the browser and creating a card via POST; side-by-side check of `/docs` against `openapi.yaml`.

 ****