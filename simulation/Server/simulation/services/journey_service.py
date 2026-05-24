"""
Journey Map Simulation Service
"""
from typing import List, Optional, Dict, Any, Generator
import orjson
from simulation.types import Persona, JourneyStep, JourneyMap, Transcript
from simulation.services.gemini_client import get_gemini_client


class JourneyMapService:
    """
    Service for simulating and generating user journey maps.
    Uses AI to predict user journey based on persona and research context.
    """

    def __init__(self):
        self.client = get_gemini_client()

    def build_journey_prompt(
        self,
        goal: str,
        persona: Persona,
        context_blocks: List[tuple[str, str]] = None
    ) -> str:
        """Build prompt for journey map generation"""
        persona_block = self._persona_block(persona)
        
        ctx_parts = []
        if context_blocks:
            for title, content in context_blocks:
                ctx_parts.append(f"[{title}]\n{content}")
        ctx = "\n\n".join(ctx_parts) if ctx_parts else "(참고 자료 없음)"
        
        return f"""다음 정보를 바탕으로 해당 페르소나의 목표를 달성하기 위한 실제 UX 유저 저니 단계를 추론해 주세요.

조건:
- 단계 수를 세세하게 추론하세요. 제한 없이, '목표 달성'에 도달하면 종료하세요.
- 각 단계는 아래 필드를 모두 포함해야 합니다:
  step, stage, action_label, rationale, expected_outcome,
  subtasks(array, 2~6개), inputs(array|string), outputs(array|string),
  system_touchpoints(array), success_metric(string), risks(array), mitigations(array),
  owner(string; user/system/moderator 등 역할), eta(string; 예: '~10분')
- 마지막 단계의 expected_outcome에는 목표 달성임을 명시하세요.
- JSON 배열로만 출력하세요. 설명/서론/코드블록 금지.

Persona: {persona_block}
Goal: {goal}

Reference transcripts:
{ctx}

JSON 스키마 예시:
[{{"step":1,"stage":"Intent Clarification","action_label":"니즈 구체화","rationale":"...","expected_outcome":"...","subtasks":["요구조건 나열","우선순위 정리"],"inputs":["예산","카테고리"],"outputs":["필수조건 리스트"],"system_touchpoints":["검색바","필터"],"success_metric":"필수조건 3개 이상 정의","risks":["조건 과다로 탐색지연"],"mitigations":["최대 3개로 제한"],"owner":"user","eta":"~5분"}}]"""

    def simulate_journey(
        self,
        goal: str,
        persona: Persona,
        fgi_transcript: Optional[Transcript] = None,
        individual_transcript: Optional[Transcript] = None,
        max_context_chars: int = 2000
    ) -> JourneyMap:
        """
        Generate a journey map for a persona achieving a goal.
        
        Args:
            goal: The goal the user wants to achieve
            persona: The persona for the journey
            fgi_transcript: Optional FGI transcript for context
            individual_transcript: Optional individual interview transcript
            max_context_chars: Max characters for context blocks
            
        Returns:
            Complete journey map
        """
        # Build context blocks from transcripts
        context_blocks = []
        
        if fgi_transcript:
            lines = fgi_transcript.as_lines()
            content = self._clip_text("\n".join(lines), max_context_chars)
            context_blocks.append(("FGI", content))
        
        if individual_transcript:
            lines = individual_transcript.as_lines()
            content = self._clip_text("\n".join(lines), max_context_chars)
            context_blocks.append((f"Individual[{persona.id}]", content))
        
        prompt = self.build_journey_prompt(goal, persona, context_blocks)
        response = self.client.generate(prompt)
        
        # Parse response
        steps = self._parse_journey_response(response)
        
        return JourneyMap(
            goal=goal,
            persona_id=persona.id,
            persona_name=persona.name,
            steps=steps
        )

    def simulate_journey_stream(
        self,
        goal: str,
        persona: Persona,
        fgi_transcript: Optional[Transcript] = None,
        individual_transcript: Optional[Transcript] = None,
        max_context_chars: int = 2000
    ) -> Generator[dict, None, None]:
        """
        Generate journey map with streaming.
        
        Yields:
            Dict with type and data for progress updates
        """
        context_blocks = []
        
        if fgi_transcript:
            lines = fgi_transcript.as_lines()
            content = self._clip_text("\n".join(lines), max_context_chars)
            context_blocks.append(("FGI", content))
        
        if individual_transcript:
            lines = individual_transcript.as_lines()
            content = self._clip_text("\n".join(lines), max_context_chars)
            context_blocks.append((f"Individual[{persona.id}]", content))
        
        prompt = self.build_journey_prompt(goal, persona, context_blocks)
        
        yield {
            "type": "start",
            "persona_id": persona.id,
            "goal": goal
        }
        
        full_response = ""
        for chunk in self.client.generate_stream(prompt):
            full_response += chunk
            yield {"type": "chunk", "chunk": chunk}
        
        # Parse completed response
        steps = self._parse_journey_response(full_response)
        
        journey_map = JourneyMap(
            goal=goal,
            persona_id=persona.id,
            persona_name=persona.name,
            steps=steps
        )
        
        yield {
            "type": "complete",
            "journey_map": journey_map.model_dump()
        }

    def journey_to_csv_rows(self, journey: JourneyMap) -> List[Dict[str, Any]]:
        """Convert journey map to CSV-friendly row format"""
        rows = []
        for step in journey.steps:
            rows.append({
                "goal": journey.goal,
                "persona_id": journey.persona_id,
                "persona_name": journey.persona_name,
                "step": step.step,
                "stage": step.stage,
                "action_label": step.action_label,
                "rationale": step.rationale,
                "expected_outcome": step.expected_outcome,
                "subtasks": "; ".join(step.subtasks),
                "inputs": "; ".join(step.inputs) if isinstance(step.inputs, list) else str(step.inputs),
                "outputs": "; ".join(step.outputs) if isinstance(step.outputs, list) else str(step.outputs),
                "system_touchpoints": "; ".join(step.system_touchpoints),
                "success_metric": step.success_metric,
                "risks": "; ".join(step.risks),
                "mitigations": "; ".join(step.mitigations),
                "owner": step.owner,
                "eta": step.eta,
            })
        return rows

    def _parse_journey_response(self, response: str) -> List[JourneyStep]:
        """Parse AI response into journey steps"""
        try:
            parsed = orjson.loads(response)
        except Exception:
            # Try to extract JSON array from response
            start = response.find("[")
            end = response.rfind("]")
            if start != -1 and end != -1 and end > start:
                snippet = response[start:end + 1]
                parsed = orjson.loads(snippet)
            else:
                return []
        
        steps = []
        for idx, item in enumerate(parsed, start=1):
            def _to_list(value) -> List[str]:
                if value is None:
                    return []
                if isinstance(value, list):
                    return [str(x) for x in value]
                return [str(value)]
            
            steps.append(JourneyStep(
                step=item.get("step") or idx,
                stage=item.get("stage") or "",
                action_label=item.get("action_label") or "",
                rationale=item.get("rationale") or "",
                expected_outcome=item.get("expected_outcome") or "",
                subtasks=_to_list(item.get("subtasks")),
                inputs=_to_list(item.get("inputs")),
                outputs=_to_list(item.get("outputs")),
                system_touchpoints=_to_list(item.get("system_touchpoints")),
                success_metric=item.get("success_metric") or "",
                risks=_to_list(item.get("risks")),
                mitigations=_to_list(item.get("mitigations")),
                owner=item.get("owner") or "",
                eta=item.get("eta") or "",
            ))
        
        return steps

    def _persona_block(self, persona: Persona) -> str:
        """Convert persona to prompt text block"""
        traits = ", ".join([f"{k}:{v}" for k, v in (persona.traits or {}).items()])
        goals = ", ".join(persona.goals or [])
        pains = ", ".join(persona.pains or [])
        
        return (
            f"id={persona.id}, name={persona.name}, age={persona.age}, "
            f"gender={persona.gender}, segment={persona.segment}, "
            f"background={persona.background or ''}, occupation={persona.occupation or ''}, "
            f"location={persona.location or ''}, traits=[{traits}], goals=[{goals}], pains=[{pains}]"
        )

    def _clip_text(self, text: str, max_len: int) -> str:
        """Clip text to max length"""
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."
