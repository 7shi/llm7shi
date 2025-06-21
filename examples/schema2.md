# schema2.py - Pydantic Schema Example

## Overview

This example demonstrates how to use Pydantic models to generate structured data output from Gemini AI models, providing type-safe JSON parsing and validation.

## What is Pydantic?

Pydantic is a Python library that uses type hints to validate data and provide serialization/deserialization. It's widely used in modern Python applications for:

- **Data Validation**: Automatically validates input data against type definitions
- **Type Safety**: Catches type errors at runtime and provides IDE support
- **JSON Schema Generation**: Automatically creates JSON schemas from Python classes
- **API Development**: Popular in FastAPI and other web frameworks
- **Configuration Management**: Type-safe configuration parsing

Key benefits:
- Write Python classes with type hints instead of manual JSON schemas
- Get automatic validation, serialization, and documentation
- Better IDE support with auto-completion and type checking

## Code Explanation

```python
from typing import List
from pydantic import BaseModel, Field
from llm7shi import config_from_schema, generate_content_retry

class LocationTemperature(BaseModel):
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]

generate_content_retry(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    config=config_from_schema(LocationsAndTemperatures),
)
```

### Key Components

1. **Pydantic Models**: Define data structure using Python classes with type hints
2. **Direct Model Usage**: `config_from_schema()` accepts Pydantic models directly
3. **Simplified Workflow**: No need for manual schema conversion or validation

### Advantages over Raw JSON Schema

- **Type Safety**: Compile-time type checking with IDEs
- **Auto-completion**: Better developer experience
- **Validation**: Automatic data validation and error reporting
- **Documentation**: Self-documenting code through type hints
- **Maintainability**: Easier to refactor and maintain

## Pydantic Model Definition

```python
class LocationTemperature(BaseModel):
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]
```

### Model Features

- **Type Hints**: Python native typing for better IDE support
- **Field Descriptions**: Provide context for AI understanding
- **Nested Models**: Compose complex structures from simple components
- **Validation**: Automatic type checking and data validation

## Schema Processing

The `config_from_schema()` function can accept Pydantic models directly, automatically handling the schema conversion internally. This eliminates the need for manual JSON schema generation and provides a cleaner API.

## Expected Output

The AI generates structured JSON output matching the Pydantic model definition:

```
- model : gemini-2.5-flash

> The temperature in Tokyo is 90 degrees Fahrenheit.

💡 Answer:

{"locations_and_temperatures": [{"location": "Tokyo", "temperature": 32.22}]}
```

## Usage

Run this example with:

```bash
uv run examples/schema2.py
```

## Use Cases

- **Simple Schema Definition**: Define schemas using familiar Python syntax
- **Type Safety**: Better IDE support with type hints and auto-completion
- **Complex Schemas**: Handle nested and complex data structures easily
- **Maintainable Code**: Self-documenting schemas through Python classes
- **Integration**: Seamless integration with FastAPI and other frameworks

## Comparison with schema1.py

| Feature | schema1.py | schema2.py |
|---------|------------|------------|
| Schema Definition | Manual JSON | Pydantic models |
| Code Complexity | Medium | Simple |
| IDE Support | Limited | Full auto-completion |
| Type Safety | Runtime only | Compile-time hints |
| Maintainability | Good | Excellent |
| Learning Curve | Simple | Moderate |

## Related Functions

- `BaseModel`: Pydantic base class for defining data models
- `Field()`: Define field constraints and descriptions
- `config_from_schema()`: Create generation config from Pydantic model or JSON schema
- `generate_content_retry()`: Main generation function with schema support