# gemini.py - Gemini API Client

This module provides a simplified interface for interacting with Google's Gemini API, including automatic retry logic, streaming support, and structured output generation.

## Core Components

### Response Class

A dataclass that encapsulates all generation results:

```python
@dataclass
class Response:
    model: Optional[str] = None
    config: Optional[types.GenerateContentConfig] = None
    contents: Optional[List[Any]] = None
    response: Optional[Any] = None  # Raw API response
    chunks: List[Any] = field(default_factory=list)
    thoughts: str = ""
    text: str = ""
    
    def __str__(self) -> str:
        """Return the text content when converting to string."""
        return self.text
    
    def __repr__(self) -> str:
        """Return a concise representation."""
        # Shows truncated contents and text
```

**Attributes:**
- `model`: The model used for generation
- `config`: GenerateContentConfig used
- `contents`: Input contents sent to the API
- `response`: Raw API response object
- `chunks`: All streaming chunks received
- `thoughts`: Thinking process text (if `include_thoughts=True`)
- `text`: Final generated text

### Available Models

```python
models = ["gemini-2.5-flash", "gemini-2.5-pro"]
DEFAULT_MODEL = models[0]  # gemini-2.5-flash
```

### Default Configuration

```python
# Plain text responses
config_text = types.GenerateContentConfig(
    response_mime_type="text/plain",
)
```

## Main Functions

### generate_content_retry()

Main generation function with automatic retry logic:

```python
response = generate_content_retry(
    contents,                  # Content to send
    model=None,                # Model name (uses DEFAULT_MODEL if None)
    config=None,               # GenerateContentConfig object
    include_thoughts=True,     # Include thinking process
    thinking_budget=None,      # Optional thinking time limit
    file=sys.stdout,           # Output stream (None to disable)
    show_params=True,          # Display parameters before generation
    max_length=None            # Maximum length of generated text
)
```

**Features:**
- Automatic retry for API errors (429, 500, 502, 503)
- Streaming output with real-time markdown formatting
- Thinking process visualization for Gemini 2.5 models
- Flexible output control (stdout, file, or silent)
- Length limitation with `max_length` parameter

**Return Value:** `Response` object containing all generation data

### build_schema_from_json()

Convert JSON schema to Gemini Schema object:

```python
json_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "active": {"type": "boolean"}
    },
    "required": ["name"]
}

schema = build_schema_from_json(json_schema)
```

**Supported Types:**
- `object`: With properties and required fields
- `string`: With optional enum values
- `boolean`: True/false values
- `number`: Floating point numbers
- `integer`: Whole numbers
- `array`: With typed items

### config_from_schema()

Create GenerateContentConfig for structured JSON output:

```python
config = config_from_schema(schema)
# Returns config with response_mime_type="application/json"
```

### upload_file()

Upload files to Gemini API:

```python
file = upload_file("image.jpg", "image/jpeg")

# Use in contents
contents = [{
    "role": "user",
    "parts": [
        {"text": "Describe this image"},
        {"fileData": {
            "mimeType": file.mime_type,
            "fileUri": file.uri
        }}
    ]
}]
```

**Supported MIME Types:**
- Images: `image/jpeg`, `image/png`, `image/gif`, `image/webp`
- Documents: `application/pdf`, `text/plain`
- Audio: `audio/mpeg`, `audio/wav`
- Video: `video/mp4`

### delete_file()

Delete uploaded files:

```python
delete_file(file)
```

## Usage Examples

### Basic Text Generation

```python
from llm7shi import generate_content_retry

# Simple generation
response = generate_content_retry(["Hello, World!"])
print(response.text)

# With specific model
response = generate_content_retry(
    ["Explain quantum computing"],
    model="gemini-2.5-pro"
)
```

### Structured Output with Schema

```python
from llm7shi import build_schema_from_json, config_from_schema

# Define schema
schema_dict = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "sentiment": {
            "type": "string",
            "enum": ["positive", "negative", "neutral"]
        },
        "score": {"type": "number"}
    },
    "required": ["summary", "sentiment", "score"]
}

# Build config
schema = build_schema_from_json(schema_dict)
config = config_from_schema(schema)

# Generate structured output
response = generate_content_retry(
    ["Analyze this text: Great product!"],
    config=config
)

import json
result = json.loads(response.text)
print(f"Sentiment: {result['sentiment']}")
```

### Thinking Process Visualization

```python
# Enable thinking display
response = generate_content_retry(
    ["Solve: What is 25% of 80?"],
    include_thoughts=True
)

print(f"Thoughts: {response.thoughts}")
print(f"Answer: {response.text}")

# Limit thinking time
response = generate_content_retry(
    ["Complex problem..."],
    thinking_budget=30  # Max 30 seconds thinking
)
```

### Output Control

```python
# Silent mode (no output)
response = generate_content_retry(contents, file=None)

# Output to file
with open("output.txt", "w", encoding="utf-8") as f:
    response = generate_content_retry(contents, file=f)

# Disable parameter display
response = generate_content_retry(
    contents,
    show_params=False  # Don't show model/prompt info
)

# Limit output length
response = generate_content_retry(
    contents,
    max_length=500  # Stop generation at 500 characters
)
```

### Error Handling and Retry

The function automatically retries on these errors:
- **429**: Rate limit (waits based on retryDelay)
- **500**: Server error (15 second wait)
- **502**: Bad Gateway (15 second wait)
- **503**: Service unavailable (15 second wait)

```python
try:
    response = generate_content_retry(contents)
except RuntimeError as e:
    print(f"Max retries exceeded: {e}")
```

## Environment Setup

Set your API key:
```bash
export GEMINI_API_KEY="your-api-key"
```

## Integration with utils.py

The module uses `do_show_params()` from utils.py for parameter display:

```python
from llm7shi.utils import do_show_params

# Called internally when show_params=True
do_show_params(contents, model=model, file=file)
```

## Terminal Formatting

Uses `MarkdownStreamConverter` for real-time markdown formatting:
- Bold text (`**text**`) converted to terminal colors
- Thinking process shown with 🤔 emoji
- Answer shown with 💡 emoji

## Notes

1. **Default Model**: Uses `gemini-2.5-flash` when model is not specified
2. **Streaming**: Always uses streaming API for real-time output
3. **File Processing**: Uploaded files wait for processing completion
4. **Rate Limiting**: Automatic retry with appropriate delays
5. **Thinking Feature**: Available on both Flash and Pro models
