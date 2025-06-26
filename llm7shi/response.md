# Response Class

The `Response` class is a dataclass that encapsulates the results from LLM API calls, providing a unified interface for accessing generation outputs and metadata.

## Overview

The Response object contains all relevant information from an LLM generation request, including the generated text, thinking process, raw API responses, and configuration details. It's designed to be provider-agnostic, supporting various LLM providers beyond just Gemini.

## Attributes

### Core Content
- **`text`** (`str`): The final generated text content
- **`thoughts`** (`str`): The thinking process text (if available and requested)

### Input/Output Data
- **`contents`** (`Optional[List[Any]]`): The input contents sent to the API
- **`response`** (`Optional[Any]`): The raw API response object from the provider
- **`chunks`** (`List[Any]`): List of all streaming chunks received during generation

### Configuration
- **`model`** (`Optional[str]`): The model identifier used for generation
- **`config`** (`Optional[Any]`): The configuration object used (provider-specific)

## Usage Examples

### Basic Text Access
```python
from llm7shi import generate_content_retry

response = generate_content_retry(["Hello, how are you?"])
print(response.text)  # Direct access to generated text
print(response)       # Same as response.text due to __str__ method
```

### Accessing Metadata
```python
response = generate_content_retry(["Explain quantum computing"])

print(f"Model used: {response.model}")
print(f"Number of chunks: {len(response.chunks)}")
print(f"Has thoughts: {bool(response.thoughts)}")
```

### Working with Thinking Process
```python
# Request thinking process for complex queries
response = generate_content_retry(
    ["Solve this complex math problem..."], 
    include_thoughts=True
)

if response.thoughts:
    print("AI's thinking process:")
    print(response.thoughts)
    
print("\nFinal answer:")
print(response.text)
```

## String Representations

The Response class provides convenient string representations:

- **`str(response)`**: Returns the generated text content
- **`repr(response)`**: Returns a concise representation showing truncated contents and text

```python
response = generate_content_retry(["Short question"])
print(str(response))   # "The answer to your question..."
print(repr(response))  # Response(contents='Short ques...', text='The answer...')
```

## Design Philosophy

### Provider Agnostic
The Response class uses generic types (`Any`) for provider-specific objects like `config` and `response`, allowing it to work with different LLM providers without modification.

### Comprehensive Data Storage
All aspects of the generation process are preserved:
- Input data for reproducibility
- Raw responses for advanced processing
- Streaming chunks for analysis
- Configuration for debugging

### Simple Access Patterns
The class prioritizes ease of use with:
- Direct text access via string conversion
- Optional metadata for when needed
- Clear attribute names and documentation

## Integration Notes

The Response class is automatically returned by `generate_content_retry()` and other generation functions in the llm7shi library. It's exported at the package level for easy access:

```python
from llm7shi import Response  # Available for type hints and direct use
```

This design supports the library's goal of providing a simple yet comprehensive interface for LLM interactions while maintaining flexibility for future enhancements and provider additions.