# test_schema1.py - JSON Schema Generation Test

## Purpose

This test validates the JSON schema-based structured output functionality demonstrated in `examples/schema1.py`, including both validated and direct JSON usage approaches.

## Test Coverage

### `test_schema1_example()`
Tests the complete schema1.py workflow:
- **Schema Loading**: Loads and validates `schema1.json` using `build_schema_from_json()`
- **Config Creation**: Creates proper generation configuration from schema
- **Structured Output**: Verifies JSON response generation with schema constraints
- **Response Validation**: Confirms Response object contains schema-related metadata
- **API Integration**: Tests the full pipeline from schema to API call

### `test_schema1_direct_json_usage()`
Tests the alternative approach mentioned in comments:
- **Direct JSON**: Uses raw JSON dict without `build_schema_from_json()` validation
- **Compatibility**: Ensures `config_from_schema()` accepts both validated and raw schemas
- **Functionality**: Confirms that validation is optional but the feature still works

### `test_schema1_validation()`
Tests the early error detection benefits of `build_schema_from_json()`:
- **Valid Schema**: Confirms that well-formed schemas are processed correctly
- **Invalid Schema**: Verifies that malformed schemas raise appropriate errors
- **Error Messages**: Tests that validation catches unsupported schema types

## Mock Strategy

- **API Key**: Sets `GEMINI_API_KEY=dummy` for credential-free testing
- **JSON Response**: Simulates structured JSON output matching the temperature conversion schema
- **Stream Chunks**: Breaks JSON response into realistic streaming chunks
- **Schema File**: Loads actual `examples/schema1.json` for authentic testing

## Test Data

### Input
```
"The temperature in Tokyo is 90 degrees Fahrenheit."
```

### Expected Output
```json
{"locations_and_temperatures": [{"location": "Tokyo", "temperature": 32.22}]}
```

This tests the AI's ability to:
- Extract location information ("Tokyo")
- Convert temperature units (90°F → 32.22°C)
- Structure data according to schema

## Schema Validation Testing

Tests both positive and negative cases:
- **Valid Schema**: Standard JSON Schema with object/array/string/number types
- **Invalid Schema**: Schema with unsupported type to trigger validation error

## Benefits

- **Schema Compliance**: Ensures generated JSON matches expected structure
- **Validation Coverage**: Tests both optional and required validation paths
- **Error Handling**: Verifies early error detection capabilities
- **Real Data**: Uses actual schema file from examples for authenticity
- **Production Simulation**: Tests error conditions that could occur in real usage