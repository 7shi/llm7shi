# llm7shi Package Initialization

This module serves as the main entry point for the llm7shi package, providing convenient imports for all public APIs.

## Package Overview

llm7shi is a simplified Python library for interacting with large language models. Currently supports Google's Gemini AI models with features including:

- Simple API wrapper with automatic retry logic
- Streaming support for real-time output
- JSON schema-based structured generation
- Terminal formatting utilities
- Robust error handling

## Module Structure

The package is organized into several modules:

### gemini.py
Core functionality for interacting with Google's Gemini API:
- `DEFAULT_MODEL`: Default model to use (gemini-2.5-flash)
- `Response`: Dataclass containing generation results
- `build_schema_from_json()`: Convert JSON schema to Gemini Schema object
- `config_from_schema()`: Create config for structured JSON output
- `config_text`: Default config for plain text responses
- `generate_content_retry()`: Main generation function with retry logic
- `upload_file()`: Upload files to Gemini API
- `delete_file()`: Delete uploaded files

### terminal.py
Terminal formatting utilities for better output display:
- `bold()`: Convert text to bold terminal format
- `convert_markdown()`: Convert Markdown bold to terminal colors
- `MarkdownStreamConverter`: Stream converter for real-time formatting

### utils.py
Utility functions for various operations:
- `do_show_params()`: Display generation parameters
- `contents_to_openai_messages()`: Convert to OpenAI message format
- `add_additional_properties_false()`: Add OpenAI schema requirements
- `inline_defs()`: Inline $defs references in JSON schemas

### compat.py (not exported)
Compatibility layer for using multiple LLM providers:
- `generate_with_schema()`: Unified interface for OpenAI and Gemini
- Must be imported explicitly: `from llm7shi.compat import generate_with_schema`

## Version Management

The package version is dynamically retrieved from package metadata using `importlib.metadata`.

## Example Usage

Basic text generation:
```python
from llm7shi import generate_content_retry

response = generate_content_retry(["Hello, World!"])
print(response.text)
```

Schema-based structured output:
```python
from llm7shi import config_from_schema, build_schema_from_json
import json

# Load and build schema
with open("schema.json") as f:
    schema_data = json.load(f)
schema = build_schema_from_json(schema_data)

# Create config and generate
config = config_from_schema(schema)
response = generate_content_retry(["Extract data"], config=config)
```

Using compatibility layer:
```python
from llm7shi.compat import generate_with_schema

# Works with both Gemini and OpenAI models
result = generate_with_schema(
    contents=["Hello"],
    model="gpt-4-mini"  # or "gemini-2.5-flash"
)
```

## Exported Symbols

All symbols listed in `__all__` are available for import directly from the llm7shi package. This provides a clean public API while keeping internal implementation details private.