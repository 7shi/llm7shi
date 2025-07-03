# compat1.py - Multi-Provider JSON Schema Example

## Why This Example Exists

This example demonstrates that structured output can be provider-independent using standard JSON Schema.

### Schema Portability Across Providers
**Problem**: Different LLM providers have incompatible schema requirements and formats, making structured output applications provider-specific and difficult to migrate.

**Solution**: Shows how the same JSON Schema file can work across cloud providers (Gemini, OpenAI) and local models (Ollama), with the compatibility layer automatically handling provider-specific schema format requirements behind the scenes.

### Transparent Schema Conversion
**Problem**: OpenAI requires `additionalProperties: false` and other specific schema modifications, while Gemini uses different format requirements and Ollama uses the `format` parameter directly. Managing these differences manually is error-prone.

**Solution**: Demonstrates automatic schema transformation that preserves the semantic meaning while meeting each provider's specific technical requirements, making structured output truly portable across all three backends.

### Multi-Provider Schema Description Enhancement
**Problem**: Some providers (particularly Ollama) completely ignore JSON schema `description` fields, leading to inconsistent structured output quality across providers. Testing revealed that models like qwen3:4b would fail to perform required conversions (e.g., Fahrenheit to Celsius) when schema descriptions weren't conveyed.

**Solution**: Demonstrates practical application of `create_json_descriptions_prompt()` for cross-provider compatibility. Shows how the same client-side enhancement technique works uniformly across Gemini, OpenAI, and Ollama backends, ensuring consistent behavior regardless of provider-specific schema handling differences. The implementation pattern shown here can be applied to any multi-provider application requiring reliable structured output.