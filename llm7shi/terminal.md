# terminal.py - Terminal Formatting Utilities

## Overview

A module for converting Markdown bold syntax (`**text**`) to terminal colors using Colorama.
Designed for displaying formatted text in CLI applications with proper handling of streaming output.

## Design Philosophy

### Purpose
Convert Markdown bold notation to terminal formatting for enhanced visual representation in command-line interfaces.

### Key Features

1. **Robustness**: Handles incomplete or malformed markdown gracefully
   - Auto-closes unclosed bold tags at newlines
   - Ensures styles are properly reset at text boundaries

2. **Streaming Support**: Optimized for real-time text processing
   - `MarkdownStreamConverter` class for chunk-by-chunk processing
   - Intelligent buffering to handle split `**` markers across chunks

3. **Cross-Platform Compatibility**: 
   - Windows console support via `just_fix_windows_console()`
   - Consistent line ending normalization (converts CRLF/CR to LF)

### Processing Flow

```
Input: "**bold** text"
     ↓
Parse: Detect ** markers and toggle bold state
     ↓
Apply: Insert Style.BRIGHT/Style.NORMAL codes
     ↓
Output: ANSI-formatted text for terminal display
```

## API Reference

### Functions

#### `bold(text: str) -> str`
Wraps text with terminal bold formatting.

**Parameters:**
- `text`: Text to format as bold

**Returns:**
- Text wrapped with `Style.BRIGHT` and `Style.NORMAL`

**Example:**
```python
print(bold("Important message"))
# Output: Displays "Important message" in bold
```

#### `convert_markdown(text: str) -> str`
Converts Markdown bold syntax to terminal formatting.

**Parameters:**
- `text`: Text containing Markdown bold markers (`**`)

**Returns:**
- Text with Colorama style codes replacing Markdown syntax

**Features:**
- Detects `**` markers and toggles bold state
- Auto-closes bold at newlines to prevent formatting bleed
- Normalizes all line endings to Unix style (LF)
- Ensures proper style reset at text end

**Example:**
```python
text = "This is **important** information\n**Unclosed bold"
print(convert_markdown(text))
# Bold automatically closed at newline and end
```

### Classes

#### `MarkdownStreamConverter`
Handles Markdown bold conversion for streaming text.

**Use Cases:**
- Real-time text streams (e.g., LLM responses)
- Processing large texts in chunks
- Incremental output display

**Attributes:**
- `buffer`: Stores incomplete `**` markers between chunks
- `bright_mode`: Tracks current bold state

**Methods:**

##### `__init__()`
Initializes the converter with empty buffer and normal text state.

##### `feed(chunk: str) -> str`
Processes a chunk of streaming text.

**Parameters:**
- `chunk`: Text fragment to process

**Returns:**
- Formatted text with appropriate style codes

**Behavior:**
- Buffers single `*` at chunk end to detect `**` across boundaries
- Combines buffered content with new chunk before processing
- Auto-closes bold at newlines
- Maintains state between calls

##### `flush() -> str`
Finalizes processing and resets converter state.

**Returns:**
- Any remaining buffered content with proper style closure

**Usage:**
```python
converter = MarkdownStreamConverter()
# Process streaming chunks
for chunk in stream:
    print(converter.feed(chunk), end='')
# Always flush at end
print(converter.flush(), end='')
```

## Usage Examples

### Basic Usage
```python
from terminal import convert_markdown

text = "**Error**: File not found"
print(convert_markdown(text))
```

### Streaming Usage
```python
from terminal import MarkdownStreamConverter

converter = MarkdownStreamConverter()
chunks = ["**Processing", "** in progress", "\nCompleted"]

for chunk in chunks:
    print(converter.feed(chunk), end='')
print(converter.flush())
```

## Limitations

1. **Nested Decorations**: Compound decorations like `***bold italic***` are not supported
2. **Other Markdown**: Headers, lists, code blocks, etc. are not converted
3. **Escaping**: Escaping with `\**` is not supported

## Implementation Details

### Dependencies
- **Colorama**: Provides cross-platform ANSI color support
  - `Style.BRIGHT`: Activates bold formatting
  - `Style.NORMAL`: Resets to normal text
  - `just_fix_windows_console()`: Enables ANSI codes on Windows

### State Management
The `MarkdownStreamConverter` maintains state across chunks:
- **bright_mode**: Boolean flag tracking bold state
  - `False`: Normal text mode
  - `True`: Bold text mode
- **buffer**: String holding incomplete markers
  - Stores single `*` when chunk ends mid-marker
  - Enables proper `**` detection across chunk boundaries