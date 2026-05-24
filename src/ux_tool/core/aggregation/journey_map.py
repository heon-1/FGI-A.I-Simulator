from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple, Any, Iterable, Optional
import csv

import orjson


Stage = str


def _read_json(path: Path) -> Dict[str, Any]:
    return orjson.loads(path.read_bytes())


def _build_stage_map_for_individual(q_path: Path) -> Dict[str, Tuple[str, Stage]]:
    """
    Returns: map of question_text -> (question_id, stage)
    Stages are coarse-grained journey phases aligned to current service:
      - Profile & Entry
      - Pre-search Research
      - Query Intent & Initial Search
      - Evaluation & Narrowing
      - Relevance & Quality
      - Satisfaction & Outcome
      - Decision Criteria
      - Failure & Retention
    """
    q = _read_json(q_path)
    items = q.get("questions", [])
    id_to_text: Dict[str, str] = {it["id"]: it["text"] for it in items}
    stage_by_id: Dict[str, Stage] = {}

    def set_stage(ids: Iterable[str], stage: Stage) -> None:
        for i in ids:
            stage_by_id[i] = stage

    set_stage(["q1", "q2", "q3", "q4", "q8", "q9"], "Profile & Entry")
    set_stage(["q10", "q11", "q12", "q13", "q14", "q15"], "Pre-search Research")
    set_stage(["q16", "q17", "q18", "q19", "q20", "q21", "q22"], "Query Intent & Initial Search")
    set_stage(["q23", "q24", "q25", "q26", "q27", "q28", "q29", "q30"], "Evaluation & Narrowing")
    set_stage(["q31", "q32", "q33", "q34", "q37"], "Relevance & Quality")
    set_stage(["q35", "q36", "q44"], "Satisfaction & Outcome")
    set_stage(["q38", "q39", "q40", "q41", "q42", "q43"], "Decision Criteria")
    set_stage(["q45", "q46"], "Failure & Retention")

    text_to_stage: Dict[str, Tuple[str, Stage]] = {}
    for qid, text in id_to_text.items():
        text_to_stage[text] = (qid, stage_by_id.get(qid, "Other"))
    return text_to_stage


def _build_stage_map_for_fgi(q_path: Path) -> Dict[str, Tuple[str, Stage]]:
    """
    Returns: map of question_text -> (question_id, stage)
    Stages tailored to FGI prompts:
      - Warmup & Awareness
      - Exploration Methods
      - Trust & Signals
      - Recommendations
      - Distrust & Workarounds
      - Decision Triggers
      - Personalization Needs
      - Improvements
    """
    q = _read_json(q_path)
    items = q.get("questions", [])
    id_to_text: Dict[str, str] = {it["id"]: it["text"] for it in items}
    stage_by_id: Dict[str, Stage] = {}

    def set_stage(ids: Iterable[str], stage: Stage) -> None:
        for i in ids:
            stage_by_id[i] = stage

    set_stage(["q1"], "Warmup & Awareness")
    set_stage(["q2", "q6", "q7"], "Exploration Methods")
    set_stage(["q3"], "Trust & Signals")
    set_stage(["q4"], "Recommendations")
    set_stage(["q5"], "Distrust & Workarounds")
    set_stage(["q8"], "Decision Triggers")
    set_stage(["q9"], "Personalization Needs")
    set_stage(["q10"], "Improvements")

    text_to_stage: Dict[str, Tuple[str, Stage]] = {}
    for qid, text in id_to_text.items():
        text_to_stage[text] = (qid, stage_by_id.get(qid, "Other"))
    return text_to_stage


def _detect_mode_from_session(session_dir: Path) -> str:
    # Expect outputs/<mode>/<session_id>
    try:
        outputs_idx = session_dir.parts.index("outputs")
        mode = session_dir.parts[outputs_idx + 1]
        return mode
    except Exception:
        return ""


def _default_questionnaire_path(mode: str, cwd: Optional[Path] = None) -> Optional[Path]:
    base = cwd or Path.cwd()
    if mode == "individual":
        p = base.joinpath("data/questionnaires/individual.json")
        return p if p.exists() else None
    if mode == "fgi":
        p = base.joinpath("data/questionnaires/fgi.json")
        return p if p.exists() else None
    return None


def _iter_transcripts(session_dir: Path, mode: str) -> List[Tuple[Path, str]]:
    """
    Returns list of (transcript_path, persona_id) for Individual,
    or (transcript_path, '') for FGI.
    """
    if mode == "individual":
        paths: List[Tuple[Path, str]] = []
        for p in session_dir.iterdir():
            if p.is_dir():
                t = p.joinpath("transcript.json")
                if t.exists():
                    paths.append((t, p.name))
        return paths
    else:
        t = session_dir.joinpath("transcript.json")
        return [(t, "")] if t.exists() else []


def generate_journey_map_csv(session_dir: Path, out_csv: Path, questionnaire_path: Optional[Path] = None) -> Path:
    """
    Build a journey map table by aligning moderator questions to questionnaire stages.
    Columns:
      mode, session_id, persona_id, stage, question_id, question_text, turn, speaker, text
    """
    mode = _detect_mode_from_session(session_dir)
    if not mode:
        raise ValueError(f"Cannot detect mode from session path: {session_dir}")
    q_path = questionnaire_path or _default_questionnaire_path(mode)
    if not q_path or not q_path.exists():
        raise FileNotFoundError(f"Questionnaire not found. Provide --q or ensure default exists (mode={mode}).")

    stage_map = (
        _build_stage_map_for_individual(q_path)
        if mode == "individual"
        else _build_stage_map_for_fgi(q_path)
    )

    rows: List[Dict[str, Any]] = []
    # Parse session_id
    session_id = session_dir.name
    for t_path, persona_id in _iter_transcripts(session_dir, mode):
        tr = _read_json(t_path)
        for u in tr.get("utterances", []):
            turn = u.get("turn")
            speaker = u.get("speaker")
            text = u.get("text")
            question_id = ""
            stage = "Other"
            question_text = ""
            if speaker == "Moderator":
                question_text = text
                if question_text in stage_map:
                    question_id, stage = stage_map[question_text]
            rows.append(
                {
                    "mode": mode,
                    "session_id": session_id,
                    "persona_id": persona_id,
                    "stage": stage,
                    "question_id": question_id,
                    "question_text": question_text,
                    "turn": turn,
                    "speaker": speaker,
                    "text": text,
                }
            )

    # Sort for readability
    rows.sort(key=lambda r: (r["session_id"], r["persona_id"], r["turn"]))

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "mode",
        "session_id",
        "persona_id",
        "stage",
        "question_id",
        "question_text",
        "turn",
        "speaker",
        "text",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out_csv


