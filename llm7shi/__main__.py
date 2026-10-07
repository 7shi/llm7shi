"""Entry point for `python -m llm7shi`; the CLI itself lives in llm7shi/cli."""
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
