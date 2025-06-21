# gemini.py - Gemini API Client

## Design Philosophy

### 1. Simple and Intuitive API
Hides the complexity of Google Gemini API and provides a simple, easy-to-use interface. Controls streaming output with the same `file` parameter as the `print` function.

### 2. Transparency of Thinking Process
Leverages Gemini 2.5's thinking capabilities to visualize AI's reasoning process. Allows separate retrieval of thinking process and final answer.

### 3. Robustness and Retry Functionality
Built-in automatic retry functionality for API errors (429, 500, 503). Sets appropriate wait times for rate limiting.

### 4. Flexible Output Control
Supports enabling/disabling streaming output and changing output destinations. Covers a wide range from CLI use to batch processing.

### 5. Schema-based Generation
Supports structured JSON output using JSON schemas. Converts standard JSON schema definitions to Gemini's Schema format for type-safe responses.

## Main Functions

### `generate_content_retry()`
Main function that returns a Response object containing all generation results.

```python
response = generate_content_retry(
    ["question content"],
    model="gemini-2.5-flash",
    config=config_text,
    include_thoughts=True,        # Include thinking process
    thinking_budget=None,         # Thinking time limit (optional)
    file=sys.stdout,             # Output destination (None to disable)
    show_params=True             # Display parameters before generation
)
```

**Return value**: `Response` object with the following attributes:
- `thoughts`: AI's thinking process (str)
- `text`: Final answer (str)
- `response`: Raw API response object
- `chunks`: List of all streaming chunks received
- `model`: The model used for generation
- `config`: The GenerateContentConfig used
- `contents`: The input contents sent to the API

### Response Class
Dataclass that encapsulates all generation results:

```python
@dataclass
class Response:
    model: Optional[str] = None
    config: Optional[types.GenerateContentConfig] = None
    contents: Optional[List[Any]] = None
    response: Optional[Any] = None
    chunks: List[Any] = field(default_factory=list)
    thoughts: str = ""
    text: str = ""
    
    def __str__(self) -> str:
        """Return the text content when converting to string."""
        return self.text
    
    def __repr__(self) -> str:
        """Return a concise representation showing contents and text."""
        # Shows contents[0] and text, truncated at 10 characters
```

### Usage Examples
```python
# Basic usage - Response object
response = generate_content_retry(["Hello, World!"])
print(response.text)  # Access text directly
print(str(response))  # Same as response.text
print(response)       # Shows concise representation

# Access all response data
print(f"Model: {response.model}")
print(f"Thoughts: {response.thoughts}")
print(f"Chunks count: {len(response.chunks)}")

# Backward compatibility - use as string
response = generate_content_retry(["Question"])
result = str(response)  # Get text content
```

## Configuration and Schemas

### Basic Configuration
```python
# For text output
config_text = types.GenerateContentConfig(
    response_mime_type="text/plain",
)

# For JSON output (with schema)
json_schema = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number"}
    },
    "required": ["answer", "confidence"]
}
schema = build_schema_from_json(json_schema)
config_json = config_from_schema(schema)
```

### Schema Functions
```python
# Build Gemini Schema from JSON schema dictionary
json_schema = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number"}
    },
    "required": ["answer", "confidence"]
}
schema = build_schema_from_json(json_schema)

# Create configuration from Schema
config = config_from_schema(schema)
```

### Supported Schema Types
- `object`: With properties and required fields
- `string`: With optional enum values
- `boolean`: Boolean values
- `number`: Floating point numbers
- `integer`: Integer values
- `array`: With typed items

## Output Control

### Standard Output (Default)
```python
response = generate_content_retry(contents, model=model, config=config)
# Thinking process and answer displayed in real-time
print(response.text)  # Access final answer
```

### Disable Output
```python
response = generate_content_retry(contents, model=model, config=config, file=None)
# No screen output, retrieve result only
print(f"Result: {response.text}")
```

### File Output
```python
with open("conversation.txt", "w", encoding="utf-8") as f:
    response = generate_content_retry(contents, model=model, config=config, file=f)
# Save thinking process and answer to file
print(f"Generated {len(response.chunks)} chunks")
```

