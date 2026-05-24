from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import orjson


def create_session_dir(mode: str, output_root: Path) -> Path:
    session_id = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    session_dir = output_root.joinpath(mode, session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    print(f"[IO] Created session dir: {session_dir}")
    return session_dir


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    b = orjson.dumps(data, option=orjson.OPT_INDENT_2)
    path.write_bytes(b)
    print(f"[IO] Wrote JSON: {path} ({len(b)} bytes)")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"[IO] Wrote text: {path} ({len(text)} chars)")


