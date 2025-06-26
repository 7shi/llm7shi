# compat1.py - Multi-Provider JSON Schema Example

## Overview

This example demonstrates structured output generation using JSON schemas with both Gemini and OpenAI models. It's the compatibility version of `schema1.py`.

## Code Explanation

```python
import json
from pathlib import Path
from llm7shi.compat import generate_with_schema

with open(Path(__file__).parent / "schema1.json") as f:
    schema = json.load(f)

generate_with_schema(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    schema=schema,
    model="gemini-2.5-flash",
)
print("=" * 40)
generate_with_schema(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    schema=schema,
    model="gpt-4.1-mini",
)
```

### Key Components

1. **Schema Loading**: Uses the same `schema1.json` file
2. **Unified Interface**: `generate_with_schema()` handles both providers
3. **Structured Output**: Both models return JSON matching the schema
4. **Data Extraction**: Converts natural language to structured data

### Differences from schema1.py

- **Original (`schema1.py`)**: Uses Gemini-specific functions:
  - `build_schema_from_json()`
  - `config_from_schema()`
  - `generate_content_retry()`
- **Compatibility (`compat1.py`)**: Uses unified `generate_with_schema()` with automatic schema handling

## Schema Used (schema1.json)

The example uses the same schema file as `schema1.py`:

```json
{
  "type": "object",
  "properties": {
    "locations_and_temperatures": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "location": {"type": "string"},
          "temperature": {
            "type": "number",
            "description": "Temperature in Celsius"
          }
        },
        "required": ["location", "temperature"]
      }
    }
  },
  "required": ["locations_and_temperatures"]
}
```

## Expected Output

Both models will:
1. Extract "Tokyo" as the location
2. Convert 90°F to approximately 32.2°C
3. Return structured JSON:

```json
{"locations_and_temperatures": [{"location": "Tokyo", "temperature": 32.2}]}
```

The output format will be identical, though exact temperature values may vary slightly between models.

## Usage

Run this example with:

```bash
uv run examples/compat1.py
```

## Environment Requirements

Ensure both API keys are set:

```bash
export GEMINI_API_KEY="your-gemini-key"
export OPENAI_API_KEY="your-openai-key"
```

## Features Demonstrated

- **Schema Portability**: Same JSON schema works with both providers
- **Automatic Conversion**: The compatibility layer handles provider-specific schema requirements
- **Consistent Results**: Both models produce the same JSON structure
- **Temperature Conversion**: Models understand the task and perform calculations

## Technical Details

The compatibility layer automatically:
- Adds `additionalProperties: false` for OpenAI
- Handles schema format differences
- Manages streaming and output formatting
- Preserves the exact schema structure

## Use Cases

- **Multi-Provider Systems**: Use the best model for each task
- **Redundancy**: Fallback to another provider if one fails
- **Cost Optimization**: Route requests based on complexity
- **A/B Testing**: Compare model performance on identical tasks

## Related Examples

- `schema1.py`: Original Gemini-only version
- `compat0.py`: Plain text generation example
- `compat2.py`: Pydantic model example