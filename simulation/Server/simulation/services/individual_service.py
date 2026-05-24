"""
Individual Interview Simulation Service
"""
from typing import List, Generator
import orjson
from simulation.types import Persona, Questionnaire, Question, Transcript, Utterance
from simulation.services.gemini_client import get_gemini_client


class IndividualInterviewService:
    """
    Service for running 1:1 individual interview simulations.
    Each persona answers questionnaire questions independently.
    """

    def __init__(self):
        self.client = get_gemini_client()

    def build_response_prompt(
        self,
        persona: Persona,
        question: Question,
        previous_responses: List[str] = None
    ) -> str:
        """Build prompt for generating persona response"""
        from simulation.services.templates import (
            SYSTEM_TEMPLATE, PERSONA_TEMPLATE, INDIVIDUAL_INTERVIEW_PROMPT,
            SCALE_INSTRUCTION, MULTI_INSTRUCTION, OPEN_INSTRUCTION
        )
        
        prev_context = ""
        if previous_responses:
            prev_context = "- " + "\n- ".join(previous_responses[-3:])
        
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
        
        return INDIVIDUAL_INTERVIEW_PROMPT.format(
            system=SYSTEM_TEMPLATE,
            persona_role=PERSONA_TEMPLATE,
            persona_name=persona.name,
            age=persona.age,
            gender=persona.gender,
            segment=persona.segment,
            background=persona.background or "",
            occupation=persona.occupation or "",
            traits=traits_str,
            goals=goals_str,
            pains=pains_str,
            previous_responses=prev_context,
            question_text=question.text,
            kind_instruction=kind_instruction
        )

    def run_interview(
        self,
        persona: Persona,
        questionnaire: Questionnaire,
        max_questions: int = None
    ) -> Transcript:
        """
        Run a complete individual interview simulation.
        
        Args:
            persona: The persona to interview
            questionnaire: The questionnaire to use
            max_questions: Maximum number of questions (None for all)
            
        Returns:
            Complete interview transcript
        """
        transcript = Transcript(
            session_id=f"ind_{persona.id}",
            mode="individual"
        )
        
        questions = questionnaire.questions
        if max_questions:
            questions = questions[:max_questions]
        
        previous_responses = []
        
        for question in questions:
            # Add question to transcript
            transcript.add("Interviewer", question.text)
            
            # Generate response
            prompt = self.build_response_prompt(persona, question, previous_responses)
            response = self.client.generate(prompt)
            
            # Add response to transcript
            transcript.add(persona.name, response)
            previous_responses.append(f"Q: {question.text}\nA: {response}")
        
        return transcript

    def run_interview_stream(
        self,
        persona: Persona,
        questionnaire: Questionnaire,
        max_questions: int = None
    ) -> Generator[dict, None, None]:
        """
        Run interview with streaming responses.
        
        Yields:
            Dict with type (question/response/complete) and data
        """
        questions = questionnaire.questions
        if max_questions:
            questions = questions[:max_questions]
        
        previous_responses = []
        all_utterances = []
        
        for i, question in enumerate(questions):
            # Yield question
            yield {
                "type": "question",
                "turn": len(all_utterances) + 1,
                "speaker": "Interviewer",
                "text": question.text
            }
            all_utterances.append({"speaker": "Interviewer", "text": question.text})
            
            # Generate and yield response
            prompt = self.build_response_prompt(persona, question, previous_responses)
            
            response_text = ""
            for chunk in self.client.generate_stream(prompt):
                response_text += chunk
                yield {
                    "type": "response_chunk",
                    "speaker": persona.name,
                    "chunk": chunk
                }
            
            yield {
                "type": "response_complete",
                "turn": len(all_utterances) + 1,
                "speaker": persona.name,
                "text": response_text
            }
            
            all_utterances.append({"speaker": persona.name, "text": response_text})
            previous_responses.append(f"Q: {question.text}\nA: {response_text}")
        
        yield {
            "type": "complete",
            "transcript": all_utterances
        }

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
