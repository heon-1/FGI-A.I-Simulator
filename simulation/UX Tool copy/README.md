UX Tool - AI Persona Research Simulator (Python + Gemini)

Overview
This project simulates UX research using AI personas with two modes:
- FGI: Focus Group Interview with moderator and multiple personas interacting.
- Individual: One-on-one questionnaire responses per persona.

Features
- Pydantic-based validation for personas, questionnaires, and scenarios.
- Gemini adapter with retry and simple safety filters.
- Turn orchestration, transcript logging, tagging and summarization stubs.
- CLI for both modes and structured outputs per session.

Quickstart
1) Python 3.10+
2) Create venv and install deps (macOS zsh):
   ./scripts/setup_venv.sh
   # or manual
   python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
3) Create .env and set GEMINI_API_KEY (optional for dev fallback)
4) Run FGI mode:
   bash scripts/run_fgi.sh --q data/questionnaires/fgi.json --p data/personas --s data/scenarios/default.json
   # or:
   PYTHONPATH=src python -m ux_tool.cli.fgi --q data/questionnaires/fgi.json --p data/personas --s data/scenarios/default.json
5) Run Individual mode:
   bash scripts/run_individual.sh --q data/questionnaires/individual.json --p data/personas --s data/scenarios/default.json --max-rounds 3
   # or:
   PYTHONPATH=src python -m ux_tool.cli.individual --q data/questionnaires/individual.json --p data/personas --s data/scenarios/default.json --max-rounds 3

Journey CLI
- Build journey map CSV from a session:
  PYTHONPATH=src python -m ux_tool.cli.journey map \
    --session outputs/fgi/<session_id> \
    --out outputs/fgi/<session_id>/journey_map.csv
- Simulate journey with Gemini (single persona):
  PYTHONPATH=src python -m ux_tool.cli.journey simulate \
    --goal "여름 이불 최저가로 구매" \
    --persona-id p_early_01 \
    --fgi-session outputs/fgi/<session_id> \
    --ind-session outputs/individual/<session_id> \
    --out outputs/simulations/journey_p_early_01.csv
- Simulate for all personas:
  PYTHONPATH=src python -m ux_tool.cli.journey simulate \
    --goal "여름 이불 최저가로 구매" \
    --all-personas \
    --personas data/personas \
    --out-dir outputs/simulations/journeys_all

Project Structure
See src/ux_tool for implementation. Data resides under data/, outputs under outputs/.

Notes
- If GEMINI_API_KEY is missing, the system falls back to deterministic placeholders for development.
 - When running modules directly with python -m, ensure PYTHONPATH includes src (e.g., PYTHONPATH=src).


bash scripts/run_fgi.sh \
  --q data/questionnaires/fgi.json \
  --p data/personas \
  --s data/scenarios/default.json \
  --max-rounds 16



bash scripts/run_individual.sh \
  --q data/questionnaires/individual.json \
  --p data/personas \
  --s data/scenarios/default.json \


PYTHONPATH=src python3 scripts/simulate_journey_gemini.py \
  --goal "여름 이불 구매" \
  --all-personas \
  --personas data/personas \
  --fgi-session "/Users/admin/Desktop/Product/UX Tool/outputs/fgi/20251107T061720Z-aa9f1ba2" \
  --ind-session "/Users/admin/Desktop/Product/UX Tool/outputs/individual/20251106T195912Z-e6c06677" \
  --out-dir outputs/simulations/journeys_all


  PYTHONPATH=src python3 scripts/session_transcripts_to_csv.py \
  --session "/Users/admin/Desktop/Product/UX Tool/outputs/fgi/20251107T074253Z-fe4b3b4c" \
  --out "/Users/admin/Desktop/Product/UX Tool/outputs/fgi/20251107T074253Z-fe4b3b4c/merged_transcript.csv"