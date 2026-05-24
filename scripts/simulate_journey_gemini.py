#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Optional

from ux_tool.adapters.gemini.client import GeminiClient
from ux_tool.config.gemini_config import load_gemini_settings
from ux_tool.core.simulation.journey_simulator_gemini import simulate_with_gemini
from ux_tool.io.validator import load_personas_from_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate a persona's journey using Gemini based on goal and transcripts.")
    parser.add_argument("--goal", required=True, help="Goal statement (e.g., '여름 이불 최저가로 구매').")
    parser.add_argument("--personas", default="data/personas", help="Personas directory")
    parser.add_argument("--persona-id", help="Persona id to simulate as")
    parser.add_argument("--all-personas", action="store_true", help="Run simulation for every persona in --personas")
    parser.add_argument("--fgi-session", help="FGI session directory (outputs/fgi/<session_id>)")
    parser.add_argument("--ind-session", help="Individual session directory (outputs/individual/<session_id>)")
    parser.add_argument("--out", help="Output CSV file path (single persona mode)")
    parser.add_argument("--out-dir", help="Output directory for per-persona CSVs (required with --all-personas)")
    parser.add_argument("--ctx-chars", type=int, default=2000, help="Max chars per transcript context block")
    args = parser.parse_args()

    gcfg = load_gemini_settings()
    client = GeminiClient(gcfg)

    personas_dir = Path(args.personas) if args.personas else None
    fgi_dir = Path(args.fgi_session) if args.fgi_session else None
    ind_dir = Path(args.ind_session) if args.ind_session else None

    if args.all_personas:
        if not personas_dir or not personas_dir.exists():
            raise SystemExit(f"--personas directory not found: {personas_dir}")
        if not args.out_dir:
            raise SystemExit("--out-dir is required when using --all-personas")
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        personas = load_personas_from_dir(personas_dir)
        fieldnames = [
            "goal",
            "persona_id",
            "persona_name",
            "step",
            "stage",
            "action_label",
            "rationale",
            "expected_outcome",
            "subtasks",
            "inputs",
            "outputs",
            "system_touchpoints",
            "success_metric",
            "risks",
            "mitigations",
            "owner",
            "eta",
        ]
        for p in personas:
            rows = simulate_with_gemini(
                client=client,
                goal=args.goal,
                personas_dir=personas_dir,
                persona_id=p.id,
                fgi_session_dir=fgi_dir,
                ind_session_dir=ind_dir,
                max_chars_each=args.ctx_chars,
            )
            out_csv = out_dir.joinpath(f"journey_{p.id}.csv")
            with out_csv.open("w", encoding="utf-8", newline="") as f:
                import csv

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"[OK] Wrote Gemini journey simulation CSV: {out_csv}")
        return

    # single persona mode
    persona_id: Optional[str] = args.persona_id
    if not persona_id:
        raise SystemExit("Provide --persona-id or use --all-personas")
    if not args.out:
        raise SystemExit("--out is required for single persona mode")
    out_csv = Path(args.out)

    rows = simulate_with_gemini(
        client=client,
        goal=args.goal,
        personas_dir=personas_dir,
        persona_id=persona_id,
        fgi_session_dir=fgi_dir,
        ind_session_dir=ind_dir,
        max_chars_each=args.ctx_chars,
    )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "goal",
        "persona_id",
        "persona_name",
        "step",
        "stage",
        "action_label",
        "rationale",
        "expected_outcome",
        "subtasks",
        "inputs",
        "outputs",
        "system_touchpoints",
        "success_metric",
        "risks",
        "mitigations",
        "owner",
        "eta",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Wrote Gemini journey simulation CSV: {out_csv}")


if __name__ == "__main__":
    main()


