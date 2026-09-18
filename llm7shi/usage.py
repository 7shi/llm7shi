# Usage dataclass for provider-agnostic token-usage info, plus helpers for
# persisting and aggregating it in a usage.jsonl file.
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .utils import locked


@dataclass
class Usage:
    """Token-usage info from a provider's streaming response.

    Field names and structure vary per provider/API (see
    docs/20260915-token-usage.md for the source survey), so `raw` keeps
    whatever the provider returned, untouched. The properties below are
    best-effort normalizations that generalize across all providers tracked
    there; each returns None where a provider doesn't report that dimension
    at all (e.g. Ollama has no reasoning or cached-token breakdown).

    Attributes:
        raw: The provider's usage dict with its own field names, e.g.
            "prompt_eval_count"/"eval_count" for Ollama vs
            "input_tokens"/"output_tokens" for OpenAI's Responses API
    """
    # defaults to {} so Usage() can serve as a zero value
    raw: dict = field(default_factory=dict)

    def _first(self, *keys: str) -> Optional[int]:
        for key in keys:
            if (value := self.raw.get(key)) is not None:
                return value
        return None

    def _first_nested(self, *paths: tuple) -> Optional[int]:
        for outer, inner in paths:
            outer_value = self.raw.get(outer)
            if isinstance(outer_value, dict) and (value := outer_value.get(inner)) is not None:
                return value
        return None

    @property
    def input_tokens(self) -> Optional[int]:
        return self._first("input_tokens", "prompt_tokens", "prompt_token_count", "prompt_eval_count")

    @property
    def output_tokens(self) -> Optional[int]:
        return self._first("output_tokens", "completion_tokens", "candidates_token_count", "eval_count")

    @property
    def reasoning_tokens(self) -> Optional[int]:
        # "reasoning_tokens" itself covers __add__'s result (see below); Gemini reports
        # this at the top level under its own name, OpenAI (both APIs) nest it under a *_details dict
        direct = self._first("reasoning_tokens", "thoughts_token_count")
        if direct is not None:
            return direct
        return self._first_nested(
            ("output_tokens_details", "reasoning_tokens"),
            ("completion_tokens_details", "reasoning_tokens"),
        )

    @property
    def cached_tokens(self) -> Optional[int]:
        # "cached_tokens" itself covers __add__'s result (see below); only OpenAI (both
        # APIs) otherwise reports this - Gemini and Ollama don't track cache hits at all
        direct = self._first("cached_tokens")
        if direct is not None:
            return direct
        return self._first_nested(
            ("input_tokens_details", "cached_tokens"),
            ("prompt_tokens_details", "cached_tokens"),
        )

    @property
    def total_tokens(self) -> Optional[int]:
        # every provider but Ollama reports a total directly; Ollama's own API never
        # surfaces a combined count either, so it's summed here from the two halves
        direct = self._first("total_tokens", "total_token_count")
        if direct is not None:
            return direct
        if self.input_tokens is not None and self.output_tokens is not None:
            return self.input_tokens + self.output_tokens
        return None

    def to_dict(self) -> dict:
        """The normalized fields (omitting any the provider didn't report), without `raw`."""
        fields = {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "cached_tokens": self.cached_tokens,
            "total_tokens": self.total_tokens,
        }
        return {k: v for k, v in fields.items() if v is not None}

    def __repr__(self) -> str:
        # raw omitted: it's the noisiest part of the object and dataclasses print on-screen
        # a lot (e.g. bare `response.usage` at a REPL); use .raw directly to inspect it
        return f"Usage({self.to_dict()})"

    def __add__(self, other: "Usage") -> "Usage":
        """Sum the normalized fields, for aggregating usage across multiple calls.

        `raw` is ignored (and absent from the result) since its shape is
        provider-specific and summing it field-by-field wouldn't generalize
        the way the normalized fields already do.
        """
        if not isinstance(other, Usage):
            return NotImplemented
        fields = {}
        for key in ("input_tokens", "output_tokens", "reasoning_tokens", "cached_tokens", "total_tokens"):
            a, b = getattr(self, key), getattr(other, key)
            if a is not None or b is not None:
                fields[key] = (a or 0) + (b or 0)
        return Usage(raw=fields)

    def __radd__(self, other: int) -> "Usage":
        """Support sum(usages) by absorbing the implicit int(0) start value."""
        if other == 0:
            return self
        return NotImplemented


# --- usage.jsonl persistence -------------------------------------------------
#
# One JSON object per line: {"timestamp": ..., "model": ..., **usage.to_dict()}.
# A caller accumulating usage across many short-lived processes (e.g. one process
# per batch item) can't hold a running total in memory, so each call's Usage is
# appended as its own record and totals are computed by re-reading the file.
# Reads and writes go through utils.locked() so concurrent writers don't interleave.


def format_usage_line(model: str, usage: Usage) -> str:
    """Format a model name and its Usage as `model|input:N|output:N|...` (comma-grouped counts)."""
    parts = [model]
    for key, value in usage.to_dict().items():
        parts.append(f"{key.removesuffix('_tokens')}:{value:,}")
    return "|".join(parts)


