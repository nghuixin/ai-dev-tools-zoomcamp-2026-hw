# Mini Kanban frontend

React + TypeScript UI with every backend call behind `src/services`. The default client is an in-memory mock persisted to `localStorage`, so the app runs with no server.

```bash
npm install
npm run dev
npm test
```

The mock is exported from `src/services/index.ts`. Replace `boardService` with an HTTP client when FastAPI is ready.
