from __future__ import annotations

from ux_tool.adapters.gemini.client import GeminiClient
from ux_tool.core.prompt.prompt_builder import build_persona_prompt
from ux_tool.types.persona import Persona
from ux_tool.types.questionnaire import Question
from ux_tool.types.scenario import Scenario


class RespondentAgent:
    def __init__(self, client: GeminiClient, persona: Persona) -> None:
        self.client = client
        self.persona = persona

    def answer(self, scenario: Scenario, question: Question, transcript_tail: list[str]) -> str:
        prompt = build_persona_prompt(self.persona, scenario, question, transcript_tail)
        return self.client.generate(prompt)


