# AI Strategy Agent (P2P Brainstorming)

This app implements a **peer-to-peer brainstorming workflow** using the GenXAI framework and local observability hooks. It follows a layered architecture and uses SOLID + GoF patterns.

## Backend (FastAPI)

### Setup
```bash
cd applications/ai_strategy_agent/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run
```bash
uvicorn app.main:app --reload
```

### Endpoints
- `POST /api/v1/strategy/brainstorm`
- `POST /api/v1/strategy/brainstorm/stream` (SSE)
- `GET /api/v1/strategy/metrics`

### Environment Variables
Create `.env` in the backend folder:
```env
OPENAI_API_KEY=optional
```

## Frontend (React)

```bash
cd applications/ai_strategy_agent/frontend
npm install
npm run dev
```

Set `VITE_API_BASE` in `.env` if backend runs elsewhere.

## Notes
- P2P engine is in `app/domain/services/p2p_engine.py`
- Strategy policies (consensus/termination) are under `app/domain/policies/`
- Metrics adapter uses a local no-op implementation (`app/infra/metrics/metrics_adapter.py`)
