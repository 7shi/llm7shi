# test_schema2.py - Pydantic Schema Integration Test

## Purpose

This test validates the Pydantic model integration demonstrated in `examples/schema2.py`, testing both the simplified API usage and type-safe data handling capabilities.

## Test Coverage

### `test_schema2_example()`
Tests the complete schema2.py workflow:
- **Direct Model Usage**: Passes Pydantic model directly to `config_from_schema()`
- **Type-Safe Generation**: Generates structured JSON from Pydantic model definition
- **Response Parsing**: Validates that generated JSON can be parsed back into Pydantic objects
- **Field Validation**: Confirms that Pydantic validation works on the response
- **Simplified API**: Tests the streamlined approach compared to manual JSON schemas

### `test_pydantic_model_schema_generation()`
Tests the internal schema generation:
- **Model Acceptance**: Verifies `config_from_schema()` accepts Pydantic models directly
- **Nested Models**: Tests both individual and composite model configurations
- **Schema Conversion**: Ensures Pydantic models are properly converted to Gemini schemas

### `test_pydantic_model_validation()`
Tests Pydantic's built-in validation capabilities:
- **Individual Models**: Validates single `LocationTemperature` objects
- **Nested Structures**: Tests `LocationsAndTemperatures` with arrays
- **JSON Parsing**: Confirms `model_validate_json()` works with generated responses
- **Type Safety**: Ensures proper type checking and data integrity

### `test_pydantic_field_description()`
Tests preservation of schema metadata:
- **Field Descriptions**: Verifies that `Field(description=...)` information is maintained
- **Schema Generation**: Confirms metadata flows through to final schema
- **AI Context**: Ensures descriptions are available for AI understanding

## Mock Strategy

- **API Key**: Uses `GEMINI_API_KEY=dummy` for authentication-free testing
- **JSON Response**: Simulates the same temperature conversion output as schema1
- **Type Safety**: Tests both generation and parsing phases of the workflow
- **Model Definitions**: Uses actual Pydantic models from schema2.py example

## Test Data

### Pydantic Models
```python
class LocationTemperature(BaseModel):
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]
```

### Input/Output
Same as schema1 test but with additional type-safe parsing validation.

## Validation Testing

Tests multiple levels of Pydantic validation:
- **Constructor Validation**: Direct object creation with dict data
- **JSON Validation**: Parsing JSON strings into typed objects
- **Nested Validation**: Arrays of typed objects
- **Field Constraints**: Description preservation and accessibility

## Benefits

- **Type Safety**: Ensures compile-time and runtime type checking
- **Developer Experience**: Tests the improved ergonomics of Pydantic vs raw JSON
- **Validation Depth**: Covers both generation and parsing phases
- **Production Ready**: Tests error handling and edge cases
- **API Simplification**: Validates the streamlined approach without manual schema conversion
- **IDE Support**: Confirms that type hints enable better development tooling