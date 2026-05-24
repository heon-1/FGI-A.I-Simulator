from __future__ import annotations

import re


_BANNED = [
    r"(?i)password",
    r"(?i)api[_-]?key",
]


def sanitize_prompt(text: str, max_chars: int = 6000) -> str:
    sanitized = text
    for pat in _BANNED:
        sanitized = re.sub(pat, "[REDACTED]", sanitized)
    if len(sanitized) > max_chars:
        sanitized = sanitized[: max_chars - 3] + "..."
    return sanitized


