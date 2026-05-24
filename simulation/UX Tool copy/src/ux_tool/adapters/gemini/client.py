from __future__ import annotations

from typing import Optional

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - optional import in dev
    genai = None  # type: ignore

from ux_tool.adapters.gemini.retry import default_retry
from ux_tool.adapters.gemini.safety import sanitize_prompt
from ux_tool.config.gemini_config import GeminiSettings


class GeminiClient:
    def __init__(self, settings: GeminiSettings) -> None:
        self._settings = settings
        self._model: Optional[object] = None
        if settings.api_key and genai is not None:
            genai.configure(api_key=settings.api_key)
            self._model = genai.GenerativeModel(settings.model)

    @default_retry()
    def generate(self, prompt: str) -> str:
        prompt = sanitize_prompt(prompt)
        head = prompt[:80].replace("\n", " ")
        if self._model is None:
            print(f"[Gen] Fallback generate: '{head}...' ")
            # Dev fallback when API key is absent or SDK missing
            return self._fallback_generate(prompt)
        print(f"[Gen] Gemini generate ({self._settings.model}): '{head}...' ")
        resp = self._model.generate_content(prompt)  # type: ignore[attr-defined]
        text = getattr(resp, "text", None)
        return text or ""

    @staticmethod
    def _fallback_generate(prompt: str) -> str:
        # Simple heuristic placeholder for local testing
        head = prompt[:120].replace("\n", " ")
        return f"[DEV_FAKE_RESPONSE] {head} ..."


