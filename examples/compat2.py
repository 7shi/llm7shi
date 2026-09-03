"""
Pydantic models face the same cross-provider schema incompatibilities as raw
JSON Schema (OpenAI rejecting $defs refs, additionalProperties requirements,
etc.); the compat layer converts them transparently so one model definition
works across all three backends. The description-enhancement pattern from
compat1.py applies unchanged to Pydantic models too. See also: compat1.py.
"""

import argparse
from typing import List
from pydantic import BaseModel, Field
from llm7shi.compat import generate_with_schema
from llm7shi import create_json_descriptions_prompt
from args import parse_model_args

args = parse_model_args(argparse.ArgumentParser(description=__doc__))

class LocationTemperature(BaseModel):
    reasoning: str
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]

# Ollama ignores schema `description` fields; fold them into the prompt so they aren't dropped
json_descriptions = create_json_descriptions_prompt(LocationsAndTemperatures)

generate_with_schema(
    ["The temperature in Tokyo is 90 degrees Fahrenheit.", json_descriptions],
    schema=LocationsAndTemperatures,
    model=args.model,
)
