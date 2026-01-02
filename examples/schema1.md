# schema1.py - Structured JSON Output Example

## Why This Example Exists

This example addresses the need for structured data extraction from LLM outputs using standard JSON Schema.

### Standard JSON Schema Approach
**Problem**: Natural language outputs from LLMs are hard to parse and integrate into applications. Developers needed a way to get predictable, structured data using existing JSON Schema standards.

**Solution**: Uses standard JSON Schema files with validation to ensure LLM outputs match expected structure, enabling reliable data extraction and integration.

### Early Error Detection Philosophy
**Problem**: Schema errors often surface during API calls, wasting time and tokens. The example shows the recommended pattern of early schema validation.

**Solution**: Demonstrates `build_schema_from_json()` for validation at load time versus direct JSON usage, catching schema issues before expensive API calls.

### Reasoning Field for Quality and Debugging
**Problem**: Structured output tasks can fail silently or produce incorrect results without visibility into the model's thought process, making debugging and quality assurance difficult.

**Solution**: Includes a `reasoning` field in the schema that captures the model's step-by-step thought process. This serves multiple purposes: enables debugging of incorrect outputs, improves output quality by encouraging the model to think through the problem, and provides transparency into how the model arrived at its conclusions.

### Item-Level Reasoning Strategy
**Problem**: When processing multiple data items (like multiple locations with temperatures), placing reasoning at the top level creates a disconnect between the thought process and specific item processing, potentially leading to generic or post-hoc explanations.

**Solution**: Positions the `reasoning` field at the item level and as the first property within each item's schema. This "reasoning-first" approach ensures that the model thinks through each item's specific processing requirements before determining the values, leading to more accurate and contextually appropriate results. This structure is particularly important for tasks involving data transformations (like unit conversions) where each item may require different processing logic.