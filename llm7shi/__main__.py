"""Command-line entry point for llm7shi.

Run with: uv run -m llm7shi <command> [args]

Commands are dispatched here (via __main__.py rather than a submodule) so that
running a module that __init__.py already imports does not trigger runpy's
"found in sys.modules" RuntimeWarning.
"""
import argparse
from pathlib import Path

from .terminal import render_file
from .usage import Usage, find_usage_file, format_usage_line, merge_usage, parse_usage_file, today


def _usage_show(file: Path, show_all: bool) -> int:
    totals = parse_usage_file(file)
    if not totals:
        print(f"{file}: no records")
        return 1

    if not show_all:
        date = today()
        if date not in totals:
            print(f"No records for {date}")
            return 1
        print(f"# {date}")
        for model, usage in totals[date].items():
            print(format_usage_line(model, usage))
        return 0

    # also accumulate a grand total across all dates, per model
    model_totals: dict[str, Usage] = {}
    sections = []
    for date, by_model in totals.items():
        lines = [f"# {date}"]
        for model, usage in by_model.items():
            lines.append(format_usage_line(model, usage))
            model_totals[model] = usage if model not in model_totals else model_totals[model] + usage
        sections.append("\n".join(lines))

    total_lines = ["===== Total ====="]
    for model, usage in model_totals.items():
        total_lines.append(format_usage_line(model, usage))
    sections.append("\n".join(total_lines))

    print("\n\n".join(sections))
    return 0


def _usage_merge(file: Path) -> int:
    if not file.exists():
        print(f"{file}: no records")
        return 1
    before, after = merge_usage(file)
    print(f"{file}: merged {before} -> {after} lines")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="llm7shi")
    sub = parser.add_subparsers(dest="command", required=True)

    md = sub.add_parser("md", help="Render a Markdown file to the terminal")
    md.add_argument("file", help="Path to the Markdown file")

    usage = sub.add_parser("usage", help="Summarize or consolidate usage.jsonl records")
    usage.add_argument("-f", "--file", type=Path, default=None,
                        help="Path to usage.jsonl (default: search upward from the current directory)")
    usage_sub = usage.add_subparsers(dest="usage_command", required=True)
    usage_show = usage_sub.add_parser("show", help="Summarize recorded token usage")
    usage_show.add_argument("-a", "--all", action="store_true",
                             help="Show every date's totals plus a grand total (default: today only)")
    usage_sub.add_parser("merge", help="Consolidate records to one line per UTC date and model")

    args = parser.parse_args(argv)

    if args.command == "md":
        render_file(args.file)  # streams in chunks, exercising the same path as live LLM output
        return 0

    if args.command == "usage":
        try:
            file = args.file or find_usage_file()
        except FileNotFoundError as e:
            print(e)
            return 1
        if args.usage_command == "show":
            return _usage_show(file, args.all)
        return _usage_merge(file)  # only "merge" remains; subparsers already validated the choice

    parser.error(f"unknown command: {args.command}")  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
