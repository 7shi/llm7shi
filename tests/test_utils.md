# test_utils.py - Utility Functions Tests

## Why These Tests Exist

Testing utility functions required addressing specific cross-cutting concerns:

### Parameter Display Testing
**Problem**: The `do_show_params()` function needed to handle various output scenarios (console, file, disabled) while maintaining consistent formatting. This seemingly simple function had complex behavior around alignment and quoting.

**Solution**: Comprehensive mocking of `sys.stdout` and file objects to verify exact output formatting and ensure the function respects the `file=None` disable mechanism.

### Message Format Conversion Testing
**Problem**: Converting between different LLM provider message formats required ensuring no content is lost and proper role assignment occurs. The `contents_to_openai_messages()` function bridges different API paradigms.

**Solution**: Tests covering various content combinations and system prompt scenarios to verify format compliance and data integrity.