# test_compat.py - Multi-Provider Compatibility Tests

Unit tests for the compatibility layer in `llm7shi/compat.py`.

## Test Coverage

### Model Selection Logic
- Gemini model routing (`gemini-2.5-flash`, `gemini-2.5-pro`)
- OpenAI model routing (`gpt-4-mini`, `gpt-4o`, etc.)
- Default model selection (falls back to Gemini)
- Unsupported model handling and fallback behavior

### Gemini Integration Tests
- `generate_with_schema()` with Pydantic models and JSON schemas
- Parameter passing to underlying Gemini functions
- Schema processing pipeline (`config_from_schema`, `build_schema_from_json`)
- Temperature parameter handling and validation
- System prompt integration (prepended to content)
- Configuration object creation and validation

### OpenAI Integration Tests
- OpenAI API client initialization and usage
- Message format conversion via `contents_to_openai_messages()`
- Streaming response handling and content extraction
- JSON schema formatting for OpenAI compatibility
- Pydantic model to JSON schema conversion
- Temperature parameter forwarding
- Response format specification for structured output

### Schema Processing Tests
- Pydantic model detection and handling (`inspect.isclass`, `issubclass`)
- JSON schema processing pipeline for OpenAI
- Schema modification (`add_additional_properties_false`)
- Reference inlining (`inline_defs`)
- Schema validation and error handling

### Error Handling Tests
- OpenAI API error propagation
- Unsupported model fallback behavior
- Invalid schema handling
- Network error scenarios

## Mock Strategy

### API Client Mocking
- Mock `openai.OpenAI` client initialization
- Mock `client.chat.completions.create()` for OpenAI responses
- Mock Gemini functions from package root (`llm7shi.generate_content_retry`, `llm7shi.config_from_schema`, etc.)
- Mock environment variables (`GEMINI_API_KEY`, `OPENAI_API_KEY`)
- Note: Uses relative imports in compat.py, requiring root-level mocking

### Response Simulation
- OpenAI response structure simulation with choices and messages
- Gemini response object mocking with proper attributes
- Error response simulation for testing error handling
- Streaming chunk simulation for response processing

### Schema Processing Mocks
- Mock schema processing utilities (`add_additional_properties_false`, `inline_defs`)
- Mock Pydantic model detection and conversion
- Mock JSON schema validation and transformation
- Note: `inline_defs` only called for Pydantic models in current implementation

## Test Classes

- **TestModelSelection**: Model routing and selection logic
- **TestGeminiIntegration**: Gemini API integration and parameter handling
- **TestOpenAIIntegration**: OpenAI API integration and response processing
- **TestErrorHandling**: Error scenarios and fallback behavior
- **TestSchemaProcessing**: Schema conversion and processing utilities

## Test Models

```python
class LocationTemperature(BaseModel):
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationList(BaseModel):
    locations: List[LocationTemperature]
```

Note: Model names avoid "Test" prefix to prevent pytest collection warnings.

## Key Test Scenarios

### Provider Selection
- Model name pattern matching for routing decisions
- Default provider selection when no model specified
- Fallback behavior for unrecognized model names

### Parameter Handling
- Temperature parameter forwarding to both providers
- System prompt integration strategies (positional vs keyword arguments)
- Schema parameter processing and conversion
- Default model selection handling (None passed to Gemini)

### Response Processing
- OpenAI response structure parsing and content extraction
- Gemini response object handling and attribute access
- Error response processing and exception handling
- Streaming response processing for both providers

### Schema Compatibility
- Pydantic model to JSON schema conversion accuracy
- OpenAI schema format requirements and modifications
- Reference resolution and schema flattening (Pydantic only)
- Schema processing pipeline differences between providers

## Running Tests

```bash
# Run all compatibility layer tests
uv run pytest tests/test_compat.py

# Run specific test class
uv run pytest tests/test_compat.py::TestModelSelection

# Run with verbose output
uv run pytest tests/test_compat.py -v
```