from __future__ import annotations

from pathlib import Path

from ux_tool.adapters.gemini.client import GeminiClient
from ux_tool.config.app_config import AppConfig
from ux_tool.core.evaluation.summarizer import summarize_transcript
from ux_tool.core.evaluation.tagger import tag_transcript
from ux_tool.core.memory.session_memory import SessionMemory
from ux_tool.core.orchestration.transcript import Transcript, Utterance
from ux_tool.io.file_store import create_session_dir, write_json, write_text
from ux_tool.io.validator import load_personas_from_dir, load_questionnaire, load_scenario
from collections import Counter
from datetime import datetime


def run_individual(
    app: AppConfig,
    client: GeminiClient,
    questionnaire_path: Path,
    personas_dir: Path,
    scenario_path: Path,
    max_rounds: int | None = None,
) -> Path:
    print(f"[Individual] Loading questionnaire: {questionnaire_path}")
    questionnaire = load_questionnaire(questionnaire_path)
    print(f"[Individual] Loading personas from: {personas_dir}")
    personas = load_personas_from_dir(personas_dir)
    print(f"[Individual] Loading scenario: {scenario_path}")
    scenario = load_scenario(scenario_path)

    session_dir = create_session_dir("individual", app.output_dir)
    print(f"[Individual] Session started: {session_dir}")

    aggregate = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "scenario_id": scenario.id,
        "questionnaire_id": questionnaire.id,
        "personas": []
    }
    all_keywords = Counter()

    for persona in personas:
        print(f"[Individual] Persona start: {persona.id} - {persona.name}")
        memory = SessionMemory(max_turns=40)
        transcript = Transcript()
        turn = 0
        questions = questionnaire.questions
        if max_rounds is not None:
            questions = questions[: max_rounds]
        for q in questions:
            # Question as moderator line
            print(f"[Individual] Q: {q.id} -> {q.text[:60]}...")
            turn += 1
            transcript.add(Utterance(turn=turn, speaker="Moderator", text=q.text))
            memory.add("Moderator", q.text)
            # Persona answer
            answer = client.generate(
                f"Answer as persona {persona.name}: {q.text}\n Context: {scenario.title} - {scenario.description}"
            )
            print(f"[Individual] A[{persona.name}] len={len(answer)}")
            turn += 1
            transcript.add(Utterance(turn=turn, speaker=persona.name, text=answer))
            memory.add(persona.name, answer)

        # Save per-persona outputs
        person_dir = session_dir.joinpath(persona.id)
        write_json(person_dir.joinpath("transcript.json"), transcript.to_dict())
        write_text(person_dir.joinpath("transcript.txt"), "\n".join(transcript.as_lines()))
        lines = transcript.as_lines()
        tags = tag_transcript(lines)
        summary_text = summarize_transcript(client, lines)
        write_json(person_dir.joinpath("tags.json"), tags)
        write_text(person_dir.joinpath("summary.txt"), summary_text)
        print(f"[Individual] Saved outputs for {persona.id}")

        # Aggregate
        keywords = tags.get("keywords", [])
        all_keywords.update(keywords)
        aggregate["personas"].append({
            "id": persona.id,
            "name": persona.name,
            "keywords": keywords,
            "summary": summary_text
        })

    aggregate["all_keywords_top"] = [w for w, _ in all_keywords.most_common(20)]
    write_json(session_dir.joinpath("aggregate.json"), aggregate)
    print(f"[Individual] Aggregate saved: {session_dir / 'aggregate.json'}")
    return session_dir


