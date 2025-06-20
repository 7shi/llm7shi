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

## Main Functions

### `generate_content_retry_with_thoughts()`
Function to retrieve thinking process and answer separately.

```python
thoughts, text = generate_content_retry_with_thoughts(
    ["question content"],
    model="gemini-2.5-flash",
    config=config_text,
    include_thoughts=True,        # Include thinking process
    thinking_budget=None,         # Thinking time limit (optional)
    file=sys.stdout              # Output destination (None to disable)
)
```

**Return value**: Tuple of `(thoughts: str, text: str)`
- `thoughts`: AI's thinking process
- `text`: Final answer

### `generate_content_retry()`
Wrapper function for backward compatibility.

```python
text = generate_content_retry(
    ["question content"],
    model="gemini-2.5-flash",
    config=config_text,
    include_thoughts=True,
    thinking_budget=None,
    file=sys.stdout
)
```

**Return value**: `str` - Final answer only

## Configuration and Schemas

### Basic Configuration
```python
# For text output
config_text = types.GenerateContentConfig(
    response_mime_type="text/plain",
)

# For JSON output (with schema)
config_json = config_from_schema_string('''
{
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number"}
    },
    "required": ["answer", "confidence"]
}
''')
```

### Schema Functions
```python
# Generate configuration from JSON schema string
config = config_from_schema_string(schema_json_string)

# Generate configuration from schema file
config = config_from_schema("schema.json")
```

## Output Control

### Standard Output (Default)
```python
text = generate_content_retry(contents, model=model, config=config)
# Thinking process and answer displayed in real-time
```

### Disable Output
```python
text = generate_content_retry(contents, model=model, config=config, file=None)
# No screen output, retrieve result only
```

### File Output
```python
with open("conversation.txt", "w", encoding="utf-8") as f:
    text = generate_content_retry(contents, model=model, config=config, file=f)
# Save thinking process and answer to file
```

### Log File Output
```python
import sys
with open("debug.log", "w", encoding="utf-8") as log_file:
    thoughts, text = generate_content_retry_with_thoughts(
        contents, 
        model=model,
        config=config,
        file=log_file  # Record details to log file
    )
    print(f"Result: {text}")  # Display only result to console
```

## Error Handling

### Auto-retry Target Errors
- **429**: Rate limit → Wait according to `retryDelay`
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
thoughts, answer = generate_content_retry_with_thoughts(
    contents, model=model, config=config, file=None
)

# Analyze thinking process
if "mathematics" in thoughts:
    print("Using mathematical reasoning")
if "step" in thoughts.lower():
    print("Executing step-by-step thinking")

print(f"Final answer: {answer}")
```

### Controlling Thinking Time
```python
# When quick response is needed
quick_answer = generate_content_retry(
    contents,
    model=model,
    config=config,
    thinking_budget=30,  # Thinking time within 30 seconds
    file=None
)
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

text = generate_content_retry(contents, model=model, config=config)

# Delete file after use
delete_file(image_file)
```

## Usage Examples

### Dialogue System
```python
def chat_with_gemini():
    while True:
        user_input = input("Question: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        answer = generate_content_retry(
            [user_input],
            model="gemini-2.5-flash",
            config=config_text,
            include_thoughts=True
        )
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
        thoughts, answer = generate_content_retry_with_thoughts(
            contents, model=model, config=config, file=log
        )
    
    results.append({
        "question": question,
        "thoughts": thoughts,
        "answer": answer
    })
    
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
5. **Thinking Feature**: Only supported on Gemini 2.5 Pro, not available on Flash
