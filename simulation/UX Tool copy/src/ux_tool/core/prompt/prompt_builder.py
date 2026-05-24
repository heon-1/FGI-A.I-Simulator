from __future__ import annotations

from typing import List

from ux_tool.core.prompt.templates import MODERATOR_TEMPLATE, PERSONA_TEMPLATE, SYSTEM_TEMPLATE
from ux_tool.types.persona import Persona
from ux_tool.types.questionnaire import Question
from ux_tool.types.scenario import Scenario


def build_moderator_prompt(
    scenario: Scenario,
    question: Question,
    transcript_tail: List[str],
) -> str:
    conversation = "\n".join(transcript_tail[-6:])
    return (
        f"SYSTEM: {SYSTEM_TEMPLATE}\n"
        f"ROLE: {MODERATOR_TEMPLATE}\n\n"
        f"SCENARIO: {scenario.title}\n{scenario.description}\n"
        f"CONSTRAINTS: {', '.join(scenario.constraints)}\n\n"
        f"RECENT_CONVERSATION:\n{conversation}\n\n"
        f"QUESTION: {question.text}\n"
        f"Instruction: Ask this question to one participant, considering the flow."
    )


def build_persona_prompt(
    persona: Persona,
    scenario: Scenario,
    question: Question,
    transcript_tail: List[str],
) -> str:
    conversation = "\n".join(transcript_tail[-6:])
    persona_ctx = (
        f"Persona: {persona.display}\n"
        f"Background: {persona.background or '-'}\n"
        f"Occupation: {persona.occupation or '-'}\n"
        f"Location: {persona.location or '-'}\n"
        f"HouseholdSize: {persona.household_size or '-'}\n"
        f"IncomeMonthly: {persona.income_monthly or '-'}\n"
        f"SpendMonthly: {persona.spend_monthly or '-'}\n"
        f"SpendBreakdown: {persona.spend_breakdown or {}}\n"
        f"Traits: {persona.traits}\n"
        f"Goals: {persona.goals}\n"
        f"Pains: {persona.pains}\n"
    )
    return (
        f"SYSTEM: {SYSTEM_TEMPLATE}\nROLE: {PERSONA_TEMPLATE}\n\n"
        f"{persona_ctx}\n"
        f"SCENARIO: {scenario.title}\n{scenario.description}\n\n"
        f"RECENT_CONVERSATION:\n{conversation}\n\n"
        f"QUESTION: {question.text}\n"
        f"Instruction: Answer strictly as the persona. Keep under 120 words."
    )


