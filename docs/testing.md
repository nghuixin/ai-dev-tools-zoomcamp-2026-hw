# Testing

Three layers, from fastest to slowest. CI is `.github/workflows/ci.yml`.

## Unit (parallel in CI)

Frontend Vitest and backend pytest run as two jobs.

```bash
make test
# or
cd frontend && npm test
cd backend && uv run pytest -m "not integration"
```

## Compose integration + e2e

CI builds `docker-compose.yml` once, waits for `GET /health`, then runs both suites against that stack (`INTEGRATION_BASE_URL` / `E2E_BASE_URL`).

Locally:

```bash
docker compose -f docker-compose.yml up -d --build
# wait until curl -fsS http://127.0.0.1:8091/health
INTEGRATION_BASE_URL=http://127.0.0.1:8091 make test-integration
E2E_BASE_URL=http://127.0.0.1:8091 make e2e
```

Or let the fixtures start their own isolated compose projects:

```bash
make test-integration
make e2e
```

Integration lives in `tests/integration/`. Playwright is `e2e/` (two isolated browsers, join link `/?board=<id>`).

## Health

`GET /health` returns `{"status":"ok"}` when the store/DB answers. Compose, the ALB, and the deploy job all use this path.

## Deploy gate

On push to `main`/`master`, if `AWS_ROLE_ARN` is set, CI calls `.github/workflows/deploy.yml` after Compose tests pass.
