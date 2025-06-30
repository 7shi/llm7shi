# test_compat.py - Multi-Provider Compatibility Tests

## Why These Tests Exist

Testing the compatibility layer required solving unique challenges around multi-provider abstraction:

### Provider Routing Validation
**Problem**: The compatibility layer automatically routes to different APIs based on model names. This routing logic is critical but simple - we needed to ensure it works correctly without over-engineering the detection mechanism.

**Solution**: Focused tests on model name pattern matching and default fallback behavior to verify the simple prefix-based routing works reliably.

### API Abstraction Testing
**Problem**: Each LLM provider has different API patterns, response formats, and parameter requirements. The compatibility layer needed to abstract these differences while preserving provider-specific features.

**Solution**: Comprehensive mocking of both OpenAI and Gemini APIs to test that the same function call produces equivalent `Response` objects regardless of the underlying provider.

### Schema Processing Pipeline Validation
**Problem**: Different providers require different schema formats, and the processing pipeline (Pydantic→JSON→Provider-specific) has multiple transformation steps that could introduce errors.

**Solution**: End-to-end tests that verify schema transformations preserve semantic meaning while meeting each provider's specific format requirements.

### Import and Mocking Complexity
**Problem**: The compat module delegates OpenAI processing to the dedicated `openai.py` module, which uses a global client instance. This required specific mocking strategies to properly intercept API calls without triggering actual OpenAI authentication.

**Solution**: Direct mocking of the global client (`llm7shi.openai.client`) rather than the OpenAI class constructor, ensuring tests work with the modular architecture while avoiding real API calls.