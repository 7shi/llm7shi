"""Check whether include_thoughts=False actually stops reasoning on OpenRouter.

Compares completion_tokens_details.reasoning_tokens (and the length of any
returned reasoning text) across:
  - llm7shi generate_with_schema(include_thoughts=True/False)
    (True sends reasoning.enabled=True, False sends reasoning.enabled=False)
  - raw Chat Completions calls with various `reasoning` objects:
    none / enabled=False / enabled=True / exclude=True / effort=none / max_tokens=0

`exclude=True` is the earlier disable attempt that only hid the reasoning; if
the counts work, it should show reasoning tokens with no reasoning text.

Each variant runs -n times, since reasoning varies between calls.

Usage (from the llm7shi repo, OPENROUTER_API_KEY set):
  uv run python docs/20261007-disable-thinking/check_openrouter_thinking.py -m nvidia/nemotron-3-super-120b-a12b:free [-m ...] [-n 3]
"""

import argparse
import io
import os

from openai import OpenAI

from llm7shi.compat import generate_with_schema

PROMPT = "What is 17 * 23? Answer with the number only."

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", action="append", required=True,
                    help="OpenRouter model id, e.g. minimax/minimax-m3:free (repeatable)")
parser.add_argument("-n", type=int, default=3, help="calls per variant")
args = parser.parse_args()

client = OpenAI(base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"])


def run(label, call):
    results = []
    for _ in range(args.n):
        try:
            results.append(call())
        except Exception as e:
            print(f"  {label:34} error: {e}")
            return
    print(f"  {label:34} " + "  ".join(f"{r}/{t}" for r, t in results))


def llm7shi_call(model, include_thoughts):
    def call():
        r = generate_with_schema([PROMPT], model=f"openrouter:{model}",
                                 include_thoughts=include_thoughts,
                                 show_params=False, file=io.StringIO())
        tokens = r.usage.reasoning_tokens if r.usage else "?"
        return tokens, len(r.thoughts or "")
    return call


def raw_call(model, reasoning):
    def call():
        extra_body = {"reasoning": reasoning} if reasoning is not None else None
        r = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": PROMPT}],
            extra_body=extra_body)
        details = r.usage.completion_tokens_details if r.usage else None
        tokens = getattr(details, "reasoning_tokens", None) if details else "?"
        message = r.choices[0].message
        text = getattr(message, "reasoning", None) or getattr(message, "reasoning_content", None) or ""
        return tokens, len(text)
    return call


print("each cell: reasoning_tokens/reasoning text length")
for model in args.model:
    print(f"=== {model} ===")
    for include_thoughts in [True, False]:
        run(f"llm7shi include_thoughts={include_thoughts}", llm7shi_call(model, include_thoughts))
    variants = {
        "raw: no reasoning param": None,
        "raw: enabled=False": {"enabled": False},
        "raw: enabled=True": {"enabled": True},
        "raw: exclude=True": {"exclude": True},
        "raw: effort=none": {"effort": "none"},
        "raw: max_tokens=0": {"max_tokens": 0},
    }
    for label, reasoning in variants.items():
        run(label, raw_call(model, reasoning))
