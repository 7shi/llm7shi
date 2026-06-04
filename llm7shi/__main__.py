"""Command-line entry point for llm7shi.

Run with: uv run -m llm7shi <command> [args]

Commands are dispatched here (via __main__.py rather than a submodule) so that
running a module that __init__.py already imports does not trigger runpy's
"found in sys.modules" RuntimeWarning.
"""
import argparse

from .terminal import render_file


def main(argv=None):
    parser = argparse.ArgumentParser(prog="llm7shi")
    sub = parser.add_subparsers(dest="command", required=True)

    md = sub.add_parser("md", help="Render a Markdown file to the terminal")
    md.add_argument("file", help="Path to the Markdown file")

    args = parser.parse_args(argv)

    if args.command == "md":
        render_file(args.file)
        return 0

    parser.error(f"unknown command: {args.command}")  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
