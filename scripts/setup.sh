#!/usr/bin/env bash
set -euo pipefail

echo "=== OmniAgent Setup ==="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not found."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not found."; exit 1; }
command -v docker >/dev/null 2>&1 || echo "Warning: Docker not found — docker-compose up will not work."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Copy env file
if [ ! -f "$PROJECT_ROOT/.env" ]; then
  cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  echo "Created .env from .env.example — please fill in your API keys."
fi

# Backend setup
echo "--- Setting up backend ---"
cd "$PROJECT_ROOT/backend"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null || true
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "Backend dependencies installed."

# Frontend setup
echo "--- Setting up frontend ---"
cd "$PROJECT_ROOT/frontend"
npm install --silent
echo "Frontend dependencies installed."

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To start with Docker:"
echo "  docker-compose up --build"
echo ""
echo "To start manually:"
echo "  # Terminal 1 — Backend"
echo "  cd backend && source .venv/bin/activate && uvicorn main:app --reload"
echo ""
echo "  # Terminal 2 — Frontend"
echo "  cd frontend && npm run dev"
