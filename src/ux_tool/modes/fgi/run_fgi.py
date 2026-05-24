from __future__ import annotations

from pathlib import Path

from ux_tool.adapters.gemini.client import GeminiClient
from ux_tool.config.app_config import AppConfig
from ux_tool.core.evaluation.summarizer import summarize_transcript
from ux_tool.core.evaluation.tagger import tag_transcript
from ux_tool.core.orchestration.turn_manager import TurnManager
from ux_tool.io.file_store import create_session_dir, write_json, write_text
from ux_tool.io.validator import load_personas_from_dir, load_questionnaire, load_scenario
from ux_tool.core.aggregation.individual_context import load_individual_context, format_insight_lines


def run_fgi(
    app: AppConfig,
    client: GeminiClient,
    questionnaire_path: Path,
    personas_dir: Path,
    scenario_path: Path,
    max_rounds: int = 3,
    individual_context_path: Path | None = None,
) -> Path:
    print(f"[FGI] Loading questionnaire: {questionnaire_path}")
    questionnaire = load_questionnaire(questionnaire_path)
    print(f"[FGI] Loading personas from: {personas_dir}")
    personas = load_personas_from_dir(personas_dir)
    print(f"[FGI] Loading scenario: {scenario_path}")
    scenario = load_scenario(scenario_path)

    session_dir = create_session_dir("fgi", app.output_dir)
    print(f"[FGI] Session started: {session_dir}")
    manager = TurnManager(client=client, personas=personas, questionnaire=questionnaire, scenario=scenario)

    # Seed memory with insights from Individual runs if provided
    if individual_context_path is not None and individual_context_path.exists():
        ctx = load_individual_context(individual_context_path)
        lines = format_insight_lines(ctx)
        for line in lines:
            manager.memory.add("Insight", line)
        print(f"[FGI] Seeded memory from Individual context: {len(lines)} lines")
    else:
        if individual_context_path is not None:
            print(f"[FGI] Individual context not found: {individual_context_path}")
    print(f"[FGI] Running turns for {len(questionnaire.questions[:max_rounds])} rounds ...")
    transcript = manager.run(max_rounds=max_rounds)
    print(f"[FGI] Turns completed. Saving outputs ...")

    # Save transcript
    write_json(session_dir.joinpath("transcript.json"), transcript.to_dict())
    write_text(session_dir.joinpath("transcript.txt"), "\n".join(transcript.as_lines()))

    # Evaluate
    lines = transcript.as_lines()
    tags = tag_transcript(lines)
    write_json(session_dir.joinpath("tags.json"), tags)
    summary = summarize_transcript(client, lines)
    write_text(session_dir.joinpath("summary.txt"), summary)

    return session_dir


