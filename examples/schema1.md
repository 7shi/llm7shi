# schema1.py - Structured JSON Output Example

## Overview

This example demonstrates how to use JSON schemas to generate structured data output from Gemini AI models, converting natural language into well-defined JSON format.

## Code Explanation

```python
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
```

### Key Components

1. **Schema Loading**: Loads `schema1.json` and converts it using `build_schema_from_json()`
2. **Schema Validation**: `build_schema_from_json()` validates the schema for early error detection
3. **Configuration**: `config_from_schema()` creates a generation config from the schema
4. **Structured Input**: Natural language text that contains data to be extracted
5. **Structured Output**: AI returns properly formatted JSON matching the schema

### Alternative Approach

You can skip schema validation and use the JSON directly:

```python
with open(Path(__file__).with_suffix(".json")) as f:
    schema = json.load(f)  # Direct usage without validation
```

However, using `build_schema_from_json()` is recommended because it:
- Validates the schema syntax at load time for early error detection
- Ensures compatibility with Gemini's schema requirements
- Catches schema errors before API calls

## Schema Definition (schema1.json)

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
uv run examples/schema1.py
```

## Use Cases

- **Data Extraction**: Extract structured information from unstructured text
- **Format Conversion**: Convert between different data representations
- **API Integration**: Generate API-ready JSON from natural language
- **Database Population**: Structure data for database insertion

## Related Functions

- `build_schema_from_json(json_data)`: Convert and validate JSON schema to Gemini Schema object
- `config_from_schema(schema)`: Create generation config from JSON schema or Gemini schema
- `generate_content_retry()`: Main generation function with schema support