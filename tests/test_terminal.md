# test_terminal.py - Terminal Formatting Tests

## Why These Tests Exist

Testing terminal formatting presented unique challenges for real-time streaming scenarios:

### Streaming State Management Testing
**Problem**: The `MarkdownStreamConverter` maintains state across multiple `feed()` calls and must handle markdown markers split across chunk boundaries. This stateful behavior is complex to test and critical for real-time LLM output.

**Solution**: Comprehensive tests for partial marker scenarios (like `*` at chunk end followed by `*bold**` in next chunk) to ensure the converter properly buffers and reassembles split markers.

### Cross-Platform Compatibility Validation
**Problem**: Terminal formatting works differently on Windows vs Unix systems. The module uses Colorama for cross-platform ANSI support, but this needed verification without requiring multiple test environments.

**Solution**: Integration tests that verify Windows console initialization and module import success, ensuring the formatting works across platforms.

### Graceful Degradation Testing
**Problem**: Real-world markdown input can be malformed (unclosed `**` markers, incomplete formatting). The converter needs to handle these gracefully without breaking or leaving terminals in inconsistent states.

**Solution**: Extensive tests for malformed input patterns and auto-closing behavior at newlines to ensure robust handling of imperfect input.

### Functional vs Implementation Testing
**Problem**: Terminal formatting produces ANSI escape sequences that are hard to test directly. We needed to verify functionality without tightly coupling tests to specific escape sequence values.

**Solution**: Content-focused testing that verifies markdown markers are removed and expected text is preserved, rather than testing exact escape sequence output.

### Inline Code vs Code Fence Disambiguation
**Problem**: A single backtick (`` `code` ``) means inline code, but a run of three or more backticks (` ``` `) means a code fence. Naively toggling on every backtick would corrupt fences, and fences can be split across streaming chunks just like `**`.

**Solution**: Tests cover inline code coloring (with backtick markers removed), fenced blocks rendered with a background (delimiters kept literally, inner `**`/`` ` `` left untouched), the two coexisting in one string, backtick runs split across chunks, and `flush()` closing an unclosed inline span or fenced block. A streaming-vs-one-shot equivalence test guards against divergence between the two code paths.