"""`llm7shi chat` CLI: an interactive chat session with one model.

Run with: uv run llm7shi chat <model>
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ..client import Client
from ..response import Response
from ..usage import _display_path, append_usage, find_usage_file, print_today_totals
from ..terminal import error

HELP = """\
/think            Show whether thinking is on
/think on|off     Turn thinking on or off
/clear            Clear the conversation history
/help             Show this help
/exit             Exit (or Ctrl+D)"""


def token_rates(resp: Response) -> dict[str, float]:
    """Tokens/s for the input and answer of one response, from its stream timestamps.

    Input: input tokens over request to first chunk (network latency included, so a
    lower bound). Output: answer tokens (output minus reasoning) over the answer's
    own span. Reasoning is left out because OpenAI and Gemini do not stream their
    thinking in full, so its timing is noise. Without a reasoning count (e.g. Ollama)
    thinking can't be split off, so all output tokens are timed from the first chunk
    of either kind.
    """
    rates = {}
    usage = resp.usage
    if usage is None or resp.start_time is None or resp.end_time is None:
        return rates
    first = min((t for t in (resp.thoughts_start_time, resp.text_start_time) if t is not None), default=None)
    if first is not None and usage.input_tokens and first > resp.start_time:
        rates["input_tokens"] = usage.input_tokens / (first - resp.start_time)
    if resp.text_start_time is not None and usage.output_tokens:
        if usage.reasoning_tokens is not None:
            tokens, since = usage.output_tokens - usage.reasoning_tokens, resp.text_start_time
        else:
            tokens, since = usage.output_tokens, first
        if tokens > 0 and resp.end_time > since:
            rates["output_tokens"] = tokens / (resp.end_time - since)
    return rates


def format_stats(usages: list, rates: dict[str, float]) -> str | None:
    """Render this turn's usage as `input:N (N.N tps) | output:N (N.N tps) | ...`."""
    if not usages:
        return None
    usage = sum(usages)  # quality retries add attempts; show what the turn consumed
    parts = []
    for key, value in usage.to_dict().items():
        part = f"{key.removesuffix('_tokens')}:{value:,}"
        if key in rates:
            part += f" ({rates[key]:.1f} tps)"
        parts.append(part)
    return " | ".join(parts)


def _command(client: Client, line: str) -> bool:
    """Handle a /command; return False when the session should end."""
    cmd, *args = line.split()
    if cmd == "/exit":
        return False
    if cmd == "/help":
        print(HELP)
    elif cmd == "/clear":
        client.history.clear()
        print("history cleared")
    elif cmd == "/think":
        if args and args[0] in ("on", "off"):
            client.include_thoughts = args[0] == "on"
        elif args:
            print("usage: /think [on|off]")
            return True
        print(f"think: {'on' if client.include_thoughts else 'off'}")
    else:
        print(f"unknown command: {cmd} (/help for commands)")
    return True


def chat(client: Client, usage_path: Path | None = None) -> None:
    """Run the chat loop; with `usage_path`, record the session's usage there on exit."""
    try:
        import readline  # noqa: F401  line editing and history for input(); absent on Windows
    except ImportError:
        pass

    print(f"model: {client.model} (/help for commands)")
    if usage_path is not None:
        print(f"usage: recording to {_display_path(usage_path)}")
    try:
        _loop(client)
    finally:
        # finally so a session ended with Ctrl+C is still recorded
        if usage_path is not None and client.usages:
            append_usage(sum(client.usages), client.model, usage_path)
            print()
            print_today_totals(usage_path, models=[client.model])


def _loop(client: Client) -> None:
    while True:
        try:
            line = input("> ").strip()
        except EOFError:  # Ctrl+D
            print()
            break
        if not line:
            continue
        if line.startswith("/"):
            if not _command(client, line):
                break
            continue

        count = len(client.usages)
        try:
            resp = client(line)
        except Exception as e:
            # keep the session (and its history) alive across a failed turn; the failed
            # prompt is not added to history since Client appends only after success
            error(f"{type(e).__name__}: {e}")
            continue
        # rates from the final attempt only: each attempt has its own timestamps
        stats = format_stats(client.usages[count:], token_rates(resp))
        if stats:
            print(f"\n{stats}")
        print()


def main(argv: list[str] | None = None, prog: str | None = None) -> int:
    parser = argparse.ArgumentParser(prog=prog, description="Chat interactively with a model")
    parser.add_argument("model", help="Model name with vendor prefix, e.g. openrouter:google/gemma-4-31b-it:free")
    parser.add_argument("--save-usage", action="store_true",
                        help="Record usage to usage.jsonl regardless of the model "
                             "(OpenAI models are always recorded)")
    args = parser.parse_args(argv)

    # same rule as docs/20260924-usage-log.md: record metered OpenAI models by default
    usage_path = None
    if args.model.startswith(("openai:", "gpt-")) or args.save_usage:
        usage_path = find_usage_file()

    # show_params off: the model is shown once at startup instead of on every turn
    chat(Client(model=args.model, show_params=False), usage_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
