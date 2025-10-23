# test_gpt_oss.py - gpt-oss Template Filter Tests

## Why These Tests Exist

Testing the gpt-oss template filter required comprehensive coverage of control token parsing, channel routing, and filter activation logic to ensure reliable separation of reasoning process from final output.

### Control Token Parsing Validation
**Problem**: The gpt-oss template uses control tokens (`<|channel|>`, `<|message|>`, `<|start|>`, `<|end|>`) that can arrive split across multiple stream chunks, making parsing fragile and error-prone.

**Solution**: Created systematic tests covering:
- Basic channel switching between `analysis` and `final` channels
- Control tokens split across chunk boundaries
- Partial role names buffered across chunks
- Empty chunks that should be handled gracefully

### Channel-Based Content Routing
**Problem**: The filter must correctly route content to different destinations (`thoughts` vs `text` properties) based on the active channel, with complex state management for channel switches.

**Solution**: Tests verify that:
- `analysis` channel content goes to `thoughts` property only
- `final` channel content goes to both `text` property and display output
- Content without explicit channel defaults to `text` (backward compatibility)
- Channel switches preserve accumulated content

### Role Token Filtering
**Problem**: The `<|start|>` token is followed by role names (`assistant`, `user`, `system`) that must be detected and discarded without appearing in output.

**Solution**: Implemented tests for:
- Complete role names in single chunks
- Partial role names split across chunks
- Multiple different role types
- Invalid role names handled gracefully

### Filter Activation Logic
**Problem**: The filter should activate only for the exact model name `"llama.cpp/gpt-oss"` to avoid false positives with other models that might contain similar substrings in their names.

**Solution**: Created dedicated test class `TestFilterActivation` with:
- **Positive test**: `test_filter_activates_for_llama_cpp_gpt_oss` - Verifies filter activates for exact match
- **Negative test 1**: `test_filter_does_not_activate_for_other_models` - Ensures `"gpt-oss:120b"` does NOT activate filter
- **Negative test 2**: `test_filter_does_not_activate_for_standard_models` - Ensures standard OpenAI models work without filter

**Design Context**: Since llama-server ignores the model name parameter and provides only one model at a time, the model name `"llama.cpp/gpt-oss"` serves as a client-side template identifier. The exact match requirement prevents accidental filter activation for models with similar names.

### Mock Integration Testing
**Problem**: The filter integrates with `openai.py`'s `generate_content()` function, requiring proper mocking of the OpenAI client to test end-to-end behavior without real API calls.

**Solution**: Tests use `@patch('llm7shi.openai.OpenAI')` to mock the OpenAI class constructor, returning a mock client instance. This approach:
- Supports the dynamic client creation pattern (no global singleton)
- Enables testing of custom `base_url` parameter handling
- Simulates realistic chunk sequences from gpt-oss template

### Complex Real-World Scenarios
**Problem**: Real gpt-oss output combines multiple control tokens, channel switches, and role markers in complex sequences that simple unit tests might miss.

**Solution**: Created `test_complex_scenario()` that simulates a complete real-world response:
```
<|channel|>analysis<|message|>User asks for greeting. Should respond politely.
<|start|>assistant<|channel|>final<|message|>Hello! How can I help you?
```

This ensures the filter correctly:
1. Routes analysis content to `thoughts`
2. Filters role name after `<|start|>`
3. Routes final content to `text`
4. Produces clean display output without control tokens

### Flush Behavior Validation
**Problem**: When streaming ends, any remaining buffer content must be properly routed to the correct channel without data loss.

**Solution**: `test_flush()` verifies:
- Partial control tokens in buffer are output as literal text
- Content is routed to the active channel
- No data is lost during flush

### Long Content Handling
**Problem**: Real LLM responses can be lengthy, requiring verification that the filter maintains correct behavior over extended content.

**Solution**: `test_long_content()` uses repeated strings (10x repetition) to ensure:
- Large content doesn't break buffering logic
- Channel accumulation works correctly for long text
- No performance degradation or memory issues

## Test Organization

Tests are organized into two categories:

1. **Unit Tests** (12 tests): Test individual filter behaviors in isolation
   - Token parsing
   - Channel routing
   - Role filtering
   - Buffer management

2. **Integration Tests** (3 tests in `TestFilterActivation`): Test filter integration with `openai.py`
   - Filter activation logic
   - End-to-end behavior with mocked API responses
   - Model name matching

This separation ensures both component-level correctness and proper integration with the OpenAI module.
