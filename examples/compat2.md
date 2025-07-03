# compat2.py - Multi-Provider Pydantic Schema Example

## Why This Example Exists

This example demonstrates the ultimate goal of the compatibility layer - making modern Python development patterns work seamlessly across LLM providers.

### Cross-Provider Pydantic Schema Portability
**Problem**: Pydantic models generate different JSON schemas for different APIs - OpenAI requires `additionalProperties: false` and doesn't support `$defs` references that Pydantic generates, while Gemini and Ollama have their own format requirements.

**Solution**: Demonstrates automatic schema transformation that preserves Pydantic model semantics while meeting each provider's technical requirements. The same Python model definition works across all three backends without modification, with the compatibility layer handling provider-specific schema conversions transparently.

### Pydantic Model Compatibility with Enhancement Patterns
**Problem**: While Pydantic models provide excellent type safety and IDE support, they still face the same cross-provider compatibility challenges as raw JSON schemas when it comes to field description handling.

**Solution**: Shows that the same enhancement techniques used for JSON schemas (see [compat1.md](compat1.md)) work seamlessly with Pydantic models. The `create_json_descriptions_prompt()` function automatically extracts field descriptions from Pydantic models' generated JSON schema, maintaining the benefits of both type-safe development and cross-provider reliability without requiring developers to abandon modern Python patterns.