# Design decisions (completed)

Record of choices made for Mini Kanban Step 1 (frontend + mock service). Each item is done.

## Service layer

- [x] **One `BoardService` interface**  
  Every mutation and query goes through `frontend/src/services`. UI and hooks never call `fetch` or talk to storage directly. This is the future OpenAPI client boundary.

- [x] **Method names match the planned REST API**  
  `createBoard`, `getBoard`, `updateColumn`, `moveCard`, etc. map 1:1 to the paths in the spec so `openapi.yaml` can be derived without renaming.

- [x] **Mock factory + injectable key-value store**  
  `createMockBoardService({ kv })` uses `localStorage` in the app and an in-memory map in tests. Same code path, no hidden globals.

- [x] **Structured errors (`ApiError` / `{ detail }`)**  
  Validation and 404s throw a typed error with `detail` and `status`, matching the spec’s JSON error shape.

- [x] **Server-side position reindex**  
  Moves and deletes rewrite `position` to a dense 0-based sequence. The UI never computes gaps.

- [x] **Hard delete with cascade**  
  Deleting a board removes its columns and cards; deleting a column removes its cards. Soft-delete was left as an open question and not implemented.

- [x] **No authentication**  
  Explicit v1 non-goal. The contract stays unauthenticated until a later step.

## Product / data model

- [x] **New boards seed To Do / In Progress / Done**  
  First card in under 30 seconds; no empty-board setup.

- [x] **Field limits from the spec**  
  Board name 1–100, column title 1–60, card title 1–200, description ≤ 2000, trimmed on write.

- [x] **WIP limit included though it is a Could**  
  The field is already on the column model; a small input and over-limit warning cost little and keep the mock aligned with the future API.

- [x] **Last-used board stored in the client**  
  `mini-kanban.lastBoardId` is UI state, not an API field. The mock has no “current user.”

- [x] **Board switcher is a thin exception to “no multi-board product”**  
  Create/list/open is required by the API (`GET/POST /boards`) and by “load most recently used.” It is not a full board manager.

## UI

- [x] **Autosave, no Save button**  
  Blur and submit persist immediately through the service.

- [x] **Optimistic updates with rollback on rename/move**  
  Board/column rename and card move update the UI first; a failed service call restores the previous snapshot and shows a banner.

- [x] **Visible error banner**  
  Unreachable or invalid service results must not fail silently.

- [x] **`@dnd-kit` for cards and columns**  
  Chosen over raw HTML5 DnD for nested lists and a path to keyboard fallback later.

- [x] **Confirm before destroying work**  
  Column delete confirms when cards exist; board delete always confirms.

- [x] **Inject `BoardService` into `App`**  
  Tests pass a fresh mock; the running app uses the default `boardService` export.

## Tests and tooling

- [x] **Vitest + Testing Library + jsdom**  
  Matches the spec’s frontend test stack; `npm test` / `make test`.

- [x] **Service-layer coverage first**  
  CRUD, validation, cascade delete, reindex, and 404s are unit-tested on the mock.

- [x] **UI tests for the happy path and error banner**  
  Create seeded board, add/edit/delete card, surface `ApiError` text.

- [x] **Service-boundary check**  
  Fail if `fetch` / `XMLHttpRequest` / `axios` appear outside `frontend/src/services`.

- [x] **Vite + React + TypeScript**  
  Default frontend for this course workflow; port 5173 as specified.

## Deferred (not tasks for Step 1)

These were decided *against* for this milestone, not forgotten:

- Real FastAPI backend and `openapi.yaml` (Steps 2–3)
- SQLite / `DATABASE_URL` (Step 4)
- Auth, sharing, realtime, labels, undo
- Soft-delete and shareable slugs (still open in the spec)
