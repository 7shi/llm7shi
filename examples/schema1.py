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
