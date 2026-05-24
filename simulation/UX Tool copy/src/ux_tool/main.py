from typing import Optional

def run() -> None:
    """Package-level entrypoint if needed by external runners."""
    # Intentionally minimal; prefer module CLIs in ux_tool.cli
    print("UX Tool package loaded. Use: python -m ux_tool.cli.fgi or individual")


if __name__ == "__main__":
    run()


