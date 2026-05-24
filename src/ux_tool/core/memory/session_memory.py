from __future__ import annotations

from collections import deque
from typing import Deque, List


class SessionMemory:
    def __init__(self, max_turns: int = 20) -> None:
        self._lines: Deque[str] = deque(maxlen=max_turns)

    def add(self, speaker: str, text: str) -> None:
        self._lines.append(f"{speaker}: {text}")

    def tail(self, n: int = 6) -> List[str]:
        return list(self._lines)[-n:]


