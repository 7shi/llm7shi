# Tests

This directory contains pytest tests for llm7shi library examples and functionality. All tests use mocked API calls to avoid requiring real Gemini API keys or making network requests.

## Test Files

### [test_hello.py](test_hello.py) - Basic Text Generation Test
Tests the basic text generation functionality from `examples/hello.py`.

**Documentation**: [test_hello.md](test_hello.md)

**Coverage**:
- Response object structure validation
- Text streaming and concatenation
- Default model configuration
- API call parameter verification

### [test_schema1.py](test_schema1.py) - JSON Schema Generation Test
Tests JSON schema-based structured output from `examples/schema1.py`.

**Documentation**: [test_schema1.md](test_schema1.md)

**Coverage**:
- Schema loading and validation with `build_schema_from_json()`
- Direct JSON usage without validation
- Error detection for invalid schemas
- Structured JSON response generation

### [test_schema2.py](test_schema2.py) - Pydantic Schema Integration Test
Tests Pydantic model integration from `examples/schema2.py`.

**Documentation**: [test_schema2.md](test_schema2.md)

**Coverage**:
- Direct Pydantic model usage with `config_from_schema()`
- Type-safe JSON parsing and validation
- Field description preservation
- Simplified API workflow

## Running Tests

Execute all tests with:

```bash
uv run pytest
```

### Test Options

```bash
# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_hello.py

# Run specific test function
uv run pytest tests/test_hello.py::test_hello_example

# Run with coverage report
uv run pytest --cov=llm7shi
```

## Test Strategy

### Mock Implementation
- **No API Calls**: All tests use `unittest.mock.patch` to mock `generate_content_stream`
- **Dummy Credentials**: Tests set `GEMINI_API_KEY=dummy` to avoid requiring real API keys
- **Realistic Responses**: Mock data simulates actual Gemini API response patterns
- **Isolated Testing**: Complete separation from external dependencies

### Test Data
- **Authentic Examples**: Tests use the same inputs and expected outputs as the examples
- **Real Schema Files**: `test_schema1.py` loads actual `examples/schema1.json`
- **Pydantic Models**: `test_schema2.py` uses the same models as `examples/schema2.py`
- **Streaming Simulation**: Mock chunks simulate realistic streaming responses

## Benefits

- **Fast Execution**: No network delays or API quota consumption
- **Reliable Results**: Consistent behavior regardless of API availability
- **Development Workflow**: Enable test-driven development without external dependencies
- **CI/CD Ready**: Tests can run in any environment without API credentials
- **Coverage Validation**: Ensure all example functionality works as expected

## Test Structure

Each test file follows a consistent pattern:
1. **Setup**: Mock API key and patch `generate_content_stream`
2. **Execution**: Run the example code with test inputs
3. **Verification**: Assert response structure, content, and API call parameters
4. **Edge Cases**: Test error conditions and alternative usage patterns

All tests are designed to be independent, fast, and comprehensive in coverage of the library's core functionality.