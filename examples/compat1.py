import json
from pathlib import Path
from llm7shi.compat import generate_with_schema
from llm7shi import create_json_descriptions_prompt

with open(Path(__file__).parent / "schema1.json") as f:
    schema = json.load(f)

# Create enhanced prompt with field descriptions
json_descriptions = create_json_descriptions_prompt(schema)

generate_with_schema(
    ["The temperature in Tokyo is 90 degrees Fahrenheit.", json_descriptions],
    schema=schema,
    model="ollama:",
)
