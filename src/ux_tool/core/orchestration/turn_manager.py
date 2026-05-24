from __future__ import annotations

from typing import List

from ux_tool.adapters.gemini.client import GeminiClient
from ux_tool.core.memory.session_memory import SessionMemory
from ux_tool.core.orchestration.transcript import Transcript, Utterance
from ux_tool.core.prompt.prompt_builder import build_moderator_prompt, build_persona_prompt
from ux_tool.types.persona import Persona
from ux_tool.types.questionnaire import Questionnaire
from ux_tool.types.scenario import Scenario


class TurnManager:
    def __init__(
        self,
        client: GeminiClient,
        personas: List[Persona],
        questionnaire: Questionnaire,
        scenario: Scenario,
    ) -> None:
        self.client = client
        self.personas = personas
        self.questionnaire = questionnaire
        self.scenario = scenario
        self.memory = SessionMemory(max_turns=40)
        self.transcript = Transcript()

    def run(self, max_rounds: int = 3) -> Transcript:
        turn = 0
        questions = self.questionnaire.questions[:max_rounds]
        print(f"[Turn] Start run: {len(questions)} questions, {len(self.personas)} personas")
        for q in questions:
            # Moderator prompt (direct to a participant implicitly)
            mod_prompt = build_moderator_prompt(self.scenario, q, self.memory.tail())
            mod_text = self.client.generate(mod_prompt)
            turn += 1
            self.transcript.add(Utterance(turn=turn, speaker="Moderator", text=mod_text))
            self.memory.add("Moderator", mod_text)
            print(f"[Turn] Q[{q.id}] Moderator spoke ({len(mod_text)} chars)")

            # Each persona answers
            for p in self.personas:
                p_prompt = build_persona_prompt(p, self.scenario, q, self.memory.tail())
                p_text = self.client.generate(p_prompt)
                turn += 1
                self.transcript.add(Utterance(turn=turn, speaker=p.name, text=p_text))
                self.memory.add(p.name, p_text)
                print(f"[Turn] Q[{q.id}] {p.name} answered ({len(p_text)} chars)")

        return self.transcript


