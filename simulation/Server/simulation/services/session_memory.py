"""
Session Memory for maintaining conversation context.
Based on original UX Tool implementation.
"""
from typing import List, Optional
from collections import deque


class SessionMemory:
    """
    Memory for tracking conversation history within a session.
    Used to provide context for subsequent prompts.
    """
    
    def __init__(self, max_turns: int = 40):
        """
        Initialize session memory.
        
        Args:
            max_turns: Maximum number of turns to keep in memory
        """
        self.max_turns = max_turns
        self._history: deque = deque(maxlen=max_turns)
    
    def add(self, speaker: str, text: str) -> None:
        """
        Add a new utterance to memory.
        
        Args:
            speaker: Who said it (Moderator, persona name, etc.)
            text: What was said
        """
        self._history.append({
            "speaker": speaker,
            "text": text
        })
    
    def tail(self, n: int = 6) -> List[str]:
        """
        Get the last n utterances as formatted strings.
        
        Args:
            n: Number of recent utterances to return
            
        Returns:
            List of formatted utterance strings
        """
        recent = list(self._history)[-n:]
        return [f"{u['speaker']}: {u['text']}" for u in recent]
    
    def get_context(self, n: int = 6) -> str:
        """
        Get recent conversation as a single string.
        
        Args:
            n: Number of recent utterances
            
        Returns:
            Formatted conversation string
        """
        return "\n".join(self.tail(n))
    
    def clear(self) -> None:
        """Clear all memory"""
        self._history.clear()
    
    def __len__(self) -> int:
        """Return number of items in memory"""
        return len(self._history)
    
    @property
    def all_utterances(self) -> List[dict]:
        """Return all stored utterances"""
        return list(self._history)
