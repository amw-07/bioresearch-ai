#!/usr/bin/env bash
set -euo pipefail

# Creates a virtual environment at .venv, installs requirements,
# and makes the local `uv` runner executable.
# Usage (from backend/):
#   ./setup_venv.sh
#   source .venv/bin/activate
#   python uv app.main:app --host 0.0.0.0 --port 8000

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  echo "requirements.txt not found in $(pwd)"
fi

if [ -f uv ]; then
  chmod +x uv
fi

echo "Virtualenv created at .venv. Activate with: source .venv/bin/activate"
echo "Run the app with: python uv app.main:app --host 0.0.0.0 --port 8000"