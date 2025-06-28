# compat1.py - Multi-Provider JSON Schema Example

## Why This Example Exists

This example demonstrates that structured output can be provider-independent using standard JSON Schema.

### Schema Portability Across Providers
**Problem**: Different LLM providers have incompatible schema requirements and formats, making structured output applications provider-specific and difficult to migrate.

**Solution**: Shows how the same JSON Schema file can work with multiple providers, with the compatibility layer automatically handling provider-specific schema format requirements behind the scenes.

### Transparent Schema Conversion
**Problem**: OpenAI requires `additionalProperties: false` and other specific schema modifications, while Gemini has different format requirements. Managing these differences manually is error-prone.

**Solution**: Demonstrates automatic schema transformation that preserves the semantic meaning while meeting each provider's specific technical requirements, making structured output truly portable.