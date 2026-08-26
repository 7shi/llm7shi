# test_gemini.py - Gemini API Module Tests

## Why These Tests Exist

Testing the Gemini API wrapper required addressing several specific challenges:

### Validating Schema Conversions
**Problem**: The `build_schema_from_json()` function needs to handle various JSON schema types and convert them to Gemini's specific schema format. This conversion is critical for structured output.

**Solution**: Comprehensive tests for all supported schema types (object, string with enums, arrays, primitives) to ensure the conversion preserves semantic meaning.
