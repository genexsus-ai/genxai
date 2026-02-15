#!/bin/bash

# restart_travel_planning_frontend.sh - Script to restart the Travel Planning Agent frontend

echo "🔄 Restarting Travel Planning Agent Frontend..."

# Find and kill any existing frontend processes
echo "🛑 Stopping existing frontend processes..."
pkill -f "vite" || echo "No existing frontend process found"
pkill -f "node.*vite" || true

# Wait a moment for processes to fully terminate
sleep 2

# Navigate to the project root directory (script is located in repo root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

# Navigate to frontend directory
FRONTEND_ROOT="$PROJECT_ROOT/applications/travel_planning_agent/frontend"
cd "$FRONTEND_ROOT"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the frontend development server
echo "🚀 Starting frontend development server..."
npm run dev &

# Store the PID
FRONTEND_PID=$!
echo "✅ Frontend started with PID: $FRONTEND_PID"
echo "🌐 Frontend should be available at http://localhost:5173"
echo ""
echo "To stop the frontend, run: kill $FRONTEND_PID"

# Wait a moment for the server to start
sleep 3

# Open the site in the default browser
echo "🌐 Opening site in browser..."
open http://localhost:5173