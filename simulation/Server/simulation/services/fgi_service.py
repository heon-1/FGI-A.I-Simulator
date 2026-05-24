"""
Focus Group Interview (FGI) Simulation Service
"""
from typing import List, Generator, Optional
import random
import orjson
from simulation.types import Persona, Questionnaire, Question, Transcript, Scenario
from simulation.services.gemini_client import get_gemini_client


class FGIService:
    """
    Service for running Focus Group Interview simulations.
    Multiple personas interact with a moderator and each other.
    """

    def __init__(self):
        self.client = get_gemini_client()

    def build_moderator_prompt(
        self,
        questionnaire: Questionnaire,
        question: Question,
        scenario: Optional[Scenario],
        previous_context: str = ""
    ) -> str:
        """Build prompt for moderator's question introduction"""
        from simulation.services.templates import (
            SYSTEM_TEMPLATE, MODERATOR_TEMPLATE, FGI_MODERATOR_PROMPT
        )
        
        scenario_title = scenario.title if scenario else "FGI Session"
        scenario_desc = scenario.description if scenario else ""
        constraints = ", ".join(scenario.constraints) if scenario and hasattr(scenario, 'constraints') else "None"
        
        # Format previous context
        conversation = previous_context if previous_context else "(No prior conversation)"
        
        return FGI_MODERATOR_PROMPT.format(
            system=SYSTEM_TEMPLATE,
            moderator_role=MODERATOR_TEMPLATE,
            scenario_title=scenario_title,
            scenario_description=scenario_desc,
            constraints=constraints,
            conversation=conversation,
            question_text=question.text
        )

    def build_persona_response_prompt(
        self,
        persona: Persona,
        question: Question,
        moderator_intro: str,
        other_responses: List[tuple[str, str]] = None,
        scenario: Optional[Scenario] = None
    ) -> str:
        """Build prompt for persona response in FGI context"""
        from simulation.services.templates import (
            SYSTEM_TEMPLATE, PERSONA_TEMPLATE, PERSONA_RESPONSE_PROMPT,
            SCALE_INSTRUCTION, MULTI_INSTRUCTION, OPEN_INSTRUCTION
        )
        
        # Build context from other participants' responses
        others_context = ""
        if other_responses:
            others_lines = [f"{name}: {resp}" for name, resp in other_responses[-3:]]
            others_context = "\nOther Participants:\n" + "\n".join(others_lines) + "\n"
        
        # Combine moderator intro and others as conversation context
        conversation = f"Moderator: {moderator_intro}\n{others_context}"

        scenario_title = scenario.title if scenario else "FGI Session"
        scenario_desc = scenario.description if scenario else ""
        
        # Determine instruction based on question kind
        if question.kind == "scale":
            kind_instruction = SCALE_INSTRUCTION.format(scale_max=question.scale_max)
        elif question.kind == "multi":
            options_str = ", ".join(question.options)
            kind_instruction = MULTI_INSTRUCTION.format(options=options_str)
        else:
            kind_instruction = OPEN_INSTRUCTION

        # Persona Details
        traits_str = ", ".join([f"{k}:{v}" for k, v in (persona.traits or {}).items()])
        goals_str = ", ".join(persona.goals or [])
        pains_str = ", ".join(persona.pains or [])
        spend_breakdown_str = str(persona.spend_breakdown or {})

        return PERSONA_RESPONSE_PROMPT.format(
            system=SYSTEM_TEMPLATE,
            persona_role=PERSONA_TEMPLATE,
            persona_display=f"{persona.name} ({persona.age}, {persona.gender}, {persona.occupation})",
            background=persona.background or "",
            occupation=persona.occupation or "",
            location=persona.location or "",
            household_size=persona.household_size,
            income_monthly=persona.income_monthly,
            spend_monthly=persona.spend_monthly,
            spend_breakdown=spend_breakdown_str,
            traits=traits_str,
            goals=goals_str,
            pains=pains_str,
            scenario_title=scenario_title,
            scenario_description=scenario_desc,
            conversation=conversation,
            question_text=f"{question.text}\n{kind_instruction}"
        )

    def run_fgi(
        self,
        personas: List[Persona],
        questionnaire: Questionnaire,
        scenario: Optional[Scenario] = None,
        max_rounds: int = 3
    ) -> Transcript:
        """
        Run a complete FGI simulation.
        
        Args:
            personas: List of personas participating
            questionnaire: The questionnaire to use
            scenario: Optional scenario context
            max_rounds: Maximum number of questions to process
            
        Returns:
            Complete FGI transcript
        """
        transcript = Transcript(
            session_id=f"fgi_{len(personas)}p",
            mode="fgi"
        )
        
        questions = questionnaire.questions[:max_rounds]
        previous_context = ""
        
        for q_idx, question in enumerate(questions):
            # Moderator introduces question
            mod_prompt = self.build_moderator_prompt(
                questionnaire, question, scenario, previous_context
            )
            moderator_intro = self.client.generate(mod_prompt)
            transcript.add("Moderator", moderator_intro)
            
            # Shuffle persona order for natural discussion
            shuffled_personas = personas.copy()
            random.shuffle(shuffled_personas)
            
            round_responses = []
            
            for persona in shuffled_personas:
                # Generate persona response
                response_prompt = self.build_persona_response_prompt(
                    persona, question, moderator_intro,
                    round_responses, scenario
                )
                response = self.client.generate(response_prompt)
                
                transcript.add(persona.name, response)
                round_responses.append((persona.name, response))
            
            # Build context for next round
            previous_context = f"이전 질문: {question.text}\n"
            previous_context += "\n".join([f"{name}: {resp[:100]}..." for name, resp in round_responses[-3:]])
        
        return transcript

    def run_fgi_stream(
        self,
        personas: List[Persona],
        questionnaire: Questionnaire,
        scenario: Optional[Scenario] = None,
        max_rounds: int = 3
    ) -> Generator[dict, None, None]:
        """
        Run FGI with streaming responses.
        
        Yields:
            Dict with type and data for each event
        """
        questions = questionnaire.questions[:max_rounds]
        previous_context = ""
        all_utterances = []
        
        for q_idx, question in enumerate(questions):
            # Moderator introduces question
            mod_prompt = self.build_moderator_prompt(
                questionnaire, question, scenario, previous_context
            )
            
            yield {"type": "moderator_start", "question_id": question.id}
            
            moderator_intro = ""
            for chunk in self.client.generate_stream(mod_prompt):
                moderator_intro += chunk
                yield {"type": "chunk", "speaker": "Moderator", "chunk": chunk}
            
            yield {
                "type": "utterance",
                "turn": len(all_utterances) + 1,
                "speaker": "Moderator",
                "text": moderator_intro
            }
            all_utterances.append({"speaker": "Moderator", "text": moderator_intro})
            
            # Shuffle persona order
            shuffled_personas = personas.copy()
            random.shuffle(shuffled_personas)
            
            round_responses = []
            
            for persona in shuffled_personas:
                response_prompt = self.build_persona_response_prompt(
                    persona, question, moderator_intro,
                    round_responses, scenario
                )
                
                yield {"type": "persona_start", "persona_id": persona.id, "name": persona.name}
                
                response = ""
                for chunk in self.client.generate_stream(response_prompt):
                    response += chunk
                    yield {"type": "chunk", "speaker": persona.name, "chunk": chunk}
                
                yield {
                    "type": "utterance",
                    "turn": len(all_utterances) + 1,
                    "speaker": persona.name,
                    "text": response
                }
                all_utterances.append({"speaker": persona.name, "text": response})
                round_responses.append((persona.name, response))
            
            # Update context for next round
            previous_context = f"이전 질문: {question.text}\n"
            previous_context += "\n".join([f"{name}: {resp[:100]}..." for name, resp in round_responses[-3:]])
            
            yield {"type": "round_complete", "round": q_idx + 1}
        
        yield {"type": "complete", "transcript": all_utterances}

    def _persona_block(self, persona: Persona) -> str:
        """Convert persona to prompt text block"""
        traits = ", ".join([f"{k}:{v}" for k, v in (persona.traits or {}).items()])
        goals = ", ".join(persona.goals or [])
        pains = ", ".join(persona.pains or [])
        
        return (
            f"이름={persona.name}, 나이={persona.age}, 성별={persona.gender}, "
            f"세그먼트={persona.segment}, 배경={persona.background or ''}, "
            f"직업={persona.occupation or ''}, 특성=[{traits}], "
            f"목표=[{goals}], 고충=[{pains}]"
        )
