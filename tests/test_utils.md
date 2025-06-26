# test_utils.py - Utility Functions Tests

Unit tests for helper functions in `llm7shi/utils.py`.

## Test Coverage

### Parameter Display Tests
- `do_show_params()` parameter display formatting with keyword-only arguments
- Output to stdout vs file handling (file=None disables output)
- Parameter alignment and formatting consistency
- Content quoting and string representation
- Temperature parameter display via **kwargs
- Configuration object display via **kwargs
- File output redirection and validation using print() internally

### Message Conversion Tests
- `contents_to_openai_messages()` message format conversion
- Conversion without system prompt (user messages only)
- Conversion with system prompt (system + user messages)
- Empty content list handling
- Single content item processing
- Empty system prompt handling (falsy values excluded)

### Schema Modification Tests
- `add_additional_properties_false()` schema modification for OpenAI compatibility
- Simple object schema property addition
- Recursive processing for nested object structures
- Array handling with object items
- Non-object schema preservation (no modification)
- Existing additionalProperties override behavior
- Deeply nested schema structure processing

### Schema Reference Resolution Tests
- `inline_defs()` JSON schema reference resolution
- Simple `$ref` inlining with definition replacement
- Nested reference resolution (refs within refs)
- Array items reference inlining
- Schema without definitions (no-op behavior)
- Unused definitions removal
- Title field removal during inlining process
- Circular reference detection (raises `RecursionError` in current implementation)

## Mock Strategy

### Output Mocking
- Mock `sys.stdout` for output capture and validation
- File object mocking for output redirection testing (via MagicMock)
- String content verification and formatting validation
- Mock file.write() calls to verify print() behavior

### Test Data
- Various content types: strings, lists, mixed content
- Schema examples: simple objects, nested structures, arrays
- Reference schemas: simple refs, nested refs, circular refs
- Edge cases: empty inputs, malformed data, boundary conditions

## Test Classes

- **TestDoShowParams**: Parameter display and formatting
- **TestContentsToOpenaiMessages**: Message format conversion
- **TestAddAdditionalPropertiesFalse**: OpenAI schema compatibility
- **TestInlineDefs**: JSON schema reference resolution

## Key Test Scenarios

### Parameter Display
- Console vs file output comparison
- Parameter value formatting and alignment
- Content string quoting and escaping
- Multiple parameter combinations

### Message Conversion
- OpenAI message format compliance
- System prompt integration strategies
- Content list processing and validation
- Role assignment and message structure

### Schema Processing
- OpenAI compatibility requirements
- Reference resolution accuracy
- Recursive processing validation
- Edge case handling and error prevention

## Running Tests

```bash
# Run all utility function tests
uv run pytest tests/test_utils.py

# Run specific test class
uv run pytest tests/test_utils.py::TestDoShowParams

# Run with verbose output
uv run pytest tests/test_utils.py -v
```