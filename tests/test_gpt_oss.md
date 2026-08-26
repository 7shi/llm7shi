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

### Reasoning Stream Extraction
**Problem**: OpenAI-compatible reasoning providers (e.g. OpenRouter) deliver the thinking process in a separate `delta.reasoning` field rather than through gpt-oss control tokens. This path must be captured into `Response.thoughts` independently of the template filter, and must stay inert for providers that never emit the field.

**Solution**: Test class `TestReasoningExtraction` covers:
- **Reasoning separated from content**: chunks carrying `delta.reasoning` accumulate into `thoughts` while `delta.content` accumulates into `text`
- **No reasoning leaves thoughts empty**: standard chunks without `delta.reasoning` leave `thoughts` empty and content flows to `text`

## Test Organization

Tests are organized into the following categories:

1. **Unit Tests** (12 tests): Test individual filter behaviors in isolation
   - Token parsing
   - Channel routing
   - Role filtering
   - Buffer management

2. **Integration Tests** (3 tests in `TestFilterActivation`): Test filter integration with `openai.py`
   - Filter activation logic
   - End-to-end behavior with mocked API responses
   - Model name matching

3. **Reasoning Extraction Tests** (2 tests in `TestReasoningExtraction`): Test `delta.reasoning` capture into `Response.thoughts`, independent of the gpt-oss filter

This separation ensures both component-level correctness and proper integration with the OpenAI module.
