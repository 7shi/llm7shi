"""
Same JSON Schema file works unmodified across Gemini, OpenAI, and Ollama: the
compat layer handles each provider's schema quirks (e.g. OpenAI's
additionalProperties: false) transparently. Also demonstrates
create_json_descriptions_prompt() working around Ollama silently ignoring
schema `description` fields (verified via qwen3:4b failing a required
Fahrenheit-to-Celsius conversion without it). See also: compat0.py, compat2.py.
"""

import argparse
import json
from pathlib import Path
from llm7shi.compat import generate_with_schema
from llm7shi import create_json_descriptions_prompt
from args import parse_model_args

args = parse_model_args(argparse.ArgumentParser(description=__doc__))

with open(Path(__file__).parent / "schema1.json") as f:
    schema = json.load(f)

# Ollama ignores schema `description` fields; fold them into the prompt so they aren't dropped
json_descriptions = create_json_descriptions_prompt(schema)

generate_with_schema(
    ["The temperature in Tokyo is 90 degrees Fahrenheit.", json_descriptions],
    schema=schema,
    model=args.model,
)
