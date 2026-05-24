import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    output_dir: Path
    log_level: str


def load_app_config() -> AppConfig:
    load_dotenv(override=False)

    cwd = Path(os.getcwd())
    data_dir = Path(os.getenv("DATA_DIR", cwd.joinpath("data")))
    output_dir = Path(os.getenv("OUTPUT_DIR", cwd.joinpath("outputs")))
    log_level = os.getenv("LOG_LEVEL", "INFO")

    output_dir.mkdir(parents=True, exist_ok=True)
    return AppConfig(data_dir=data_dir, output_dir=output_dir, log_level=log_level)


