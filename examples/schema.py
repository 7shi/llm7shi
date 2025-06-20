from pathlib import Path
from llm7shi import config_from_schema, generate_content_retry

schema = Path(__file__).with_suffix(".json")
generate_content_retry(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    config=config_from_schema(schema),
)
