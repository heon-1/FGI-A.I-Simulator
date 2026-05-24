from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from ux_tool.adapters.gemini.client import GeminiClient
from ux_tool.config.app_config import load_app_config
from ux_tool.config.gemini_config import load_gemini_settings
from ux_tool.modes.individual.run_individual import run_individual
from ux_tool.io.csv_export import merge_transcripts_to_csv


app = typer.Typer(add_completion=False)


@app.command()
def main(
    q: Path = typer.Option(..., "--q", help="Questionnaire JSON path"),
    p: Path = typer.Option(..., "--p", help="Personas directory"),
    s: Path = typer.Option(..., "--s", help="Scenario JSON path"),
    max_rounds: int = typer.Option(None, help="Max rounds (optional)"),
    auto_csv: bool = typer.Option(True, "--auto-csv/--no-auto-csv", help="Export merged CSV after completion"),
):
    print(f"[CLI] Individual start: q={q}, p={p}, s={s}, max_rounds={max_rounds}")
    cfg = load_app_config()
    gcfg = load_gemini_settings()
    client = GeminiClient(gcfg)
    session_dir = run_individual(cfg, client, q, p, s, max_rounds=max_rounds)
    print(f"[green]Individual sessions completed[/green]: {session_dir}")
    if auto_csv:
        session_path = Path(session_dir)
        transcript_paths = list(session_path.rglob("transcript.json"))
        if transcript_paths:
            out_csv = session_path.joinpath("merged_transcripts.csv")
            merge_transcripts_to_csv(transcript_paths, out_csv)
            print(f"[green]Exported CSV[/green]: {out_csv}")


if __name__ == "__main__":
    app()


