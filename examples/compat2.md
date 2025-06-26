# compat2.py - Multi-Provider Pydantic Schema Example

## Overview

This example demonstrates structured output generation using Pydantic models with both Gemini and OpenAI models. It's the compatibility version of `schema2.py`.

## Code Explanation

```python
from typing import List
from pydantic import BaseModel, Field
from llm7shi.compat import generate_with_schema

class LocationTemperature(BaseModel):
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]

generate_with_schema(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    schema=LocationsAndTemperatures,
    model="gemini-2.5-flash",
)
print("=" * 40)
generate_with_schema(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    schema=LocationsAndTemperatures,
    model="gpt-4.1-mini",
)
```

### Key Components

1. **Pydantic Models**: Type-safe schema definition with Python classes
2. **Nested Structure**: `LocationsAndTemperatures` contains a list of `LocationTemperature`
3. **Field Descriptions**: `Field()` provides metadata for better AI understanding
4. **Direct Model Usage**: Pass Pydantic class directly as schema

### Differences from schema2.py

- **Original (`schema2.py`)**: Uses Gemini-specific:
  - `config_from_schema(LocationsAndTemperatures)`
  - `generate_content_retry()`
- **Compatibility (`compat2.py`)**: Uses unified `generate_with_schema()` that automatically handles Pydantic models

## Pydantic Models

### LocationTemperature
```python
class LocationTemperature(BaseModel):
    location: str
    temperature: float = Field(description="Temperature in Celsius")
```
- `location`: String field for place name
- `temperature`: Float field with description for unit clarity

### LocationsAndTemperatures
```python
class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]
```
- Container model with a list of location-temperature pairs
- Allows multiple locations in a single response

## Expected Output

Both models will:
1. Parse the natural language input
2. Convert 90°F to approximately 32.2°C
3. Return JSON matching the Pydantic structure:

```json
{"locations_and_temperatures": [{"location": "Tokyo", "temperature": 32.2}]}
```

## Usage

Run this example with:

```bash
uv run examples/compat2.py
```

## Environment Requirements

Ensure both API keys are set:

```bash
export GEMINI_API_KEY="your-gemini-key"
export OPENAI_API_KEY="your-openai-key"
```

## Features Demonstrated

- **Pydantic Integration**: Direct use of Pydantic models as schemas
- **Automatic Conversion**: The compatibility layer handles:
  - Converting Pydantic to JSON schema
  - Inlining `$defs` references
  - Adding OpenAI-required fields
- **Type Safety**: Python type hints ensure correct data structures
- **Provider Agnostic**: Same models work with both APIs

## Technical Details

The compatibility layer automatically:
- Calls `model_json_schema()` on Pydantic models
- Processes `$defs` references with `inline_defs()`
- Adds `additionalProperties: false` for OpenAI
- Handles format differences between providers

## Advantages of Pydantic

1. **Type Validation**: Automatic validation of response data
2. **IDE Support**: Autocomplete and type checking
3. **Documentation**: Docstrings and field descriptions
4. **Reusability**: Models can be used throughout your application
5. **Serialization**: Easy conversion to/from JSON

## Use Cases

- **API Development**: Define response models once, use everywhere
- **Data Validation**: Ensure LLM outputs match expected format
- **Type-Safe Systems**: Integrate with typed Python codebases
- **Schema Evolution**: Easy to update and version models

## Related Examples

- `schema2.py`: Original Gemini-only version
- `compat1.py`: JSON schema example
- `compat0.py`: Plain text generation example