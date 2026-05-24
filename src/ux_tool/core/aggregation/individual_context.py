from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

import orjson


def load_individual_context(path: Path) -> Dict[str, Any]:
    print(f"[Ctx] Loading Individual aggregate: {path}")
    data = orjson.loads(path.read_bytes())
    print(f"[Ctx] Loaded. Personas={len(data.get('personas', []))}, top_keywords={len(data.get('all_keywords_top', []))}")
    return data


def format_insight_lines(ctx: Dict[str, Any], max_personas: int = 4, max_keywords: int = 8) -> List[str]:
    lines: List[str] = []
    top_keywords = ctx.get("all_keywords_top", [])[:max_keywords]
    if top_keywords:
        lines.append(f"TopKeywords: {', '.join(top_keywords)}")
    for p in ctx.get("personas", [])[:max_personas]:
        name = p.get("name")
        kws = ", ".join((p.get("keywords") or [])[:4])
        summary = (p.get("summary") or "").strip()
        if summary:
            summary = summary.split("\n")[0][:200]
        lines.append(f"PersonaSummary[{name}]: {summary}")
        if kws:
            lines.append(f"PersonaKeywords[{name}]: {kws}")
    return lines


