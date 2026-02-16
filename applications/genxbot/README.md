# GenXBot (OpenClaw-style Autonomous Coding App)

This app is scaffolded in `applications/genxbot` and now wired to **GenXAI** primitives:

- `AgentFactory` + `AgentRuntime` for planner/executor/reviewer agents
- `MemorySystem` for per-run memory context
- `ToolRegistry` + built-in tools for tool-available execution context
- `CriticReviewFlow` for reviewer feedback loop

## Structure

```text
applications/genxbot/
  backend/
    app/
      api/routes_runs.py
      services/{orchestrator,policy,store}.py
      config.py
      schemas.py
      main.py
    tests/test_orchestrator.py
    requirements.txt
  frontend/
    src/{App.tsx,main.tsx,index.css}
    index.html
    package.json
    tsconfig*.json
    vite.config.ts
```

## Backend quick start

```bash
cd /Users/irsalimran/Desktop/GenXAI-OSS/applications/genxbot/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Frontend quick start

```bash
cd /Users/irsalimran/Desktop/GenXAI-OSS/applications/genxbot/frontend
npm install
npm run dev
```

## API

- `POST /api/v1/runs` create autonomous coding run
- `GET /api/v1/runs` list runs
- `GET /api/v1/runs/{run_id}` run details
- `POST /api/v1/runs/{run_id}/approval` approve/reject proposed action

## Notes

- If `OPENAI_API_KEY` is present, GenXAI runtime executes live planner/executor/reviewer pipeline.
- If key is missing or runtime fails, flow falls back to deterministic proposal while preserving GenXAI wiring.
- Approval gates remain active via `SafetyPolicy`.
