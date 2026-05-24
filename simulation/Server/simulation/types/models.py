"""
Type definitions for UX Simulation
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Persona(BaseModel):
    """Persona definition for simulation"""
    id: str
    name: str
    age: int
    gender: str = ""
    segment: str = ""
    background: str = ""
    occupation: str = ""
    location: str = ""
    household_size: int = 1
    income_monthly: int = 0
    spend_monthly: int = 0
    spend_breakdown: Dict[str, int] = Field(default_factory=dict)
    traits: Dict[str, str] = Field(default_factory=dict)
    goals: List[str] = Field(default_factory=list)
    pains: List[str] = Field(default_factory=list)


class Question(BaseModel):
    """Question in a questionnaire"""
    id: str
    text: str
    kind: str = "open"  # open, scale, multi
    scale_min: Optional[int] = None
    scale_max: Optional[int] = None
    options: List[str] = Field(default_factory=list)


class Questionnaire(BaseModel):
    """Questionnaire for FGI or Individual interview"""
    id: str
    title: str
    instructions: str = ""
    questions: List[Question]


class Scenario(BaseModel):
    """Scenario for simulation context"""
    id: str
    title: str
    description: str = ""
    context: str = ""


class Utterance(BaseModel):
    """A single utterance in a transcript"""
    turn: int
    speaker: str
    text: str
    timestamp: Optional[str] = None


class Transcript(BaseModel):
    """Collection of utterances from a session"""
    session_id: str
    mode: str  # fgi or individual
    utterances: List[Utterance] = Field(default_factory=list)

    def add(self, speaker: str, text: str):
        """Add a new utterance"""
        turn = len(self.utterances) + 1
        self.utterances.append(Utterance(turn=turn, speaker=speaker, text=text))

    def as_lines(self) -> List[str]:
        """Convert to list of formatted lines"""
        return [f"{u.turn}. {u.speaker}: {u.text}" for u in self.utterances]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "utterances": [u.model_dump() for u in self.utterances]
        }


class JourneyStep(BaseModel):
    """A step in a user journey"""
    step: int
    stage: str
    action_label: str
    rationale: str = ""
    expected_outcome: str = ""
    subtasks: List[str] = Field(default_factory=list)
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    system_touchpoints: List[str] = Field(default_factory=list)
    success_metric: str = ""
    risks: List[str] = Field(default_factory=list)
    mitigations: List[str] = Field(default_factory=list)
    owner: str = ""
    eta: str = ""


class JourneyMap(BaseModel):
    """Complete journey map for a persona"""
    goal: str
    persona_id: str
    persona_name: str
    steps: List[JourneyStep] = Field(default_factory=list)
