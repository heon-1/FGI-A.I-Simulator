from typing import List, Literal, Optional

from pydantic import BaseModel, Field


QuestionKind = Literal["open", "scale", "multi"]


class Question(BaseModel):
    id: str
    text: str
    kind: QuestionKind = "open"
    options: Optional[List[str]] = None
    scale_min: Optional[int] = Field(default=None)
    scale_max: Optional[int] = Field(default=None)


class Questionnaire(BaseModel):
    id: str
    title: str
    instructions: Optional[str] = None
    questions: List[Question]


