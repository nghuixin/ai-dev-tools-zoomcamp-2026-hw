.PHONY: run backend dev test

run backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8091

dev:
	cd frontend && npm run dev

test:
	cd frontend && npm test
	cd backend && uv run pytest
