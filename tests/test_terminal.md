# test_terminal.py - Terminal Formatting Tests

Unit tests for terminal output formatting in `llm7shi/terminal.py`.

## Test Coverage

### Bold Function Tests
- `bold()` simple text formatting with colorama styles
- Empty string handling and edge cases
- Special character processing (newlines, symbols)
- Color code application and reset sequences

### Markdown Conversion Tests
- `convert_markdown()` one-shot markdown to terminal conversion
- Single bold section conversion (`**text**` → colored text)
- Multiple bold sections in single string
- Bold text at string start, middle, and end
- Entirely bold text handling
- Plain text without formatting (pass-through)
- Empty string and edge case handling

### Unclosed Formatting Tests
- Unclosed bold markers (`**text` without closing `**`)
- Empty bold markers (`****`)
- Only asterisks handling
- Malformed markup graceful degradation

### Newline and Multiline Tests
- Bold text spanning multiple lines
- Mixed content with newlines between bold sections
- Newline preservation in formatted output
- Complex multiline scenarios

### Streaming Converter Tests
- `MarkdownStreamConverter` initialization and state management
- Complete bold formatting in single chunk processing
- Bold formatting split across multiple chunks
- Opening marker split across chunks (`*` + `*bold content**`)
- Closing marker split across chunks (`**bold content*` + `*`)
- Multiple bold sections in streaming context

### Buffer Management Tests
- Partial marker buffering and state tracking
- Buffer content management and cleanup
- Bold state persistence across feed operations
- Non-matching continuation handling (buffer flush)

### Auto-closing Behavior Tests
- Newline auto-closing of bold formatting
- Newlines within properly closed bold sections
- `flush()` method with pending content processing
- End-of-stream bold completion

### Streaming State Tests
- Bold state tracking (`bright_mode` flag, not `bold_open`)
- Buffer management for incomplete markers
- State persistence across multiple `feed()` calls
- Complex streaming scenarios with multiple partial updates
- Proper attribute name usage matching actual implementation

### Windows Console Integration Tests
- Windows console compatibility verification
- Module import success validation
- Cross-platform behavior validation

## Test Strategy

### Pure Input/Output Testing
- Tests actual colorama ANSI escape sequences without mocking
- Focuses on content preservation and functionality verification
- Validates that markdown markers are properly removed
- Checks for presence of expected text content rather than exact formatting codes

### Test Data
- Various markdown patterns: simple, complex, nested, malformed
- Streaming chunk scenarios: complete, partial, split markers
- Edge cases: empty strings, only asterisks, very long text
- Realistic streaming scenarios with multiple chunks
- Pure functional testing without dependency on internal colorama constants

## Test Classes

- **TestBoldFunction**: Simple bold text formatting
- **TestConvertMarkdown**: One-shot markdown conversion
- **TestMarkdownStreamConverter**: Streaming conversion functionality
- **TestWindowsConsoleIntegration**: Platform compatibility
- **TestEdgeCases**: Error conditions and boundary cases

## Key Test Scenarios

### Basic Functionality
- Bold text wrapping with ANSI escape sequences
- Markdown pattern recognition and replacement
- Plain text pass-through behavior
- Correct `convert_markdown()` behavior for unclosed markers
- Content preservation in all formatting operations

### Streaming Processing
- Incremental chunk processing with state management
- Partial marker handling across chunk boundaries
- Auto-closing behavior for incomplete formatting
- Buffer management for single asterisk at chunk boundaries

### Edge Case Handling
- Malformed markdown graceful degradation (immediate processing)
- Very long text processing efficiency
- Nested marker pattern handling with proper state transitions
- Single asterisk buffering at chunk boundaries

### Platform Compatibility
- Windows console initialization verification
- Cross-platform ANSI escape sequence consistency
- Module import success across platforms

## Running Tests

```bash
# Run all terminal formatting tests
uv run pytest tests/test_terminal.py

# Run specific test class
uv run pytest tests/test_terminal.py::TestMarkdownStreamConverter

# Run with verbose output
uv run pytest tests/test_terminal.py -v
```