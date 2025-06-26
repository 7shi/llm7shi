# test_gemini.py - Gemini API Module Tests

Unit tests for the core Gemini API wrapper functionality in `llm7shi/gemini.py`.

## Test Coverage

### Response Dataclass Tests
- `Response` initialization with default values (`None` for optional fields)
- String representation (`__str__` returns text content)
- Repr representation shows condensed contents and text
- Data structure integrity and field validation

### Schema Building Tests
- `build_schema_from_json()` for all supported schema types:
  - Object schemas with properties and required fields
  - String schemas with enum values
  - Array schemas with item definitions
  - Primitive types (boolean, number, integer)
- Error handling for unsupported schema types with `ValueError`
- Nested schema structures and complex configurations

### Configuration Tests
- `config_from_schema()` returns `GenerateContentConfig` object
- Configuration includes `response_schema` and `response_mime_type`
- Proper integration with Gemini API types

### Content Generation Tests
- `generate_content_retry()` with various parameters and error conditions
- Basic text generation with default and custom models
- Thinking budget parameter handling and validation
- Configuration parameter passing and integration (with `GenerateContentConfig`)
- Thinking process extraction from streaming responses
- Custom model parameter validation

### Retry Logic Tests
- API error handling (429, 500, 502, 503) using `genai.errors.APIError`
- Proper error object initialization with message and `response_json` parameters
- Error object structure with `code` attribute and error details
- Retry attempt counting and success after retry
- Error propagation for non-retryable errors
- Mock stderr output suppression during error testing

### File Operations Tests
- File upload with `UploadFileConfig` object structure
- Processing state polling (`PROCESSING` → `ACTIVE`) with wait logic
- File deletion operations requiring file object with `name` attribute
- Error handling for file operation failures
- Proper parameter structure verification for upload calls

### Backward Compatibility Tests
- Legacy function wrapper validation
- Parameter forwarding to new implementations
- Response object compatibility

## Mock Strategy

### API Mocking
- Mock `genai.Client` and `client.models.generate_content_stream()`
- Mock file operations (`client.files.upload`, `client.files.get`, `client.files.delete`)
- Mock time delays (`time.sleep`) for retry logic testing
- Mock `genai.errors.APIError` for proper error handling testing
- Mock `builtins.print` to suppress stderr output during error testing

### Test Data
- `MockChunk` class simulates realistic Gemini API streaming responses
- Support for both regular text and thinking process chunks
- Configurable chunk content and metadata
- Realistic error objects with proper initialization (`message`, `response_json`) and `code` attributes

### Environment Setup
- Automatic dummy API key setup (`GEMINI_API_KEY=dummy`)
- Isolated test environment without external dependencies
- Proper Google GenAI types integration for configuration testing

## Test Classes

- **TestResponse**: Dataclass functionality and representations
- **TestSchemaBuilding**: Schema conversion and validation
- **TestGenerateContentRetry**: Main generation function testing
- **TestFileOperations**: File upload/delete functionality
- **TestBackwardCompatibility**: Legacy function support

## Running Tests

```bash
# Run all Gemini module tests
uv run pytest tests/test_gemini.py

# Run specific test class
uv run pytest tests/test_gemini.py::TestResponse

# Run with verbose output
uv run pytest tests/test_gemini.py -v
```