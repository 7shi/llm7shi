# test_compat_vendor.py - Vendor Prefix Routing Tests

## Why These Tests Exist

The vendor prefix feature required dedicated testing to ensure robust multi-provider routing without breaking existing functionality:

### Vendor Prefix Parsing Validation
**Problem**: The new vendor prefix format (`"openai:model"`, `"google:model"`, `"ollama:model"`) needed reliable parsing logic that could handle edge cases like empty prefixes, unknown vendors, and malformed input without affecting system stability.

**Solution**: Comprehensive tests covering regex-based parsing (`([^:]+):(.*)`) to verify correct vendor identification and model name extraction across all supported patterns and error conditions.

### Backward Compatibility Assurance
**Problem**: Existing code using legacy model names (`"gpt-4.1-mini"`, `"gemini-2.5-flash"`) must continue working seamlessly after vendor prefix introduction, requiring validation that the fallback detection logic works correctly.

**Solution**: Specific tests ensuring legacy patterns are correctly identified and routed to appropriate providers without requiring code changes in existing applications.

### Default Model Delegation Testing
**Problem**: Empty vendor prefixes (`"openai:"`, `"google:"`, `"ollama:"`) should delegate to each provider's default model system, but this delegation needed verification to ensure the empty string correctly triggers default model selection.

**Solution**: Tests validating that empty model names are passed through to underlying providers where existing default model logic can handle them appropriately.

### Error Boundary Validation
**Problem**: Unknown vendor prefixes (`"unknown:model"`) should fail fast with clear error messages rather than silently defaulting to unexpected providers, preventing user confusion and debugging difficulties.

**Solution**: Exception testing to verify that unsupported vendor prefixes raise `ValueError` with descriptive messages, maintaining predictable behavior for invalid input.

### Provider Routing Isolation
**Problem**: The vendor prefix logic needed testing in isolation from the full API integration to ensure routing decisions were made correctly regardless of underlying provider behavior or availability.

**Solution**: Mock-based testing approach that focuses purely on routing logic validation, separating vendor prefix parsing concerns from actual API interaction testing covered in the main test suite.

### Base URL and API Key Environment Variable Parsing
**Problem**: The extended syntax `model@base_url|api_key_env` required comprehensive testing to ensure correct parsing across various URL formats, environment variable names, and edge cases without breaking existing `model@base_url` syntax.

**Solution**: Dedicated test class `TestBaseUrlAndApiKeyEnvParsing` with six test scenarios:

1. **Basic base_url-only syntax**: Validates `model@base_url` without `api_key_env` correctly sets `api_key_env=None`
2. **Full syntax with pipe delimiter**: Verifies `model@base_url|api_key_env` correctly extracts both components
3. **No custom endpoint**: Confirms models without `@` syntax pass `None` for both parameters
4. **URLs with ports and colons**: Tests parsing robustness with complex URLs like `http://192.168.0.8:8080/v1`
5. **Empty api_key_env**: Validates `model@base_url|` correctly handles trailing pipe with empty string
6. **Environment variable naming**: Ensures support for realistic env var names with underscores and numbers

**Why this matters**: The pipe delimiter syntax enables secure custom endpoint usage by allowing explicit environment variable specification while maintaining backward compatibility with the simpler `@base_url` format. These tests ensure the parsing logic handles real-world URL formats and environment variable naming conventions correctly.