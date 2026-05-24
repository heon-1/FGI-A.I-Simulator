#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from ux_tool.io.csv_export import merge_transcripts_to_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge transcript.json files into a tidy CSV.")
    parser.add_argument("--out", required=True, help="Output CSV path")
    parser.add_argument("transcripts", nargs="+", help="Paths to transcript.json files")
    args = parser.parse_args()

    out_csv = Path(args.out)
    transcript_paths: List[Path] = [Path(p) for p in args.transcripts]
    result = merge_transcripts_to_csv(transcript_paths, out_csv)
    print(f"[OK] Wrote CSV: {result}")


if __name__ == "__main__":
    main()


