#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from ux_tool.core.aggregation.journey_map import generate_journey_map_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a journey map CSV from a session directory (FGI or Individual).")
    parser.add_argument("--session", required=True, help="Path to session directory under outputs/<mode>/<session_id>")
    parser.add_argument("--out", required=True, help="Output CSV file")
    parser.add_argument("--q", help="Questionnaire JSON path (optional). If omitted, defaults per mode.")
    args = parser.parse_args()

    session_dir = Path(args.session)
    out_csv = Path(args.out)
    q_path: Optional[Path] = Path(args.q) if args.q else None

    result = generate_journey_map_csv(session_dir, out_csv, questionnaire_path=q_path)
    print(f"[OK] Wrote journey map CSV: {result}")


if __name__ == "__main__":
    main()


