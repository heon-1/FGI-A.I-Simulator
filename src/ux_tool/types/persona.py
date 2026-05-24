from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Segment = Literal["early", "mainstream", "pro"]
Gender = Literal["female", "male", "nonbinary", "other"]


class Persona(BaseModel):
    id: str
    name: str
    age: int = Field(ge=15, le=90)
    gender: Optional[Gender] = None
    segment: Segment
    background: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None
    household_size: Optional[int] = Field(default=None, ge=1, le=10)
    income_monthly: Optional[float] = Field(default=None, ge=0)
    spend_monthly: Optional[float] = Field(default=None, ge=0)
    spend_breakdown: Dict[str, float] = Field(default_factory=dict)
    traits: Dict[str, str] = Field(default_factory=dict)
    goals: List[str] = Field(default_factory=list)
    pains: List[str] = Field(default_factory=list)

    @property
    def display(self) -> str:
        return f"{self.name} ({self.segment}, {self.age})"


