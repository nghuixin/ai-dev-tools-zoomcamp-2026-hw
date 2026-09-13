# Mini Kanban frontend

React + TypeScript UI with every backend call behind `src/services`. The default client is `createHttpBoardService()`, which talks to FastAPI at `http://localhost:8091` (override with `VITE_API_URL`).

```bash
npm install
npm run dev
npm test
```

Keep the backend running (`make backend`) while using the app. Tests can still inject `createMockBoardService()`.
