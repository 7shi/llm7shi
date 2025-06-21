# schema.py - Structured JSON Output Example

## Overview

This example demonstrates how to use JSON schemas to generate structured data output from Gemini AI models, converting natural language into well-defined JSON format.

## Code Explanation

```python
import json
from pathlib import Path
from llm7shi import build_schema_from_json, config_from_schema, generate_content_retry

with open(Path(__file__).with_suffix(".json")) as f:
    schema = build_schema_from_json(json.load(f))

generate_content_retry(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    config=config_from_schema(schema),
)
```

### Key Components

1. **Schema Loading**: Loads `schema.json` and converts it using `build_schema_from_json()`
2. **Configuration**: `config_from_schema()` creates a generation config from the Gemini schema
3. **Structured Input**: Natural language text that contains data to be extracted
4. **Structured Output**: AI returns properly formatted JSON matching the schema

## Schema Definition (schema.json)

```json
{
  "type": "object",
  "properties": {
    "locations_and_temperatures": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string"
          },
          "temperature": {
            "type": "number",
            "description": "Temperature in Celsius"
          }
        },
        "required": ["location", "temperature"]
      }
    }
  }
}
```

### Schema Features

- **Object Structure**: Defines the expected JSON object shape
- **Array Support**: Handles multiple location-temperature pairs
- **Type Validation**: Ensures correct data types (string, number)
- **Required Fields**: Specifies mandatory properties
- **Descriptions**: Provides context for AI understanding

## Expected Output

The AI will:
1. Parse the natural language input ("Tokyo is 90 degrees Fahrenheit")
2. Convert Fahrenheit to Celsius (90°F → 32.2°C)
3. Return structured JSON:

```json
{
  "locations_and_temperatures": [
    {
      "location": "Tokyo",
      "temperature": 32.2
    }
  ]
}
```

## Usage

Run this example with:

```bash
uv run examples/schema.py
```

## Use Cases

- **Data Extraction**: Extract structured information from unstructured text
- **Format Conversion**: Convert between different data representations
- **API Integration**: Generate API-ready JSON from natural language
- **Database Population**: Structure data for database insertion

## Related Functions

- `build_schema_from_json(json_data)`: Convert JSON schema to Gemini Schema object
- `config_from_schema(schema)`: Create generation config from Gemini schema
- `generate_content_retry()`: Main generation function with schema support