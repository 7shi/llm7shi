# test_utils.py - Utility Functions Tests

## Why These Tests Exist

Testing utility functions required addressing specific cross-cutting concerns:

### Parameter Display Testing
**Problem**: The `do_show_params()` function needed to handle various output scenarios (console, file, disabled) while maintaining consistent formatting. This seemingly simple function had complex behavior around alignment and quoting.

**Solution**: Comprehensive mocking of `sys.stdout` and file objects to verify exact output formatting and ensure the function respects the `file=None` disable mechanism.

### Schema Transformation Validation
**Problem**: The schema processing functions (`add_additional_properties_false`, `inline_defs`) perform complex recursive transformations that must preserve schema semantics while meeting API-specific requirements. These transformations are critical for multi-provider compatibility.

**Solution**: Extensive test cases covering nested structures, arrays, and edge cases to ensure transformations don't break schema validity or lose information.

### Message Format Conversion Testing
**Problem**: Converting between different LLM provider message formats required ensuring no content is lost and proper role assignment occurs. The `contents_to_openai_messages()` function bridges different API paradigms.

**Solution**: Tests covering various content combinations and system prompt scenarios to verify format compliance and data integrity.

### Circular Reference Handling
**Problem**: JSON schemas can contain circular references, which the `inline_defs()` function needs to detect to avoid infinite loops during processing.

**Solution**: Explicit tests for circular reference detection to ensure the function fails gracefully with `RecursionError` rather than hanging indefinitely.