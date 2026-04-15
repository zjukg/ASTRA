#!/bin/bash
# ASTRA Demo Startup Script
# Usage:
#   ./start.sh          - Start backend only (frontend via Vite dev server separately)
#   ./start.sh --build  - Build frontend and start backend serving built files

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$1" = "--build" ]; then
    echo "Building frontend..."
    cd "$DIR/frontend"
    npm run build
    cd "$DIR"
fi

echo "Starting ASTRA Demo Server on http://localhost:8080"
echo "  API docs: http://localhost:8080/docs"

if [ -d "$DIR/frontend/dist" ]; then
    echo "  Frontend: http://localhost:8080 (built files)"
else
    echo "  Frontend: run 'cd frontend && npm run dev' in another terminal"
fi

cd "$DIR"
python server.py
