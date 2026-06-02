# Frontend

React + Vite interface for browsing the indexed images, running live searches, and viewing benchmark summaries.

The backend API and database must be running first. Vite proxies `/api` to `http://localhost:8000`, which matches the default FastAPI development server.

## Setup

```bash
cd frontend
npm install
```

## Run

Start the database and backend:

```bash
cd db
make up

cd ../backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Then start the frontend:

```bash
cd frontend
npm run dev
```

Open the URL printed by Vite, usually `http://localhost:5173`.

## Checks

```bash
npm run lint
npm run build
```

## Main Files

- `src/App.tsx` routes between image browsing, search, and benchmark views.
- `src/api.ts` contains all API calls.
- `src/engines.ts` defines display labels and categories for the engines.
- `src/components/` contains the page components.
