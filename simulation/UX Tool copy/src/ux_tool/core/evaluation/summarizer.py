from __future__ import annotations

from typing import List

from ux_tool.adapters.gemini.client import GeminiClient


def summarize_transcript(client: GeminiClient, lines: List[str]) -> str:
    if not lines:
        return ""
    prompt = (
        "Summarize the following focus group transcript into key insights, pains, and opportunities "
        "in under 200 words.\n\n" + "\n".join(lines[-40:])
    )
    return client.generate(prompt)


