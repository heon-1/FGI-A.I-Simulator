#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Please install Python 3.10+" 1>&2
  exit 1
fi

if [ ! -d .venv ]; then
  echo "Creating virtual environment at $REPO_ROOT/.venv"
  python3 -m venv .venv
fi

echo "Activating venv and installing requirements..."
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo
echo "Done. Activate with:"
echo "  source .venv/bin/activate"
echo "Then run, e.g.:"
echo "  python -m ux_tool.cli.fgi --q data/questionnaires/fgi.json --p data/personas --s data/scenarios/default.json"


