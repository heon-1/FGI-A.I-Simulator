#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from ux_tool.io.csv_export import merge_transcripts_to_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge all transcript.json files in a session directory into a CSV.")
    parser.add_argument("--session", required=True, help="Path to a session directory under outputs/<mode>/<session_id>")
    parser.add_argument("--out", required=True, help="Output CSV path")
    args = parser.parse_args()

    session_dir = Path(args.session)
    out_csv = Path(args.out)

    # Find all transcript.json under session_dir (e.g., <session>/<persona_id>/transcript.json)
    transcript_paths: List[Path] = [p for p in session_dir.rglob("transcript.json") if p.is_file()]
    if not transcript_paths:
        raise SystemExit(f"No transcript.json files found under: {session_dir}")

    result = merge_transcripts_to_csv(transcript_paths, out_csv)
    print(f"[OK] Wrote CSV: {result} (from {len(transcript_paths)} transcripts)")


if __name__ == "__main__":
    main()


