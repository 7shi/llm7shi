# test_compat_vendor.py - Vendor Prefix Routing Tests

## Why These Tests Exist

The vendor prefix feature required dedicated testing to ensure robust multi-provider routing without breaking existing functionality:

### Vendor Prefix Parsing Validation
**Problem**: The new vendor prefix format (`"openai:model"`, `"google:model"`) needed reliable parsing logic that could handle edge cases like empty prefixes, unknown vendors, and malformed input without affecting system stability.

**Solution**: Comprehensive tests covering regex-based parsing (`([^:]+):(.*)`) to verify correct vendor identification and model name extraction across all supported patterns and error conditions.

### Backward Compatibility Assurance
**Problem**: Existing code using legacy model names (`"gpt-4o-mini"`, `"gemini-2.5-flash"`) must continue working seamlessly after vendor prefix introduction, requiring validation that the fallback detection logic works correctly.

**Solution**: Specific tests ensuring legacy patterns are correctly identified and routed to appropriate providers without requiring code changes in existing applications.

### Default Model Delegation Testing
**Problem**: Empty vendor prefixes (`"openai:"`, `"google:"`) should delegate to each provider's default model system, but this delegation needed verification to ensure the empty string correctly triggers default model selection.

**Solution**: Tests validating that empty model names are passed through to underlying providers where existing default model logic can handle them appropriately.

### Error Boundary Validation
**Problem**: Unknown vendor prefixes (`"unknown:model"`) should fail fast with clear error messages rather than silently defaulting to unexpected providers, preventing user confusion and debugging difficulties.

**Solution**: Exception testing to verify that unsupported vendor prefixes raise `ValueError` with descriptive messages, maintaining predictable behavior for invalid input.

### Provider Routing Isolation
**Problem**: The vendor prefix logic needed testing in isolation from the full API integration to ensure routing decisions were made correctly regardless of underlying provider behavior or availability.

**Solution**: Mock-based testing approach that focuses purely on routing logic validation, separating vendor prefix parsing concerns from actual API interaction testing covered in the main test suite.