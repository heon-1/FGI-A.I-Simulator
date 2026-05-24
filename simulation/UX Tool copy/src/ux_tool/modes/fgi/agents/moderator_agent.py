from __future__ import annotations

from ux_tool.adapters.gemini.client import GeminiClient
from ux_tool.core.prompt.prompt_builder import build_moderator_prompt
from ux_tool.types.questionnaire import Question
from ux_tool.types.scenario import Scenario


class ModeratorAgent:
    def __init__(self, client: GeminiClient) -> None:
        self.client = client

    def speak(self, scenario: Scenario, question: Question, transcript_tail: list[str]) -> str:
        prompt = build_moderator_prompt(scenario, question, transcript_tail)
        return self.client.generate(prompt)


