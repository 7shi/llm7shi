"""
Structured extraction via a standard JSON Schema file (schema1.json), so LLM
output is predictable and parseable instead of free-form text.

schema1.json puts `reasoning` first, at the item level (inside each entry of
locations_and_temperatures, not just once at the top). Item-level placement
forces the model to think through each item's specific conversion (e.g.
Fahrenheit->Celsius) before assigning its value, rather than reasoning once
and applying it generically across items -- important whenever items may need
different per-item processing. See also: schema2.py (same pattern in
Pydantic).
"""

import json
from pathlib import Path
from llm7shi import build_schema_from_json, config_from_schema, generate_content_retry

with open(Path(__file__).with_suffix(".json")) as f:
    # build_schema_from_json() provides schema validation for early error detection
    schema = build_schema_from_json(json.load(f))
    # You can also use json.load(f) directly, but schema validation is recommended
    #schema = json.load(f)

generate_content_retry(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    config=config_from_schema(schema),
)
