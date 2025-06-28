# schema1.py - Structured JSON Output Example

## Why This Example Exists

This example addresses the need for structured data extraction from LLM outputs using standard JSON Schema.

### Standard JSON Schema Approach
**Problem**: Natural language outputs from LLMs are hard to parse and integrate into applications. Developers needed a way to get predictable, structured data using existing JSON Schema standards.

**Solution**: Uses standard JSON Schema files with validation to ensure LLM outputs match expected structure, enabling reliable data extraction and integration.

### Early Error Detection Philosophy
**Problem**: Schema errors often surface during API calls, wasting time and tokens. The example shows the recommended pattern of early schema validation.

**Solution**: Demonstrates `build_schema_from_json()` for validation at load time versus direct JSON usage, catching schema issues before expensive API calls.