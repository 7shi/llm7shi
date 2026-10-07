"""List the models a provider offers, to pick a value for the `model` argument.

Run with: uv run llm7shi models openrouter [--free]
"""
import argparse
import json
import urllib.request

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Non-text input modalities, abbreviated to one letter each in a fixed order so
# the column lines up regardless of how the API happens to order the list.
_INPUT_ABBREV = [("image", "i"), ("file", "f"), ("audio", "a"), ("video", "v")]

_OPENROUTER_HEADER = ("ID", "CONTEXT", "MAX_OUT", "IN$/M", "OUT$/M", "INPUT", "THINK", "TOOLS", "JSON", "EXPIRES")


def fetch_openrouter_models(url: str = OPENROUTER_MODELS_URL) -> list[dict]:
    """Fetch the public model list (no API key needed)."""
    # fetched on every run: the free tier changes week to week, so a cached copy goes
    # stale; urllib rather than requests to avoid a dependency for a single GET
    with urllib.request.urlopen(url) as res:
        return json.load(res)["data"]


def _tokens(n) -> str:
    if n is None:
        return "-"
    for unit in (1_000_000, 1 << 20):  # providers use both 1M and 1MiB contexts
        if n >= unit and n % unit == 0:
            return f"{n // unit}M"
    if n >= 1000:
        return f"{round(n / 1000)}K"
    return str(n)


def _price(per_token) -> str:
    if per_token is None:
        return "-"
    p = float(per_token)
    if p < 0:
        return "var"  # routers such as openrouter/auto bill per the model they pick
    if p == 0:
        return "0"
    return f"{p * 1_000_000:.2f}"


def _inputs(model: dict) -> str:
    mods = model.get("architecture", {}).get("input_modalities") or []
    return "".join(c for name, c in _INPUT_ABBREV if name in mods) or "-"


def _think(model: dict) -> str:
    """Whether the model reasons, and whether include_thoughts=False can stop it.

    The compat layer maps include_thoughts=False to reasoning.enabled=False, which
    mandatory-reasoning models ignore; that is the case worth flagging.
    """
    if "reasoning" not in (model.get("supported_parameters") or []):
        return "-"
    info = model.get("reasoning") or {}
    if info.get("mandatory"):
        return "must"  # reasoning.enabled=False is ignored, so it always thinks
    return "on" if info.get("default_enabled") else "opt"


def _openrouter_row(model: dict) -> tuple[str, ...]:
    params = model.get("supported_parameters") or []
    pricing = model.get("pricing") or {}
    return (
        model["id"],
        _tokens(model.get("context_length")),
        _tokens((model.get("top_provider") or {}).get("max_completion_tokens")),
        _price(pricing.get("prompt")),
        _price(pricing.get("completion")),
        _inputs(model),
        _think(model),
        "yes" if "tools" in params else "-",
        # structured_outputs means json_schema is enforced; response_format alone may only be
        # JSON mode, so schema= output is not guaranteed to match
        "schema" if "structured_outputs" in params else "mode" if "response_format" in params else "-",
        model.get("expiration_date") or "-",  # free/preview models are retired on a schedule
    )


def format_openrouter_models(models: list[dict], free: bool = False) -> str:
    if free:
        models = [m for m in models if m["id"].endswith(":free")]
    rows = [_OPENROUTER_HEADER] + [_openrouter_row(m) for m in sorted(models, key=lambda m: m["id"])]
    widths = [max(len(r[i]) for r in rows) for i in range(len(_OPENROUTER_HEADER))]
    # left-align the text columns (ID, INPUT, THINK, TOOLS, JSON, EXPIRES), right-align numbers
    left = {0, 5, 6, 7, 8, 9}
    lines = []
    for r in rows:
        cells = [c.ljust(w) if i in left else c.rjust(w) for i, (c, w) in enumerate(zip(r, widths))]
        lines.append("  ".join(cells).rstrip())
    return "\n".join(lines)


def main(argv: list[str] | None = None, prog: str | None = None) -> int:
    parser = argparse.ArgumentParser(prog=prog, description="List the models a provider offers")
    # one subparser per provider: listing options such as --free are provider-specific
    sub = parser.add_subparsers(dest="provider", required=True, metavar="<provider>")

    openrouter = sub.add_parser(
        "openrouter",
        help="List OpenRouter models sorted by ID",
        description="List OpenRouter models sorted by ID. Prices are USD per 1M tokens. "
                    "INPUT: non-text inputs (i=image f=file a=audio v=video). "
                    "THINK: must=always reasons, on=reasons by default, opt=reasons when "
                    "enabled, -=no reasoning. JSON: schema=structured outputs, "
                    "mode=JSON mode only.",
    )
    openrouter.add_argument("--free", action="store_true", help="Only show models whose ID ends with ':free'")

    args = parser.parse_args(argv)

    if args.provider == "openrouter":
        print(format_openrouter_models(fetch_openrouter_models(), free=args.free))
        return 0

    parser.error(f"unknown provider: {args.provider}")  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
