# Mini Kanban — Spec

**Status:** Draft v1.0 · **Date:** 2026-09-12  
**Stack:** React + TypeScript · FastAPI · SQLite via SQLAlchemy  
**Approach:** Spec-driven, frontend-first, contract-driven

A single-board task tracker: create a board, add columns and cards, drag cards between columns. State persists. No accounts. Built as a full-stack reference (UI → OpenAPI → backend → DB).

---

## Goals

- First card in under 30 seconds, no sign-up
- Create / edit / move / reorder / delete cards; persist across restart
- Versioned OpenAPI contract; agent-friendly repo (`AGENTS.md`, `Makefile`, tests)
- Deployable later without a rewrite

**Out of scope (v1):** auth, multiple boards in a picker UI beyond the current board, sharing, realtime, attachments/comments/labels/due dates/assignees, mobile apps, undo. Data model should not block these.

---

## Must-haves

**Board:** create (name 1–100), rename, load most recently used on open. Delete (cascade) is Should.

**Columns:** create (title 1–60), rename, delete (confirm if cards exist), seed new boards with *To Do / In Progress / Done*. Reorder by drag-and-drop is Should. WIP limit is Could.

**Cards:** create (title 1–200, optional description ≤ 2000), inline edit, drag-and-drop move + reorder, delete. Column card count is Should.

**Sync:** every mutation persisted immediately through the service layer; restart loses nothing once a real backend exists. Optimistic UI + rollback is Should.

**Quality:** autosave (no Save button); clear error if the backend/service is down.

---

## Build plan

Interfaces stay stable; replace internals one layer at a time.

1. Frontend + mock service (`frontend/src/services/` is the only API boundary)
2. `openapi.yaml` from that service layer
3. FastAPI + in-memory store; switch frontend to real client (fix CORS)
4. SQLite + SQLAlchemy (DB-agnostic ORM; Postgres later is a config change)

```
/backend   /docs   /frontend   AGENTS.md   openapi.yaml   Makefile
```

Backend: `uv`, port **8091**. Frontend: **5173**. `make run` / `make test`. Keep `openapi.yaml` in sync.

---

## Data model

| Entity | Fields |
|---|---|
| Board | `id` UUID, `name`, `created_at`, `updated_at` |
| Column | `id` UUID, `board_id` FK cascade, `title`, `position` (0-based), `wip_limit` nullable |
| Card | `id` UUID, `column_id` FK cascade, `title`, `description` nullable, `position` (0-based), `created_at`, `updated_at` |

Server re-indexes positions on every move.

---

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/boards` | Create (seeds default columns) |
| GET | `/boards` | List |
| GET | `/boards/{id}` | Board + nested columns/cards |
| PATCH | `/boards/{id}` | Rename |
| DELETE | `/boards/{id}` | Delete |
| POST | `/boards/{id}/columns` | Create column |
| PATCH | `/columns/{id}` | Rename, WIP, position |
| DELETE | `/columns/{id}` | Delete column |
| POST | `/columns/{id}/cards` | Create card |
| PATCH | `/cards/{id}` | Edit title/description |
| POST | `/cards/{id}/move` | Move to `{column_id, position}` |
| DELETE | `/cards/{id}` | Delete card |

JSON only. Errors: `{ "detail": string }`. No auth.

---

## Step 1 exit criteria (this milestone)

- App runs with `npm run dev`
- User stories work against the mock
- `frontend/src/services/` is the single integration point
- Frontend tests pass (`npm test`)
