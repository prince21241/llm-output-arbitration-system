# Frontend

Vite + React workspace for the evaluate API.

## Run

Start the API from `backend/` first (`uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`), then:

```bash
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Vite proxies `/api` and `/health` to the FastAPI server.

Visual rules live in [`DESIGN.md`](../DESIGN.md). Agent skills live in [`.agents/skills`](../.agents/skills).
