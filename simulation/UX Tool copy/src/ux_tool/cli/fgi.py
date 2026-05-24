from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from ux_tool.adapters.gemini.client import GeminiClient
from ux_tool.config.app_config import load_app_config
from ux_tool.config.gemini_config import load_gemini_settings
from ux_tool.modes.fgi.run_fgi import run_fgi
from ux_tool.io.csv_export import merge_transcripts_to_csv


app = typer.Typer(add_completion=False)


@app.command()
def main(
    q: Path = typer.Option(..., "--q", help="Questionnaire JSON path"),
    p: Path = typer.Option(..., "--p", help="Personas directory"),
    s: Path = typer.Option(..., "--s", help="Scenario JSON path"),
    max_rounds: int = typer.Option(3, help="Max rounds (questions) to run"),
    ind_ctx: Path = typer.Option(None, "--ind_ctx", help="Aggregate.json from Individual session"),
    auto_csv: bool = typer.Option(True, "--auto-csv/--no-auto-csv", help="Export merged CSV after completion"),
):
    print(f"[CLI] FGI start: q={q}, p={p}, s={s}, max_rounds={max_rounds}, ind_ctx={ind_ctx}")
    cfg = load_app_config()
    gcfg = load_gemini_settings()
    client = GeminiClient(gcfg)
    session_dir = run_fgi(cfg, client, q, p, s, max_rounds=max_rounds, individual_context_path=ind_ctx)
    print(f"[green]FGI session completed[/green]: {session_dir}")
    if auto_csv:
        session_path = Path(session_dir)
        transcript_paths = list(session_path.rglob("transcript.json"))
        if transcript_paths:
            out_csv = session_path.joinpath("merged_transcript.csv")
            merge_transcripts_to_csv(transcript_paths, out_csv)
            print(f"[green]Exported CSV[/green]: {out_csv}")


if __name__ == "__main__":
    app()


