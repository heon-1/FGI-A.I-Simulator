from typing import Dict, List, Optional

from pydantic import BaseModel


class Scenario(BaseModel):
    id: str
    title: str
    description: str
    context: Dict[str, str] = {}
    constraints: List[str] = []


