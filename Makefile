.PHONY: dev backend test

dev:
	cd frontend && npm run dev

backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8091

test:
	cd frontend && npm test
	cd backend && uv run pytest
