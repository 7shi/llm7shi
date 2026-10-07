"""Check whether include_thoughts=False actually stops OpenAI's reasoning.

Compares output_tokens_details.reasoning_tokens across:
  - llm7shi generate_with_schema(include_thoughts=True/False)
    (run from the llm7shi repo so its local source is used; with the pre-fix
    openai.py, False sends no reasoning param)
  - raw Responses API calls: no reasoning param (llm7shi's behavior before the fix)
    / effort none / minimal / low

Each variant runs -n times, since reasoning varies between calls.

Usage (from the llm7shi repo, OPENAI_API_KEY set):
  uv run python docs/20261007-disable-thinking/check_openai_thinking.py [-m gpt-6-luna] [-m gpt-5.6-luna] [-n 3]
"""

import argparse
import io

from openai import OpenAI

from llm7shi.compat import generate_with_schema

PROMPT = "What is 17 * 23? Answer with the number only."

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", action="append", help="OpenAI model (repeatable)")
parser.add_argument("-n", type=int, default=3, help="calls per variant")
args = parser.parse_args()
models = args.model or ["gpt-6-luna"]

client = OpenAI()


def reasoning_tokens(usage: dict | None):
    if not usage:
        return "?"
    details = usage.get("output_tokens_details") or {}
    return details.get("reasoning_tokens")


def run(label, call):
    counts = []
    for _ in range(args.n):
        try:
            counts.append(call())
        except Exception as e:
            print(f"  {label:32} error: {e}")
            return
    print(f"  {label:32} reasoning={counts}")


def llm7shi_call(model, include_thoughts):
    def call():
        r = generate_with_schema([PROMPT], model=f"openai:{model}",
                                 include_thoughts=include_thoughts,
                                 show_params=False, file=io.StringIO())
        return r.usage.reasoning_tokens if r.usage else "?"
    return call


def raw_call(model, reasoning):
    def call():
        kwargs = {"reasoning": reasoning} if reasoning is not None else {}
        r = client.responses.create(model=model, input=PROMPT, **kwargs)
        return reasoning_tokens(r.usage.model_dump() if r.usage else None)
    return call


for model in models:
    print(f"=== {model} ===")
    for include_thoughts in [True, False]:
        run(f"llm7shi include_thoughts={include_thoughts}", llm7shi_call(model, include_thoughts))
    variants = {
        "raw: no reasoning param": None,
        "raw: effort=none": {"effort": "none"},
        "raw: effort=minimal": {"effort": "minimal"},
        "raw: effort=low": {"effort": "low"},
    }
    for label, reasoning in variants.items():
        run(label, raw_call(model, reasoning))
