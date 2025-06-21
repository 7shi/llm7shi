# test_hello.py - Basic Text Generation Test

## Purpose

This test validates the basic text generation functionality demonstrated in `examples/hello.py` without making actual API calls to the Gemini service.

## Test Coverage

### `test_hello_example()`
Tests the core functionality of the hello.py example:
- **Mock Setup**: Uses dummy API key and mocked `generate_content_stream`
- **Response Structure**: Verifies that `generate_content_retry()` returns a proper Response object with all expected attributes
- **Content Validation**: Confirms that streamed text chunks are properly concatenated
- **API Call Verification**: Ensures the correct parameters are passed to the underlying API call
- **Model Configuration**: Validates that the default model (`gemini-2.5-flash`) is used

## Mock Strategy

- **API Key**: Sets `GEMINI_API_KEY=dummy` to avoid requiring real credentials
- **Stream Response**: Creates mock chunks that simulate the streaming response from Gemini
- **No Network**: Completely isolates the test from external dependencies

## Test Data

The test simulates a typical greeting response:
```
"Hello there! A classic greeting.\n\nHow can I help you today?"
```

This matches the expected conversational output format from Gemini models.

## Assertions

- Response object contains all required fields (`text`, `thoughts`, `model`, `chunks`)
- Text content matches expected concatenated output
- Model is correctly set to default
- Number of chunks matches mock data
- API call arguments are properly passed through

## Benefits

- **Fast Execution**: No network delays or API quotas
- **Reliable**: Consistent results regardless of API availability
- **Isolated**: Tests only the library's functionality, not Gemini's responses
- **Development**: Enables TDD workflow without external dependencies