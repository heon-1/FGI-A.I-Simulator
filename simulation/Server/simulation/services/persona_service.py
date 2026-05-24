"""
Persona Management Service
"""
from typing import List, Optional
import orjson
from pathlib import Path
from django.conf import settings

from simulation.types import Persona


class PersonaService:
    """Service for managing personas"""

    @staticmethod
    def create_persona(data: dict) -> Persona:
        """Create a new persona from data"""
        return Persona(**data)

    @staticmethod  
    def validate_persona(data: dict) -> tuple[bool, Optional[str]]:
        """Validate persona data"""
        try:
            Persona(**data)
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def persona_to_prompt_block(persona: Persona) -> str:
        """Convert persona to a text block for prompts"""
        traits = ", ".join([f"{k}:{v}" for k, v in (persona.traits or {}).items()])
        goals = ", ".join(persona.goals or [])
        pains = ", ".join(persona.pains or [])
        
        return (
            f"id={persona.id}, name={persona.name}, age={persona.age}, "
            f"gender={persona.gender}, segment={persona.segment}, "
            f"background={persona.background or ''}, occupation={persona.occupation or ''}, "
            f"location={persona.location or ''}, traits=[{traits}], goals=[{goals}], pains=[{pains}]"
        )

    @staticmethod
    def generate_persona_prompt(context: str) -> str:
        """Generate prompt for AI persona generation"""
        from simulation.services.templates import PERSONA_GENERATION_PROMPT
        
        return PERSONA_GENERATION_PROMPT.format(context=context)
