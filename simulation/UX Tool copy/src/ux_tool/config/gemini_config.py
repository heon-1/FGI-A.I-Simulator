import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class GeminiSettings:
    api_key: Optional[str]
    model: str
    temperature: float
    top_p: float
    top_k: int


def load_gemini_settings() -> GeminiSettings:
    load_dotenv(override=False)
    return GeminiSettings(
        api_key=os.getenv("GEMINI_API_KEY"),
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-pro"),
        temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.8")),
        top_p=float(os.getenv("GEMINI_TOP_P", "0.95")),
        top_k=int(os.getenv("GEMINI_TOP_K", "40")),
    )


