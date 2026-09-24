"""Command-line entry point for llm7shi.

Run with: uv run llm7shi <command> [args]

Commands are dispatched here (via __main__.py rather than a submodule) so that
running a module that __init__.py already imports does not trigger runpy's
"found in sys.modules" RuntimeWarning.
"""
import argparse
import sys

from . import __version__
from .terminal import render_file
from . import usage as usage_module


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)

    # "usage" has its own argparse CLI (see usage.py) so it also works as a
    # standalone console-script target elsewhere; dispatch to it directly
    # rather than redefining its parser here.
    if argv and argv[0] == "usage":
        return usage_module.main(argv[1:], prog="llm7shi usage")

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

    args = parser.parse_args(argv)

    if args.command == "md":
        render_file(args.file)  # streams in chunks, exercising the same path as live LLM output
        return 0

    parser.error(f"unknown command: {args.command}")  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
