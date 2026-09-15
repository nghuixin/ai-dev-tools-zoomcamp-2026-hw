.PHONY: run backend dev test test-integration test-e2e e2e image postgres up aws-deploy aws-destroy

postgres:
	docker compose up -d postgres

up:
	docker compose up --build

run backend:
	cd backend && uv run uvicorn app.main:app --reload --reload-dir app --port 8091

dev:
	cd frontend && npm run dev

test:
	cd frontend && npm test
	cd backend && uv run pytest -m "not integration"

test-integration:
	cd backend && uv run pytest ../tests/integration -m integration

test-e2e e2e:
	cd e2e && npm test

image:
	docker build -t mini-kanban .

aws-deploy:
	pwsh -File infra/deploy.ps1

aws-destroy:
	pwsh -File infra/destroy.ps1
