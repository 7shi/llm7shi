"""`llm7shi usage` CLI: summarize or consolidate usage.jsonl records.

Run with: uv run llm7shi usage <command> [args]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ..usage import (
    Usage,
    _display_path,
    find_usage_file,
    format_usage_line,
    merge_usage,
    parse_usage_file,
    print_today_totals,
    today,
)


def _cmd_show(file: Path, show_all: bool, models: list[str] | None = None) -> int:
    totals = parse_usage_file(file)
    if not totals:
        print(f"{file}: no records")
        return 1

    if models is not None:
        # drop dates left with no matching model so --all doesn't print empty sections
        filtered = {}
        for date, by_model in totals.items():
            kept = {m: u for m, u in by_model.items() if m in models}
            if kept:
                filtered[date] = kept
        if not filtered:
            print(f"No records for {', '.join(models)}")
            return 1
        totals = filtered

    if not show_all:
        date = today()
        if date not in totals:
            print(f"No records for {date}")
            return 1
        print_today_totals(file, date, models)
        return 0

    # also accumulate a grand total across all dates, per model
    model_totals: dict[str, Usage] = {}
    sections = [f"# {_display_path(file)}"]
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


def _cmd_merge(file: Path) -> int:
    if not file.exists():
        print(f"{file}: no records")
        return 1
    before, after = merge_usage(file)
    print(f"{file}: merged {before} -> {after} lines")
    return 0


def main(argv: list[str] | None = None, prog: str | None = None) -> int:
    """CLI for summarizing/consolidating usage.jsonl records.

    Run with: uv run llm7shi usage <command> [args]

    `prog` defaults to argparse's own choice (the invoked script's name), which is
    right when a downstream project points a console script straight at this
    function; `llm7shi/__main__.py` passes "llm7shi usage" so help text matches
    how it was actually invoked.
    """
    parser = argparse.ArgumentParser(prog=prog, description="Summarize or consolidate usage.jsonl records")
    parser.add_argument("-f", "--file", type=Path, default=None,
                        help="Path to usage.jsonl (default: the account-level file under "
                             "$XDG_STATE_HOME or ~/.local/state)")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="Summarize recorded token usage")
    show.add_argument("-a", "--all", action="store_true",
                      help="Show every date's totals plus a grand total (default: today only)")
    show.add_argument("-m", "--model", action="append", dest="models", metavar="MODEL",
                      help="Only show this model (exact name); repeat for several")

    sub.add_parser("merge", help="Consolidate records to one line per UTC date and model")

    args = parser.parse_args(argv)
    file = args.file or find_usage_file()

    if args.command == "show":
        return _cmd_show(file, args.all, args.models)
    return _cmd_merge(file)  # only "merge" remains; the subparsers already validated the choice


if __name__ == "__main__":
    raise SystemExit(main())
