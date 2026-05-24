from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Dict, Any, Tuple
import csv

import orjson


def _parse_context_from_path(path: Path) -> Tuple[str, str, str]:
    """
    Extract (mode, session_id, persona_id) from transcript paths.

    Supported layouts:
    - Individual: .../outputs/<mode>/<session_id>/<persona_id>/transcript.json
    - FGI:        .../outputs/<mode>/<session_id>/transcript.json
    """
    parts = path.parts
    try:
        out_idx = parts.index("outputs")
    except ValueError:
        # Fallback: best-effort based on parents
        mode = ""
        session_id = path.parents[1].name if len(path.parents) >= 2 else ""
        persona_id = path.parent.name if path.parent else ""
        return mode, session_id, persona_id

    mode = parts[out_idx + 1] if len(parts) > out_idx + 1 else ""
    rel_after_mode = parts[out_idx + 2 :]  # e.g., [session_id, (persona_id), 'transcript.json']

    session_id = rel_after_mode[0] if len(rel_after_mode) >= 1 else ""
    # If we have at least 3 parts after mode, we assume persona_id exists
    if len(rel_after_mode) >= 3:
        persona_id = rel_after_mode[-2]
    else:
        persona_id = ""

    return mode, session_id, persona_id


def _load_transcript(path: Path) -> Dict[str, Any]:
    return orjson.loads(path.read_bytes())


def collect_transcript_rows(transcript_paths: Iterable[Path]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for p in transcript_paths:
        mode, session_id, persona_id = _parse_context_from_path(p)
        data = _load_transcript(p)
        utterances = data.get("utterances", [])
        for u in utterances:
            rows.append(
                {
                    "mode": mode,
                    "session_id": session_id,
                    "persona_id": persona_id,
                    "turn": u.get("turn"),
                    "speaker": u.get("speaker"),
                    "text": u.get("text"),
                    "source_path": str(p),
                }
            )
    # Stable, readable ordering
    rows.sort(key=lambda r: (r["session_id"], r["persona_id"], r["turn"]))
    return rows


def merge_transcripts_to_csv(transcript_paths: Iterable[Path], out_csv: Path) -> Path:
    rows = collect_transcript_rows(transcript_paths)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["mode", "session_id", "persona_id", "turn", "speaker", "text", "source_path"]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out_csv


