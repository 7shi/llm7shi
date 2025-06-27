# llm7shi/compat.py - LLM API Compatibility Layer

## Overview

`llm7shi/compat.py` provides a unified interface for both OpenAI and Gemini APIs. It abstracts the implementation differences between these APIs, enabling seamless switching between providers with minimal code changes.

## Key Features

### 1. generate_with_schema()

The main function that provides a unified interface for content generation:

```python
from llm7shi.compat import generate_with_schema

# Generate structured output with schema
response = generate_with_schema(
    contents=["Your prompt here"],
    schema=YourPydanticModel,  # or JSON schema dict
    model="gemini-2.5-flash",  # or "gpt-4.1-mini"
    temperature=0.7,
    system_prompt="You are a helpful assistant",
    include_thoughts=True,      # Gemini only
    thinking_budget=None,       # Gemini only
    file=sys.stdout,
    show_params=True,
    max_length=None            # Maximum length of generated text
)

# Access generated text
print(response.text)  # The generated content
print(response.model)  # The model used
print(response.thoughts)  # Thinking process (Gemini only)

# Generate plain text without schema
response = generate_with_schema(
    contents=["Hello, World!"],
    schema=None,  # Plain text generation
    model="gpt-4.1-mini"
)
print(response.text)  # Direct text access
```

**Parameters:**
- `contents`: List of user content strings
- `schema`: JSON schema dict, Pydantic model, or None for plain text
- `model`: Model name (defaults to Gemini if None or starts with "gemini")
- `temperature`: Generation temperature (None uses API default)
- `system_prompt`: System instructions
- `include_thoughts`: Show thinking process (Gemini only)
- `thinking_budget`: Thinking token budget (Gemini only)
- `file`: Output stream for real-time display
- `show_params`: Display generation parameters
- `max_length`: Maximum length of generated text (None for no limit)

**Returns:**
- `Response`: Response object containing generated text and metadata

### 2. API-Specific Implementations

#### Gemini API (_generate_with_gemini)

Features:
- Uses `config_from_schema()` for structured output or `config_text` for plain text
- Supports thinking process display with `include_thoughts`
- System prompt becomes `system_instruction`
- Leverages `generate_content_retry()` with automatic retry logic

#### OpenAI API (_generate_with_openai)

Features:
- Streaming enabled by default for better UX
- Automatic conversion of Pydantic models to JSON schema
- Inlines `$defs` references using `inline_defs()`
- Adds required `additionalProperties: false` for OpenAI compatibility
- Converts message format using `contents_to_openai_messages()`
- Creates Response object with collected chunks and raw response data

### 3. Utility Functions (from utils.py)

#### contents_to_openai_messages()

Converts simple content array to OpenAI message format:

```python
openai_messages = contents_to_openai_messages(
    contents=["Question 1", "Question 2"],
    system_prompt="System instructions"
)
# Result: [
#   {"role": "system", "content": "System instructions"},
#   {"role": "user", "content": "Question 1"},
#   {"role": "user", "content": "Question 2"}
# ]
```

#### add_additional_properties_false()

Recursively adds `additionalProperties: false` to all objects in a JSON schema:
- Required by OpenAI's strict schema validation
- Handles nested objects and array items
- Preserves all other schema properties

#### inline_defs()

Resolves `$defs` references in JSON schemas:
- Inlines referenced definitions at usage points
- Removes `title` fields during processing
- Essential for Pydantic model compatibility with OpenAI

## Design Decisions

### Model Detection

Simple prefix matching for automatic API selection:
```python
if model is None or model.startswith("gemini"):
    return _generate_with_gemini(...)
else:
    return _generate_with_openai(...)
```

### Schema Handling

1. **Pydantic Models**: Automatically converted to JSON schema
2. **JSON Schema**: Used directly with necessary transformations
3. **None**: Enables plain text generation without structure

### Streaming Behavior

- **OpenAI**: Always streams for real-time output
- **Gemini**: Streaming handled by `generate_content_retry()`
- Output displayed progressively when `file` is provided

### Temperature Handling

- `None`: Uses each API's default temperature
- Explicit value: Passed directly to the API
- Allows leveraging provider-specific defaults

## Usage Examples

### Basic Structured Generation

```python
from llm7shi.compat import generate_with_schema
from pydantic import BaseModel
import json

class Location(BaseModel):
    city: str
    temperature: float

# Works with both APIs
response = generate_with_schema(
    contents=["What's the weather in Tokyo?"],
    schema=Location,
    model="gemini-2.5-flash"  # or "gpt-4.1-mini"
)

# Parse structured output
location_data = json.loads(response.text)
location = Location(**location_data)
print(f"City: {location.city}, Temperature: {location.temperature}")
```

### Plain Text Generation

```python
# Simple text generation without schema
response = generate_with_schema(
    contents=["Write a haiku about coding"],
    schema=None,
    temperature=0.9
)
print(response.text)
```

### With System Prompt

```python
response = generate_with_schema(
    contents=["Analyze this code: print('hello')"],
    schema=None,
    system_prompt="You are a code review expert",
    model="gpt-4.1-mini"
)
print(response.text)

# Limit response length
response = generate_with_schema(
    contents=["Write a long essay about AI"],
    schema=None,
    max_length=300  # Stop at 300 characters
)
print(response.text)
```

## Environment Setup

### Required Environment Variables

- **Gemini**: `GEMINI_API_KEY`
- **OpenAI**: `OPENAI_API_KEY`

### Import Method

Since this module is not exported in `__init__.py`, import it explicitly:

```python
from llm7shi.compat import generate_with_schema
```

## Implementation Notes

### Error Handling

- API errors are handled by underlying implementations
- Gemini uses retry logic from `generate_content_retry()`
- Schema validation errors surface immediately

### Performance Considerations

- Streaming reduces perceived latency
- Schema transformations are done once before API calls
- Minimal overhead for API detection

### Future Extensibility

To add a new provider:
1. Update model detection logic
2. Implement `_generate_with_[provider]()`
3. Add necessary schema transformations
4. Handle provider-specific features

## Summary

`compat.py` provides a clean abstraction over multiple LLM APIs while preserving access to provider-specific features. It simplifies multi-provider applications by:

- Unifying the interface for common operations
- Handling schema format differences automatically
- Preserving streaming and real-time output capabilities
- Allowing provider-specific optimizations when needed

This design enables easy switching between providers for testing, cost optimization, or feature availability without changing application code.