# terminal.py - Terminal Formatting Utilities

## Why This Exists

When building CLI applications that display LLM responses, we faced several specific challenges that standard terminal output couldn't address:

### Real-Time Markdown Formatting
**Problem**: LLM APIs stream responses with markdown formatting (like `**bold**` text), but terminals need ANSI escape codes for visual formatting. Converting after complete response arrival loses the real-time streaming effect.

**Solution**: Created a streaming converter that processes markdown in chunks as they arrive, maintaining formatting state across chunk boundaries.

### Robustness for Incomplete Text
**Problem**: Streaming text can be cut off mid-markdown marker (e.g., a chunk ending with just `*` when `**` is intended). Standard markdown parsers expect complete text.

**Solution**: Implemented intelligent buffering that holds incomplete markers until the next chunk arrives, plus auto-closing of unclosed formatting at line boundaries.

### Cross-Platform Terminal Support
**Problem**: Windows consoles historically didn't support ANSI escape codes, causing formatting to display as raw escape sequences.

**Solution**: Integrated Colorama's Windows console fixes and normalized line endings across platforms.

## Key Design Decisions

### Streaming-First Architecture
The `MarkdownStreamConverter` class maintains state between `feed()` calls, allowing continuous processing of text streams without losing formatting context.

### Conservative Formatting
Auto-closes bold formatting at newlines to prevent formatting "bleed" into subsequent content. This ensures that unclosed markdown doesn't affect the entire terminal session.

### Minimal Scope
Focused only on bold formatting (`**text**`) rather than full markdown support, as this was the specific need for displaying LLM thinking processes and emphasis.