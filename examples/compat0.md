# compat0.py - Multi-Provider Hello World Example

## Overview

This example demonstrates the compatibility layer's ability to generate plain text responses from both Gemini and OpenAI models using the same interface. It's the compatibility version of `hello.py`.

## Code Explanation

```python
from llm7shi.compat import generate_with_schema

generate_with_schema(["Hello, World!"], model="gemini-2.5-flash")
print("=" * 40)
generate_with_schema(["Hello, World!"], model="gpt-4.1-mini")
```

### Key Components

1. **Unified Interface**: `generate_with_schema()` works with both providers
2. **Plain Text Generation**: No schema specified (`schema=None` by default)
3. **Model Selection**: Explicitly specify the model to use
4. **Same Input Format**: Contents list as first positional argument for both APIs

### Differences from hello.py

- **Original (`hello.py`)**: Uses Gemini-specific `generate_content_retry()`
- **Compatibility (`compat0.py`)**: Uses unified `generate_with_schema()` for both APIs

## Expected Output

The example runs the same prompt twice:

1. **Gemini Output**: Response from `gemini-2.5-flash`
2. **Separator**: 40 equals signs
3. **OpenAI Output**: Response from `gpt-4.1-mini`

Both models will generate a greeting or response to "Hello, World!" in their own style.

## Usage

Run this example with:

```bash
uv run examples/compat0.py
```

## Environment Requirements

Ensure both API keys are set:

```bash
export GEMINI_API_KEY="your-gemini-key"
export OPENAI_API_KEY="your-openai-key"
```

## Features Demonstrated

- **Provider Abstraction**: Same code works with different LLM providers
- **Plain Text Mode**: Generate unstructured text without schemas
- **Model Flexibility**: Easy switching between providers
- **Consistent Interface**: No need to learn provider-specific APIs

## Use Cases

- **Provider Comparison**: Test the same prompt across different models
- **Fallback Systems**: Switch providers based on availability
- **Cost Optimization**: Choose providers based on pricing
- **Feature Testing**: Compare model capabilities

## Related Examples

- `hello.py`: Original Gemini-only version
- `compat1.py`: Structured output with JSON schema
- `compat2.py`: Structured output with Pydantic models