def today() -> str:
    """Today's date in UTC, as `YYYY/MM/DD` (matching parse_usage_file's date keys)."""
    return datetime.now(timezone.utc).strftime("%Y/%m/%d")


def find_usage_file() -> Path:
    """Search upward from the current directory for a usage.jsonl, and return its path.

    This module makes no assumption about where a project's usage.jsonl lives (that's
    a per-project choice), so the search starts from cwd rather than anywhere fixed,
    and raises FileNotFoundError instead of falling back to a guessed location.
    """
    start = Path.cwd().resolve()
    for d in (start, *start.parents):
        candidate = d / "usage.jsonl"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"usage.jsonl not found searching upward from {start}")


def parse_usage_file(path: Path) -> dict[str, dict[str, Usage]]:
    """Parse a usage.jsonl file into {date: {model: total Usage}}.

    Each record's date is its `timestamp` converted to UTC. Date and model keys
    keep the order they first appear in the file. Returns {} if `path` doesn't
    exist. Reading is serialized via the same lock writers use.
    """
    if not path.exists():
        return {}

    with locked(path, "r") as f:
        text = f.read()

    totals: dict[str, dict[str, Usage]] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        timestamp = datetime.fromisoformat(record["timestamp"]).astimezone(timezone.utc)
        date = timestamp.strftime("%Y/%m/%d")
        model = record["model"]
        usage = Usage(raw={k: v for k, v in record.items() if k not in ("timestamp", "model")})
        by_model = totals.setdefault(date, {})
        by_model[model] = usage if model not in by_model else by_model[model] + usage
    return totals


def append_usage(usage: Usage, model: str, path: Path, timestamp: datetime | None = None) -> None:
    """Append one record (Usage, model name, timezone-aware timestamp) to usage.jsonl.

    `timestamp` defaults to the current local time. Appending is serialized via flock.
    """
    timestamp = timestamp or datetime.now().astimezone()
    record = {"timestamp": timestamp.isoformat(), "model": model, **usage.to_dict()}
    with locked(path, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def merge_usage(path: Path) -> tuple[int, int]:
    """Consolidate usage.jsonl to one record per (UTC date, model), rewriting the file.

    Records sharing a UTC date and model are summed into one; the merged record's
    timestamp is that day's UTC midnight, so re-merging is idempotent. Date/model
    order follows first appearance. Reading and writing happen under one lock, so
    no other process can observe a half-written file. Returns (line count before,
    line count after).
    """
    with locked(path, "r+") as f:
        lines = [line for line in f.read().splitlines() if line.strip()]

        merged: dict[tuple, Usage] = {}
        order: list[tuple] = []
        for line in lines:
            record = json.loads(line)
            timestamp = datetime.fromisoformat(record["timestamp"]).astimezone(timezone.utc)
            date = timestamp.date()
            model = record["model"]
            usage = Usage(raw={k: v for k, v in record.items() if k not in ("timestamp", "model")})
            key = (date, model)
            if key not in merged:
                merged[key] = usage
                order.append(key)
            else:
                merged[key] = merged[key] + usage

        new_lines = []
        for date, model in order:
            timestamp = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)
            record = {"timestamp": timestamp.isoformat(), "model": model, **merged[(date, model)].to_dict()}
            new_lines.append(json.dumps(record, ensure_ascii=False))

        f.seek(0)
        f.write("".join(line + "\n" for line in new_lines))
        f.truncate()

    return len(lines), len(new_lines)


# --- CLI ----------------------------------------------------------------
#
# A full argparse CLI (not just functions __main__.py could call directly) so
# this module works as a console-script target on its own, e.g. a downstream
# project's `usage = "llm7shi.usage:main"`, without needing a wrapper that
# prepends "usage" to argv. `llm7shi/__main__.py`'s `usage` subcommand forwards
# its remaining argv here instead of redefining the same parser.

def _cmd_show(file: Path, show_all: bool) -> int:
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


def _cmd_merge(file: Path) -> int:
    if not file.exists():
        print(f"{file}: no records")
        return 1
    before, after = merge_usage(file)
    print(f"{file}: merged {before} -> {after} lines")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI for summarizing/consolidating usage.jsonl records.

    Run with: uv run -m llm7shi usage <command> [args]
    """
    parser = argparse.ArgumentParser(prog="usage", description="Summarize or consolidate usage.jsonl records")
    parser.add_argument("-f", "--file", type=Path, default=None,
                        help="Path to usage.jsonl (default: search upward from the current directory)")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="Summarize recorded token usage")
    show.add_argument("-a", "--all", action="store_true",
                      help="Show every date's totals plus a grand total (default: today only)")

    sub.add_parser("merge", help="Consolidate records to one line per UTC date and model")

    args = parser.parse_args(argv)

    try:
        file = args.file or find_usage_file()
    except FileNotFoundError as e:
        print(e)
        return 1

    if args.command == "show":
        return _cmd_show(file, args.all)
    return _cmd_merge(file)  # only "merge" remains; the subparsers already validated the choice


if __name__ == "__main__":
    raise SystemExit(main())
