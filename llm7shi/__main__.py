"""Command-line entry point for llm7shi.

Run with: uv run -m llm7shi <command> [args]

Commands are dispatched here (via __main__.py rather than a submodule) so that
running a module that __init__.py already imports does not trigger runpy's
"found in sys.modules" RuntimeWarning.
"""
import argparse
import sys

from .terminal import render_file
from . import usage as usage_module


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)

    # "usage" has its own argparse CLI (see usage.py) so it also works as a
    # standalone console-script target elsewhere; dispatch to it directly
    # rather than redefining its parser here.
    if argv and argv[0] == "usage":
        return usage_module.main(argv[1:])

    parser = argparse.ArgumentParser(prog="llm7shi")
    sub = parser.add_subparsers(dest="command", required=True)

    md = sub.add_parser("md", help="Render a Markdown file to the terminal")
    md.add_argument("file", help="Path to the Markdown file")

    sub.add_parser("usage", help="Summarize or consolidate usage.jsonl records (see llm7shi.usage)")

    args = parser.parse_args(argv)

    if args.command == "md":
        render_file(args.file)  # streams in chunks, exercising the same path as live LLM output
        return 0

    parser.error(f"unknown command: {args.command}")  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
