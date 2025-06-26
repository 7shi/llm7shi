# llm7shi Package

This directory contains the core modules of the llm7shi library for interacting with large language models.

## Core Modules

### [__init__.py](__init__.py) - Package Interface
Package initialization and public API exports. Provides convenient access to all main functions.

**Documentation**: [__init__.md](__init__.md)

**Key Exports**:
- Functions from all modules for easy import
- Dynamic version management
- Clean public API interface

### [gemini.py](gemini.py) - Gemini API Client
Main API wrapper for Google's Gemini AI models with automatic retry logic, streaming support, and structured output generation.

**Documentation**: [gemini.md](gemini.md)

**Key Features**:
- `generate_content_retry()` - Main generation function with retry logic
- `build_schema_from_json()` - JSON schema to Gemini Schema conversion
- `config_from_schema()` - Create config for structured output
- File upload/delete operations
- Thinking process visualization

### [response.py](response.py) - Response Data Class
Provider-agnostic response object that encapsulates results from LLM API calls.

**Documentation**: [response.md](response.md)

**Key Features**:
- `Response` dataclass - Comprehensive result object
- Provider-independent design
- Text, thoughts, and metadata access
- String conversion support

### [utils.py](utils.py) - Utility Functions
Helper functions for parameter display, message formatting, and schema transformations.

**Documentation**: [utils.md](utils.md)

**Key Functions**:
- `do_show_params()` - Display generation parameters
- `contents_to_openai_messages()` - Convert to OpenAI message format
- `add_additional_properties_false()` - Add OpenAI schema requirements
- `inline_defs()` - Inline $defs references in JSON schemas

### [compat.py](compat.py) - API Compatibility Layer
Unified interface for both OpenAI and Gemini APIs, enabling seamless switching between providers.

**Documentation**: [compat.md](compat.md)

**Key Features**:
- `generate_with_schema()` - Unified generation function
- Automatic API selection based on model name
- Support for JSON schemas, Pydantic models, or plain text
- Preserves provider-specific features

**Note**: This module is not exported in `__init__.py`. Import explicitly:
```python
from llm7shi.compat import generate_with_schema
```

### [terminal.py](terminal.py) - Terminal Formatting
Terminal output formatting utilities for better display of streaming responses.

**Documentation**: [terminal.md](terminal.md)

**Key Features**:
- `convert_markdown()` - Convert Markdown bold to terminal colors
- `MarkdownStreamConverter` - Stream converter for real-time formatting
- `bold()` - Simple bold text formatting
- Windows console compatibility

## Usage Examples

### Basic Import
```python
from llm7shi import generate_content_retry, Response

response = generate_content_retry(["Hello, World!"])
print(response.text)
```

### Structured Output
```python
from llm7shi import build_schema_from_json, config_from_schema

schema = build_schema_from_json(json_schema_dict)
config = config_from_schema(schema)
response = generate_content_retry(contents, config=config)
```

### Multi-Provider Support
```python
from llm7shi.compat import generate_with_schema

# Works with both providers
response = generate_with_schema(
    contents=["Your prompt"],
    schema=YourModel,
    model="gemini-2.5-flash"  # or "gpt-4-mini"
)
print(response.text)
```

## Architecture

The package follows a modular design with clear separation of concerns:

```
llm7shi/
├── __init__.py      # Public API exports
├── gemini.py        # Gemini-specific implementation
├── response.py      # Response data class
├── utils.py         # Shared utility functions
├── compat.py        # Multi-provider compatibility
└── terminal.py      # Output formatting
```

Each module:
- Has comprehensive documentation in a corresponding `.md` file
- Can be used independently or in combination
- Follows consistent patterns and conventions
- Is designed for extensibility

## Environment Setup

### Gemini API
```bash
export GEMINI_API_KEY="your-api-key"
```

### OpenAI API (for compat.py)
```bash
export OPENAI_API_KEY="your-api-key"
```

## Dependencies

- `google-genai` - Google's Gemini API client
- `openai` - OpenAI API client (optional, for compat.py)
- `pydantic` - Data validation (optional, for schema support)

See the main project README for installation instructions.