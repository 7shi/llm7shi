# Tests

This directory contains pytest tests for llm7shi library modules and functionality. All tests use mocked API calls to avoid requiring real API keys or making network requests.

## Test Structure

Tests are organized by module to provide comprehensive unit test coverage:

### Core Module Tests

#### [test_gemini.py](test_gemini.py) - Gemini API Module Tests
Unit tests for the core Gemini API wrapper functionality in `llm7shi/gemini.py`.

**Documentation**: [test_gemini.md](test_gemini.md)

**Key Features**: Response dataclass, schema building, content generation with retry logic, file operations, thinking process extraction.

#### [test_utils.py](test_utils.py) - Utility Functions Tests
Unit tests for helper functions in `llm7shi/utils.py`.

**Documentation**: [test_utils.md](test_utils.md)

**Key Features**: Parameter display, OpenAI message conversion.

#### [test_utils_schema.py](test_utils_schema.py) - Schema Processing Tests
Unit tests for schema transformation functions in `llm7shi/utils.py`.

**Documentation**: [test_utils_schema.md](test_utils_schema.md)

**Key Features**: Schema modification for OpenAI compatibility, reference resolution and inlining, circular reference handling.

#### [test_utils_descriptions.py](test_utils_descriptions.py) - Schema Description Processing Tests
Unit tests for schema description extraction and prompt generation functions in `llm7shi/utils.py`.

**Documentation**: [test_utils_descriptions.md](test_utils_descriptions.md)

**Key Features**: Description extraction from JSON schemas and Pydantic models, cross-provider prompt generation, multi-provider consistency validation.

#### [test_monitor_repetition.py](test_monitor_repetition.py) - Repetition Detection Tests
Unit tests for the `detect_repetition()` function in `llm7shi/monitor.py`.

**Documentation**: [test_monitor_repetition.md](test_monitor_repetition.md)

**Key Features**: Pattern detection algorithms, threshold validation, edge case handling, LLM loop prevention.

#### [test_compat.py](test_compat.py) - Multi-Provider Compatibility Tests
Unit tests for the compatibility layer in `llm7shi/compat.py`.

**Documentation**: [test_compat.md](test_compat.md)

**Key Features**: Model selection, multi-provider generation, schema processing, error handling.

#### [test_compat_vendor.py](test_compat_vendor.py) - Vendor Prefix Routing Tests
Unit tests for vendor prefix functionality in `llm7shi/compat.py`.

**Documentation**: [test_compat_vendor.md](test_compat_vendor.md)

**Key Features**: Vendor prefix parsing, backward compatibility, default model delegation, error boundary validation.

#### [test_terminal.py](test_terminal.py) - Terminal Formatting Tests
Unit tests for terminal output formatting in `llm7shi/terminal.py`.

**Documentation**: [test_terminal.md](test_terminal.md)

**Key Features**: Bold formatting, markdown conversion, streaming processing, Windows compatibility.

## Running Tests

Execute all tests with:

```bash
uv run pytest
```

### Test Options

```bash
# Run with verbose output
uv run pytest -v

# Run specific test module
uv run pytest tests/test_gemini.py

# Run specific test class
uv run pytest tests/test_gemini.py::TestResponse

# Run specific test function
uv run pytest tests/test_gemini.py::TestResponse::test_response_init

# Run with coverage report
uv run pytest --cov=llm7shi

# Run tests matching a pattern
uv run pytest -k "schema"
```

## Test Strategy

### Mock Implementation
- **No API Calls**: Most tests use `unittest.mock.patch` to mock API clients and methods
- **Dummy Credentials**: API tests set `GEMINI_API_KEY=dummy` and `OPENAI_API_KEY=dummy` to avoid requiring real API keys
- **Realistic Responses**: Mock data simulates actual API response patterns for Gemini, OpenAI, and Ollama
- **Pure I/O Testing**: Terminal formatting tests use actual colorama output without mocking for realistic validation
- **Isolated Testing**: Complete separation from external dependencies

### Mock Patterns
- **Gemini API**: Mock `genai.Client` and `client.models.generate_content_stream()`
- **OpenAI API**: Mock `openai.OpenAI` and `client.chat.completions.create()`
- **Ollama API**: Mock `ollama.chat()` function for local model interactions
- **File Operations**: Mock file upload/delete operations and processing state polling
- **Environment Variables**: Use `monkeypatch.setenv()` for API key setup
- **Streaming Responses**: `MockChunk` class simulates realistic streaming chunks

### Test Organization
Tests are organized by functionality within each module:

1. **Class-based Testing**: Related tests grouped into test classes (e.g., `TestResponse`, `TestSchemaBuilding`)
2. **Comprehensive Coverage**: Each public function and method has dedicated test cases
3. **Edge Case Testing**: Error conditions, empty inputs, malformed data, and boundary conditions
4. **Parameter Validation**: All function parameters and their combinations are tested
5. **State Management**: Streaming converters and stateful objects are thoroughly tested

## Benefits

- **Fast Execution**: No network delays or API quota consumption
- **Reliable Results**: Consistent behavior regardless of API availability
- **Development Workflow**: Enable test-driven development without external dependencies
- **CI/CD Ready**: Tests can run in any environment without API credentials
- **Modular Coverage**: Each module can be tested independently
- **Regression Prevention**: Comprehensive unit tests catch breaking changes early

## Test Structure

Each test file follows a consistent pattern:

1. **Imports**: Module-specific imports and test utilities
2. **Mock Classes**: Reusable mock objects (e.g., `MockChunk` for API responses)
3. **Fixtures**: Shared test setup (e.g., `set_dummy_api_key`)
4. **Test Classes**: Grouped by functionality for better organization
5. **Test Methods**: Individual test cases with descriptive names
6. **Assertions**: Comprehensive validation of outputs and side effects

### Test Naming Convention
- Test files: `test_{module_name}.py`
- Test classes: `Test{ClassName}` or `Test{FunctionGroup}`
- Test methods: `test_{specific_functionality}`

All tests are designed to be independent, fast, and provide comprehensive coverage of the library's functionality without requiring external API access.