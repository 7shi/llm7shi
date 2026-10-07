"""Check whether include_thoughts=False actually stops Gemini's thinking.

Compares thoughts_token_count across:
  - llm7shi generate_with_schema(include_thoughts=True/False)
  - raw google-genai calls: no config / include_thoughts=False / thinking_budget=0

Usage (from the llm7shi repo, GEMINI_API_KEY set):
  uv run python docs/20261007-disable-thinking/check_gemini_thinking.py [-m gemini-3.8-flash] [-m gemini-2.5-flash]
"""

import argparse
import io
import os

from google import genai
from google.genai import types

from llm7shi.compat import generate_with_schema

PROMPT = "What is 17 * 23? Answer with the number only."

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", action="append", help="Gemini model (repeatable)")
args = parser.parse_args()
models = args.model or ["gemini-3.8-flash", "gemini-2.5-flash"]


def show(label, um):
    if um is None:
        print(f"  {label:32} usage: none")
        return
    print(f"  {label:32} thoughts={um.get('thoughts_token_count')} "
          f"candidates={um.get('candidates_token_count')} total={um.get('total_token_count')}")


client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def raw_call(model, config):
    response = client.models.generate_content(model=model, contents=PROMPT, config=config)
    um = response.usage_metadata
    return um.model_dump(exclude_none=True) if um else None


for model in models:
    print(f"=== {model} ===")

    # llm7shi path (output suppressed; only usage is shown)
    for include_thoughts in [True, False]:
        try:
            r = generate_with_schema([PROMPT], model=f"google:{model}",
                                     include_thoughts=include_thoughts,
                                     show_params=False, file=io.StringIO())
            show(f"llm7shi include_thoughts={include_thoughts}", r.usage.raw if r.usage else None)
        except Exception as e:
            print(f"  llm7shi include_thoughts={include_thoughts}: {e}")

    # raw google-genai variants
    variants = {
        "raw: no config": None,
        "raw: include_thoughts=False": types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(include_thoughts=False)),
        "raw: thinking_budget=0": types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)),
        "raw: thinking_level=MINIMAL": types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL)),
        "raw: thinking_level=LOW": types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW)),
    }
    for label, config in variants.items():
        try:
            show(label, raw_call(model, config))
        except Exception as e:
            print(f"  {label:32} error: {e}")
