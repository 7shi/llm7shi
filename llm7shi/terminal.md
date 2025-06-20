# terminal.py - Markdown Bold → Terminal Decoration Conversion Module

## Design Philosophy

### Purpose
A utility to visually represent Markdown notation's `**bold**` on the terminal using Colorama.  
Aimed at beautifully displaying Markdown-formatted text in CLI applications.

### Design Principles

1. **Robustness**: Tolerant of malformed formats and unclosed tags
   - Automatically resets style on newline
   - Auto-closes styles at string end

2. **Streaming Support**: Designed for real-time output use
   - Supports chunk-by-chunk processing with `MarkdownStreamConverter`
   - Resolves `*` ambiguity through buffering

3. **Platform Compatibility**: 
   - Executes `just_fix_windows_console()` for Windows
   - Normalizes line endings (CR/CRLF → LF)

### Architecture

```
Input: "**bold** string"
     ↓
Parse: Detect ** and toggle
     ↓
Output: Style.BRIGHT + "bold" + Style.NORMAL + " string"
```

## API Reference

### Functions

#### `bold(text: str) -> str`
Simple bold conversion function.

**Parameters:**
- `text`: String to make bold

**Return value:**
- String wrapped with Colorama style

**Example:**
```python
print(bold("Important message"))
# → Style.BRIGHT + "Important message" + Style.NORMAL
```

#### `convert_markdown(text: str) -> str`
Function to batch convert entire Markdown text.

**Parameters:**
- `text`: Markdown format string (containing `**bold**`)

**Return value:**
- String converted to Colorama styles

**Behavior:**
- Toggles bright_mode on `**` detection
- Automatically resets style on newline
- Auto-closes unclosed styles at string end

**Example:**
```python
text = "This is **important** information\n**Another line**"
print(convert_markdown(text))
```

### Classes

#### `MarkdownStreamConverter`
Markdown conversion class for streaming processing.

**Use cases:**
- Real-time output (e.g., LLM response streams)
- Processing large text in chunks

**Methods:**

##### `__init__()`
Initialize the converter.

**Internal state:**
- `buffer`: Unprocessed characters (mainly trailing `*`)
- `bright_mode`: Current bold mode state

##### `feed(chunk: str) -> str`
Process text chunk and return conversion result.

**Parameters:**
- `chunk`: Text fragment to process

**Return value:**
- Converted text (with Colorama styles)

**Features:**
- Trailing `*` held in buffer (for `**` determination in next chunk)
- Automatic style reset on newline

##### `flush() -> str`
Output remaining buffer and reset state.

**Return value:**
- Characters remaining in buffer with style reset

**Usage example:**
```python
converter = MarkdownStreamConverter()
for chunk in streaming_chunks:
    print(converter.feed(chunk), end='')
print(converter.flush(), end='')  # Required at the end
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

## Technical Details

### Colorama Dependencies
- `Style.BRIGHT`: Start bold
- `Style.NORMAL`: Reset style
- `just_fix_windows_console()`: Ensure Windows compatibility

### State Management
`MarkdownStreamConverter` is implemented as a finite state machine:
- `bright_mode=False`: Normal mode
- `bright_mode=True`: Bold mode
- `buffer`: Pending characters (for resolving `*` ambiguity)