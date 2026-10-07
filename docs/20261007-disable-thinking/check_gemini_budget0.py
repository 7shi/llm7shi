"""Repeat thinking_budget=0 (and no config for reference) to see if Gemini honors it consistently.

  uv run python docs/20261007-disable-thinking/check_gemini_budget0.py [-m gemini-3.8-flash] [-n 5]
"""

import argparse
import os

from google import genai
from google.genai import types

PROMPT = "What is 17 * 23? Answer with the number only."

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", default="gemini-3.8-flash")
parser.add_argument("-n", type=int, default=5)
args = parser.parse_args()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
variants = {
    "no config": None,
    "thinking_budget=0": types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0)),
}
for label, config in variants.items():
    counts = []
    for _ in range(args.n):
        r = client.models.generate_content(model=args.model, contents=PROMPT, config=config)
        counts.append(r.usage_metadata.thoughts_token_count if r.usage_metadata else "?")
    print(f"{label:20} thoughts={counts}")
