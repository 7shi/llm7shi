# hello.py - Basic Text Generation Example

## Overview

This example demonstrates the simplest usage of llm7shi for basic text generation using Google's Gemini AI models.

## Code Explanation

```python
from llm7shi import generate_content_retry

generate_content_retry(["Hello, World!"])
```

### Key Points

1. **Simple Import**: Uses the package-level import for convenience
2. **Basic Usage**: Passes a simple text prompt as a list
3. **Default Behavior**: 
   - Uses `gemini-2.5-flash` model (fastest, most cost-effective)
   - Outputs to stdout with real-time streaming
   - Includes thinking process visualization
   - Automatic retry on API errors

## Expected Output

The model will respond to the "Hello, World!" prompt with a greeting and explanation, displaying:
- 🤔 **Thinking...** (the AI's reasoning process)
- 💡 **Answer:** (the final response)

## Usage

Run this example with:

```bash
uv run examples/hello.py
```

## Prerequisites

- Set `GEMINI_API_KEY` environment variable
- Install dependencies with `uv sync`

## Related Functions

- `generate_content_retry()`: Main function for text generation
- `generate_content_retry_with_thoughts()`: For separate access to thinking process