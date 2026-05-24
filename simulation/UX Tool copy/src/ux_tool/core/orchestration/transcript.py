from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List


@dataclass
class Utterance:
    turn: int
    speaker: str
    text: str


class Transcript:
    def __init__(self) -> None:
        self._items: List[Utterance] = []

    def add(self, utterance: Utterance) -> None:
        self._items.append(utterance)

    def to_dict(self) -> dict:
        return {"utterances": [asdict(u) for u in self._items]}

    def as_lines(self) -> List[str]:
        return [f"{u.speaker}: {u.text}" for u in self._items]


