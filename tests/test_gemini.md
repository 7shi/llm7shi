# test_gemini.py - Gemini API Module Tests

## Why These Tests Exist

Testing the Gemini API wrapper required addressing several specific challenges:

### Mocking Complex API Interactions
**Problem**: The Gemini API has complex streaming responses, file operations with state transitions, and specific retry logic for different error codes. Testing this without actual API calls required sophisticated mocking.

**Solution**: Created `MockChunk` classes to simulate realistic streaming responses and comprehensive error objects with proper `code` attributes to test retry logic paths.

### Validating Schema Conversions
**Problem**: The `build_schema_from_json()` function needs to handle various JSON schema types and convert them to Gemini's specific schema format. This conversion is critical for structured output.

**Solution**: Comprehensive tests for all supported schema types (object, string with enums, arrays, primitives) to ensure the conversion preserves semantic meaning.

### Testing File Upload Workflows
**Problem**: Gemini's file API requires upload, wait for processing, then reference in requests. This asynchronous workflow needed testing without real file uploads.

**Solution**: Mocked the state transition from `PROCESSING` to `ACTIVE` and verified proper parameter structures for upload configurations.

### Ensuring Backward Compatibility
**Problem**: As the API evolved, we needed to ensure existing function signatures continued to work while internally using new implementations.

**Solution**: Dedicated tests for legacy function wrappers to verify parameter forwarding and response compatibility.