from __future__ import annotations

from pathlib import Path
from typing import List

import orjson
from pydantic import ValidationError

from ux_tool.types.persona import Persona
from ux_tool.types.questionnaire import Questionnaire
from ux_tool.types.scenario import Scenario


def _read_json(path: Path) -> dict:
    return orjson.loads(path.read_bytes())


def load_questionnaire(path: Path) -> Questionnaire:
    data = _read_json(path)
    try:
        return Questionnaire.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Questionnaire validation failed for {path}: {e}") from e


def load_scenario(path: Path) -> Scenario:
    data = _read_json(path)
    try:
        return Scenario.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Scenario validation failed for {path}: {e}") from e


def load_personas_from_dir(dir_path: Path) -> List[Persona]:
    if not dir_path.exists():
        raise FileNotFoundError(f"Persona directory not found: {dir_path}")
    personas: List[Persona] = []
    for path in sorted(dir_path.glob("*.json")):
        data = _read_json(path)
        try:
            personas.append(Persona.model_validate(data))
        except ValidationError as e:
            raise ValueError(f"Persona validation failed for {path}: {e}") from e
    if not personas:
        raise ValueError(f"No personas found in {dir_path}")
    return personas


