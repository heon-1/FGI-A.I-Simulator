from __future__ import annotations

from pathlib import Path

from ux_tool.io.validator import load_personas_from_dir, load_questionnaire, load_scenario


def main() -> None:
    root = Path.cwd()
    data_dir = root.joinpath("data")

    # Optional default locations
    q_fgi = data_dir.joinpath("questionnaires/fgi.json")
    q_ind = data_dir.joinpath("questionnaires/individual.json")
    personas_dir = data_dir.joinpath("personas")
    scenario = data_dir.joinpath("scenarios/default.json")

    if q_fgi.exists():
        load_questionnaire(q_fgi)
        print(f"Validated: {q_fgi}")
    if q_ind.exists():
        load_questionnaire(q_ind)
        print(f"Validated: {q_ind}")
    if personas_dir.exists():
        load_personas_from_dir(personas_dir)
        print(f"Validated personas: {personas_dir}")
    if scenario.exists():
        load_scenario(scenario)
        print(f"Validated: {scenario}")


if __name__ == "__main__":
    main()


