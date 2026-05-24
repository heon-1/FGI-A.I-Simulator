from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich import print

from ux_tool.core.aggregation.journey_map import generate_journey_map_csv
from ux_tool.adapters.gemini.client import GeminiClient
from ux_tool.config.gemini_config import load_gemini_settings
from ux_tool.core.simulation.journey_simulator_gemini import simulate_with_gemini
from ux_tool.io.validator import load_personas_from_dir


app = typer.Typer(add_completion=False, help="Journey map utilities (FGI/Individual).")


@app.command(help="Build a journey map CSV from a session's transcript(s).")
def map(
    session: Path = typer.Option(..., "--session", help="Session directory under outputs/<mode>/<session_id>"),
    out: Path = typer.Option(..., "--out", help="Output CSV path"),
    q: Optional[Path] = typer.Option(None, "--q", help="Questionnaire path (optional; defaults per mode)"),
) -> None:
    print(f"[CLI] Journey map: session={session}, out={out}, q={q}")
    result = generate_journey_map_csv(session, out, questionnaire_path=q)
    print(f"[green]Wrote journey map CSV[/green]: {result}")


@app.command(help="Simulate a persona's journey to a goal using Gemini.")
def simulate(
    goal: str = typer.Option(..., "--goal", help="Goal statement"),
    personas: Path = typer.Option(Path("data/personas"), "--personas", help="Personas directory"),
    persona_id: Optional[str] = typer.Option(None, "--persona-id", help="Target persona id"),
    all_personas: bool = typer.Option(False, "--all-personas", help="Run for every persona"),
    fgi_session: Optional[Path] = typer.Option(None, "--fgi-session", help="FGI session dir (optional)"),
    ind_session: Optional[Path] = typer.Option(None, "--ind-session", help="Individual session dir (optional)"),
    out: Optional[Path] = typer.Option(None, "--out", help="Output CSV (single persona mode)"),
    out_dir: Optional[Path] = typer.Option(None, "--out-dir", help="Output directory (all-personas mode)"),
    ctx_chars: int = typer.Option(2000, "--ctx-chars", help="Max chars per transcript block"),
) -> None:
    gcfg = load_gemini_settings()
    client = GeminiClient(gcfg)

    if all_personas:
        if not personas.exists():
            raise typer.BadParameter(f"--personas not found: {personas}")
        if not out_dir:
            raise typer.BadParameter("--out-dir is required with --all-personas")
        out_dir.mkdir(parents=True, exist_ok=True)
        plist = load_personas_from_dir(personas)
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
        for p in plist:
            rows = simulate_with_gemini(
                client=client,
                goal=goal,
                personas_dir=personas,
                persona_id=p.id,
                fgi_session_dir=fgi_session,
                ind_session_dir=ind_session,
                max_chars_each=ctx_chars,
            )
            target = out_dir.joinpath(f"journey_{p.id}.csv")
            target.parent.mkdir(parents=True, exist_ok=True)
            import csv

            with target.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"[green]Wrote[/green]: {target}")
        return

    # single persona
    if not persona_id:
        raise typer.BadParameter("Provide --persona-id or use --all-personas")
    if not out:
        raise typer.BadParameter("--out is required for single persona")
    rows = simulate_with_gemini(
        client=client,
        goal=goal,
        personas_dir=personas,
        persona_id=persona_id,
        fgi_session_dir=fgi_session,
        ind_session_dir=ind_session,
        max_chars_each=ctx_chars,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    import csv

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
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[green]Wrote[/green]: {out}")


if __name__ == "__main__":
    app()