### Log File Output
```python
import sys
with open("debug.log", "w", encoding="utf-8") as log_file:
    response = generate_content_retry(
        contents, 
        model=model,
        config=config,
        file=log_file  # Record details to log file
    )
    print(f"Result: {response.text}")  # Display only result to console
    print(f"Thinking: {response.thoughts[:100]}...")  # Show thinking summary
```

## Error Handling

### Auto-retry Target Errors
- **429**: Rate limit → Wait according to `retryDelay` from error details (default 15s)
- **500**: Server error → Retry after 15 seconds
- **502**: Bad Gateway → Retry after 15 seconds
- **503**: Service unavailable → Retry after 15 seconds

### Retry Behavior
- Retry up to 5 times
- Set appropriate wait time between attempts
- No wait on final attempt
- `RuntimeError` if all attempts fail

## Utilizing Thinking Features

### Analyzing Thinking Process
```python
response = generate_content_retry(
    contents, model=model, config=config, file=None
)

# Analyze thinking process
if "mathematics" in response.thoughts:
    print("Using mathematical reasoning")
if "step" in response.thoughts.lower():
    print("Executing step-by-step thinking")

print(f"Final answer: {response.text}")
print(f"Used model: {response.model}")
```

### Controlling Thinking Time
```python
# When quick response is needed
response = generate_content_retry(
    contents,
    model=model,
    config=config,
    thinking_budget=30,  # Thinking time within 30 seconds
    file=None
)
print(f"Quick answer: {response.text}")
```

## File Operations

### File Upload
```python
# Upload image file
image_file = upload_file("image.jpg", "image/jpeg")

contents = [
    {"role": "user", "parts": [
        {"text": "Please describe this image"},
        {"fileData": {"mimeType": image_file.mime_type, "fileUri": image_file.uri}}
    ]}
]

response = generate_content_retry(contents, model=model, config=config)
print(f"Image description: {response.text}")

# Delete file after use
delete_file(image_file)
```

### Supported MIME Types
- Images: `image/jpeg`, `image/png`, `image/gif`, `image/webp`
- Documents: `application/pdf`, `text/plain`
- Audio: `audio/mpeg`, `audio/wav`
- Video: `video/mp4`

## Utility Functions

### `do_show_params()`
Display generation parameters for debugging.

```python
do_show_params(["Analyze this file"], model="gemini-2.5-flash", file=sys.stderr)
# Output:
# - model : gemini-2.5-flash
# 
# > Analyze this file
```

### Parameter Display
The `generate_content_retry` functions have a `show_params` parameter (default=True) that automatically displays the model and prompt before generation:

```python
# Parameters will be displayed before generation
response = generate_content_retry(["Hello"], show_params=True)
print(response.text)

# Disable parameter display
response = generate_content_retry(["Hello"], show_params=False)
print(response.text)
```

## Usage Examples

### Dialogue System
```python
def chat_with_gemini():
    while True:
        user_input = input("Question: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        response = generate_content_retry(
            [user_input],
            model="gemini-2.5-flash",
            config=config_text,
            include_thoughts=True
        )
        print(f"Answer: {response.text}")
        print()
```

### Batch Processing
```python
questions = ["question1", "question2", "question3"]
results = []

for i, question in enumerate(questions):
    contents = [question]
    
    # File output for progress display
    with open(f"log_{i+1}.txt", "w", encoding="utf-8") as log:
        response = generate_content_retry(
            contents, model=model, config=config, file=log
        )
    
    results.append(response)
    
    print(f"Completed: {i+1}/{len(questions)}")
```

## Model List

```python
models = [
    "gemini-2.5-flash",    # Fast, low cost
    "gemini-2.5-pro",      # High performance, thinking feature support
]

default_model = models[0]  # Set Flash as default
```

## Notes

1. **Environment Variable**: `GEMINI_API_KEY` configuration required
2. **Encoding**: UTF-8 recommended for file output
3. **Resource Management**: Delete uploaded files after use
4. **Rate Limiting**: Automatically waits on 429 errors, but appropriate usage intervals recommended
5. **Thinking Feature**: Supported on both Gemini 2.5 Pro and Flash models
