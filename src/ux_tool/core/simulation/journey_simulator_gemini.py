from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import orjson

from ux_tool.adapters.gemini.client import GeminiClient
from ux_tool.io.validator import load_personas_from_dir
from ux_tool.types.persona import Persona


def _read_json(path: Path) -> Dict[str, Any]:
    return orjson.loads(path.read_bytes())


def _safe_clip(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _pick_persona(personas_dir: Optional[Path], persona_id: Optional[str]) -> Optional[Persona]:
    if not personas_dir:
        return None
    try:
        personas = load_personas_from_dir(personas_dir)
    except Exception:
        return None
    if persona_id:
        for p in personas:
            if p.id == persona_id:
                return p
    return personas[0] if personas else None


def _persona_block(persona: Optional[Persona]) -> str:
    if not persona:
        return ""
    traits = ", ".join([f"{k}:{v}" for k, v in (persona.traits or {}).items()])
    goals = ", ".join(persona.goals or [])
    pains = ", ".join(persona.pains or [])
    gender = getattr(persona, "gender", None) or ""
    return (
        f"id={persona.id}, name={persona.name}, age={persona.age}, gender={gender}, segment={persona.segment}, "
        f"background={persona.background or ''}, occupation={persona.occupation or ''}, location={persona.location or ''}, "
        f"traits=[{traits}], goals=[{goals}], pains=[{pains}]"
    )


def _read_transcript_lines(transcript_path: Path, max_chars: int) -> str:
    data = _read_json(transcript_path)
    lines: List[str] = []
    for u in data.get("utterances", []):
        turn = u.get("turn")
        speaker = u.get("speaker")
        text = (u.get("text") or "").replace("\n", " ").strip()
        lines.append(f"{turn}. {speaker}: {text}")
        if sum(len(x) + 1 for x in lines) > max_chars:
            break
    return _safe_clip("\n".join(lines), max_chars)


def _collect_context_blocks(
    fgi_session_dir: Optional[Path], ind_session_dir: Optional[Path], persona_id: Optional[str], max_chars_each: int
) -> List[Tuple[str, str]]:
    blocks: List[Tuple[str, str]] = []
    if fgi_session_dir and fgi_session_dir.exists():
        fgi_tr = fgi_session_dir.joinpath("transcript.json")
        if fgi_tr.exists():
            blocks.append(("FGI", _read_transcript_lines(fgi_tr, max_chars_each)))
    if ind_session_dir and ind_session_dir.exists():
        if persona_id:
            t = ind_session_dir.joinpath(persona_id, "transcript.json")
            if t.exists():
                blocks.append((f"IND[{persona_id}]", _read_transcript_lines(t, max_chars_each)))
        else:
            for d in ind_session_dir.iterdir():
                if d.is_dir():
                    t = d.joinpath("transcript.json")
                    if t.exists():
                        blocks.append((f"IND[{d.name}]", _read_transcript_lines(t, max_chars_each)))
    return blocks


def _build_prompt(goal: str, persona: Optional[Persona], blocks: List[Tuple[str, str]]) -> str:
    persona_txt = _persona_block(persona)
    ctx_parts = []
    for title, content in blocks:
        ctx_parts.append(f"[{title}]\n{content}")
    ctx = "\n\n".join(ctx_parts) if ctx_parts else "(no prior transcripts)"
    return (
        "다음 정보를 바탕으로 해당 페르소나의 목표를 달성하기 위한 실제 UX 유저 저니 단계를 추론해 주세요.\n"
        "조건:\n"
        "- 단계 수 세세하게 추론하세요. 제한 없이, '목표 달성'에 도달하면 종료하세요.\n"
        "- 각 단계는 아래 필드를 모두 포함해야 합니다:\n"
        "  step, stage, action_label, rationale, expected_outcome,\n"
        "  subtasks(array, 2~6개), inputs(array|string), outputs(array|string),\n"
        "  system_touchpoints(array), success_metric(string), risks(array), mitigations(array),\n"
        "  owner(string; user/system/moderator 등 역할), eta(string; 예: '~10분')\n"
        "- 마지막 단계의 expected_outcome에는 목표 달성임을 명시하세요.\n"
        "- JSON 배열로만 출력하세요. 설명/서론/코드블록 금지.\n\n"
        f"Persona: {persona_txt}\n"
        f"Goal: {goal}\n\n"
        f"Reference transcripts:\n{ctx}\n\n"
        "JSON 스키마 예시:\n"
        '[{"step":1,"stage":"Intent Clarification","action_label":"니즈 구체화","rationale":"...",'
        '"expected_outcome":"...","subtasks":["요구조건 나열","우선순위 정리"],'
        '"inputs":["예산","카테고리"],"outputs":["필수조건 리스트"],'
        '"system_touchpoints":["검색바","필터"],"success_metric":"필수조건 3개 이상 정의",'
        '"risks":["조건 과다로 탐색지연"],"mitigations":["최대 3개로 제한"],"owner":"user","eta":"~5분"}]'
    )


def _extract_json_array(text: str) -> Any:
    try:
        return orjson.loads(text)
    except Exception:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            return orjson.loads(snippet)
        raise


def simulate_with_gemini(
    client: GeminiClient,
    goal: str,
    personas_dir: Optional[Path],
    persona_id: Optional[str],
    fgi_session_dir: Optional[Path],
    ind_session_dir: Optional[Path],
    max_chars_each: int = 2000,
) -> List[Dict[str, Any]]:
    persona = _pick_persona(personas_dir, persona_id)
    blocks = _collect_context_blocks(fgi_session_dir, ind_session_dir, persona_id, max_chars_each=max_chars_each)
    prompt = _build_prompt(goal, persona, blocks)
    resp = client.generate(prompt)
    parsed = _extract_json_array(resp)
    rows: List[Dict[str, Any]] = []
    for idx, it in enumerate(parsed, start=1):
        def _join(value: Any) -> str:
            if value is None:
                return ""
            if isinstance(value, list):
                return "; ".join([str(x) for x in value])
            return str(value)
        rows.append(
            {
                "goal": goal,
                "persona_id": persona.id if persona else "",
                "persona_name": persona.name if persona else "",
                "step": it.get("step") or idx,
                "stage": it.get("stage") or "",
                "action_label": it.get("action_label") or "",
                "rationale": it.get("rationale") or "",
                "expected_outcome": it.get("expected_outcome") or "",
                "subtasks": _join(it.get("subtasks")),
                "inputs": _join(it.get("inputs")),
                "outputs": _join(it.get("outputs")),
                "system_touchpoints": _join(it.get("system_touchpoints")),
                "success_metric": it.get("success_metric") or "",
                "risks": _join(it.get("risks")),
                "mitigations": _join(it.get("mitigations")),
                "owner": it.get("owner") or "",
                "eta": it.get("eta") or "",
            }
        )
    return rows


