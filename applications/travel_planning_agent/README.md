# Travel Planning Agent (GenXAI)

This app is a **GenXAI-powered travel planning agent** with:
- **FastAPI backend** (JWT auth, SQLite, streaming progress, GenXAI workflow)
- **React frontend** (login/register, planner form, live updates, itinerary view)

## Backend Setup

```bash
cd travel_planning_agent/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will run at `http://localhost:8000`.

## Frontend Setup

```bash
cd travel_planning_agent/frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Environment Variables

Create `travel_planning_agent/backend/.env`:

```env
JWT_SECRET=change-me
OPENAI_API_KEY=optional
```

You can also set `VITE_API_BASE` in `travel_planning_agent/frontend/.env` if the backend runs elsewhere.

## API Summary

- `POST /api/v1/auth/register` → create user and get token
- `POST /api/v1/auth/login` → login and get token
- `POST /api/v1/planner/plan` → non-stream plan
- `POST /api/v1/planner/plan/stream` → SSE stream (progress + final plan)

## Testing

```bash
cd travel_planning_agent/backend
pytest
```