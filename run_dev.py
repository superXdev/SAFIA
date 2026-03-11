"""Run the bot with auto-reload on file changes.

  uv sync --extra dev
  uv run python run_dev.py
"""
import os
import sys

from watchfiles import run_process


def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    cmd = f"{sys.executable} main.py"
    run_process(root, target=cmd, target_type="command")


if __name__ == "__main__":
    main()
