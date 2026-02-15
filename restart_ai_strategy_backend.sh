#!/bin/bash

# restart_ai_strategy_backend.sh - Script to restart the AI Strategy Agent backend

echo "🔄 Restarting AI Strategy Agent Backend..."

# Find and kill any existing backend processes
echo "🛑 Stopping existing backend processes..."
pkill -f "uvicorn.*app.main:app" || echo "No existing backend process found"
pkill -f "python.*app/main.py" || true
if command -v lsof >/dev/null 2>&1; then
    EXISTING_PIDS=$(lsof -t -iTCP:8000 -sTCP:LISTEN 2>/dev/null | tr '\n' ' ')
    if [ -n "$EXISTING_PIDS" ]; then
        echo "🔌 Port 8000 in use by PID(s): $EXISTING_PIDS. Stopping..."
        kill $EXISTING_PIDS 2>/dev/null || true
    fi
fi

# Wait a moment for processes to fully terminate
sleep 2

# Navigate to the project root directory (script is located in repo root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

# Check if virtual environment exists in ai strategy backend
BACKEND_ROOT="$PROJECT_ROOT/applications/ai_strategy_agent/backend"
if [ -d "$BACKEND_ROOT/venv" ]; then
    echo "🐍 Activating virtual environment..."
    source "$BACKEND_ROOT/venv/bin/activate"
elif [ -d "$BACKEND_ROOT/.venv" ]; then
    echo "🐍 Activating virtual environment..."
    source "$BACKEND_ROOT/.venv/bin/activate"
else
    echo "⚠️  No virtual environment found. Creating one at $BACKEND_ROOT/.venv"
    python3 -m venv "$BACKEND_ROOT/.venv"
    source "$BACKEND_ROOT/.venv/bin/activate"
fi

# Check if required dependencies are installed
echo "🔍 Checking dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null || ! python3 -c "import uvicorn" 2>/dev/null || ! python3 -c "import openai" 2>/dev/null; then
    echo "📦 Installing backend dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r "$BACKEND_ROOT/requirements.txt"
fi

# Create logs directory if it doesn't exist
mkdir -p "$BACKEND_ROOT/logs"

# Ensure local GenXAI package is used instead of pip-installed fallback
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH}"

# Start the backend server
echo "🚀 Starting backend server..."
cd "$BACKEND_ROOT"

# Run uvicorn with timestamped logs (Python prefix for macOS compatibility)
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
    2>&1 | python3 -u -c '
import sys
from datetime import datetime
for line in sys.stdin:
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    sys.stdout.write(f"{ts} {line}")
    sys.stdout.flush()
' > "$BACKEND_ROOT/logs/backend.log" &

# Store the PID
BACKEND_PID=$!
echo $BACKEND_PID > "$BACKEND_ROOT/logs/backend.pid"

# Wait a moment for the server to start
sleep 3

# Check if the server is actually running
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "✅ Backend started successfully with PID: $BACKEND_PID"
    echo "📡 Backend should be available at http://localhost:8000"
    echo "📚 API docs available at http://localhost:8000/docs"
    echo "📝 Logs available at: $BACKEND_ROOT/logs/backend.log"
    echo ""
    echo "To stop the backend, run: kill $BACKEND_PID"
    echo "Or use: pkill -f 'uvicorn.*app.main:app'"
else
    echo "❌ Error: Backend failed to start. Check logs at: $BACKEND_ROOT/logs/backend.log"
    exit 1
fi
