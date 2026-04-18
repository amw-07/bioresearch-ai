#!/usr/bin/env bash
# .devcontainer/setup.sh
# Runs after Codespace container is created.
# Installs all dependencies for both backend and frontend.
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   BioResearch AI — Codespaces Setup      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── PATH: add uv and cargo bin ────────────────────────────────────────────────
export PATH="$HOME/.cargo/bin:$PATH"

# ── Backend: install Python dependencies via uv ───────────────────────────────
echo "[1/4] Installing backend Python dependencies..."
cd /workspaces/bioresearch-ai/backend
uv pip install -r requirements.txt --system
echo "      ✓ Backend dependencies installed"

# ── Backend: copy .env if not present ────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo "      ✓ Created backend/.env from .env.example"
  echo "      ⚠  Fill in your secrets in backend/.env or set Codespaces secrets"
fi

# ── ML: generate training data + train model ─────────────────────────────────
echo "[2/4] Training RandomForest scorer (≈30 seconds)..."
mkdir -p ml/models ml/reports
python scripts/generate_training_data.py
python ml/train_scorer.py
echo "      ✓ scorer_v1.joblib created, eval_v1.json updated"

# ── Frontend: install Node dependencies ───────────────────────────────────────
echo "[3/4] Installing frontend Node dependencies..."
cd /workspaces/bioresearch-ai/frontend
npm install
echo "      ✓ Frontend dependencies installed"

# ── Frontend: copy .env if not present ───────────────────────────────────────
if [ ! -f .env.local ]; then
  echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
  echo "      ✓ Created frontend/.env.local (points to local backend)"
fi

echo ""
echo "[4/4] Setup complete!"
echo ""
echo "┌─────────────────────────────────────────────────────────────────┐"
echo "│  Start backend:   cd backend && uvicorn app.main:app --reload   │"
echo "│  Start frontend:  cd frontend && npm run dev                    │"
echo "│  API docs:        http://localhost:8000/docs                    │"
echo "│  Dashboard:       http://localhost:3000                         │"
echo "└─────────────────────────────────────────────────────────────────┘"
echo ""
echo "  Set Codespaces secrets (Settings → Codespaces → Secrets):"
echo "  - DATABASE_URL, REDIS_URL, GEMINI_API_KEY, PUBMED_EMAIL, SECRET_KEY"
echo ""