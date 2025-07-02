import json
from pathlib import Path
from llm7shi.compat import generate_with_schema

with open(Path(__file__).parent / "schema1.json") as f:
    schema = json.load(f)

models = [
    "google:gemini-2.5-flash",
    "openai:gpt-4o-mini",
    "ollama:qwen3:4b"
]

for i, model in enumerate(models):
    if i:
        print("", "=" * 60, "", sep="\n")
    generate_with_schema(
        ["The temperature in Tokyo is 90 degrees Fahrenheit."],
        schema=schema,
        model=model,
    )
