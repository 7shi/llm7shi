"""Command-line entry point for llm7shi, installed as the `llm7shi` command.

Run with: uv run llm7shi <command> [args]
"""
import argparse
import sys

from .. import __version__
from ..terminal import render_file


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)

    # "usage" and "models" own their argparse CLIs (see usage.py, models.py); forward
    # to them rather than redefining their parsers here. Imported on demand so that
    # `python -m llm7shi.cli.usage` does not find itself already in sys.modules
    # (runpy's RuntimeWarning).
    if argv and argv[0] == "usage":
        from .usage import main as usage_main
        return usage_main(argv[1:], prog="llm7shi usage")
    if argv and argv[0] == "models":
        from .models import main as models_main
        return models_main(argv[1:], prog="llm7shi models")

    parser = argparse.ArgumentParser(
        prog="llm7shi",
        description="Command-line tools bundled with the llm7shi library.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    md = sub.add_parser(
        "md",
        help="Render a Markdown file with llm7shi's terminal formatting",
        description="Render a Markdown file to the terminal with the same colored "
                    "formatting llm7shi applies to streamed LLM output (bold, inline "
                    "code, code fences). The file is fed through the streaming "
                    "converter in chunks, so this is mainly for checking how output "
                    "will look without calling an API; it also works as a simple "
                    "Markdown viewer.",
    )
    md.add_argument("file", help="Path to the Markdown file")

    sub.add_parser(
        "usage",
        help="Show or merge recorded token usage (usage.jsonl); "
             "run 'llm7shi usage -h' for its options",
        add_help=False,  # never reached: "usage" is dispatched above before parsing
    )
    sub.add_parser(
        "models",
        help="List the models a provider offers (e.g. 'openrouter --free'); "
             "run 'llm7shi models -h' for its options",
        add_help=False,  # never reached: dispatched above like "usage"
    )

    args = parser.parse_args(argv)

    if args.command == "md":
        render_file(args.file)  # streams in chunks, exercising the same path as live LLM output
        return 0

    parser.error(f"unknown command: {args.command}")  # pragma: no cover

