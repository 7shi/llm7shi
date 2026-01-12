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
- Repetition detection and automatic stopping

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
- `extract_descriptions()` - Extract property descriptions for prompt enhancement
- `create_json_descriptions_prompt()` - Generate enhanced prompts with schema field descriptions

### [openai.py](openai.py) - OpenAI API Client
Direct OpenAI API wrapper with streaming support and monitoring capabilities.

**Documentation**: [openai.md](openai.md)

**Key Features**:
- `generate_content()` - Pure OpenAI API wrapper with streaming
- Accepts pre-converted OpenAI message format
- Streaming output with terminal formatting
- Repetition detection and length monitoring
- Custom endpoint support via `base_url` parameter
- Secure API key management via `api_key_env` parameter with safe defaults
- gpt-oss template filter for reasoning-capable models (model name `"llama.cpp/gpt-oss"` serves as client-side template identifier)
- Thoughts capture and real-time display

**Note**: This module is optional and not exported in `__init__.py`. Import explicitly:
```python
from llm7shi.openai import generate_content
```

### [ollama.py](ollama.py) - Ollama API Client
Local Ollama API wrapper with streaming support and thinking process visualization.

**Documentation**: [ollama.md](ollama.md)

**Key Features**:
- `generate_content()` - Ollama API wrapper with streaming
- Thinking process extraction via `chunk.message.thinking`
- Automatic capability detection for thinking support
- Consistent interface matching OpenAI and Gemini modules
- Default model: qwen3:4b for balanced performance
- Real-time thinking and answer display

**Note**: This module is optional and not exported in `__init__.py`. Import explicitly:
```python
from llm7shi.ollama import generate_content
```

### [compat.py](compat.py) - API Compatibility Layer
Unified interface for OpenAI, Gemini, and Ollama APIs, enabling seamless switching between providers.

**Documentation**: [compat.md](compat.md)

**Key Features**:
- `generate_with_schema()` - Unified generation function
- Vendor prefix support:
  - Core providers: "openai:gpt-4.1-mini", "google:gemini-2.5-flash", "ollama:qwen3:4b"
  - OpenAI-compatible: "openrouter:qwen/qwen3-4b:free", "groq:llama-3.1-8b-instant", "grok:grok-4-1"
- Base URL embedding support (e.g., "openai:model@http://localhost:8080/v1") - model name acts as client-side template identifier for llama-server
- API key environment variable specification (e.g., "openai:model@http://proxy.com/v1|MY_PROXY_KEY")
- Secure defaults: Empty API key for custom endpoints to prevent key leakage
- Backward compatible automatic API selection based on model name
- Support for JSON schemas, Pydantic models, or plain text
- Preserves provider-specific features
- Delegates OpenAI and Ollama processing to respective modules

**Note**: This module is optional and not exported in `__init__.py`. Import explicitly:
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

### [monitor.py](monitor.py) - Stream Output Monitoring
Stream monitoring for output quality control, including repetition detection and length limits.

**Documentation**: [monitor.md](monitor.md)

**Key Features**:
- `StreamMonitor` - Class for monitoring streaming output
- `detect_repetition()` - Detect repetitive patterns in text output
- Real-time pattern and whitespace detection
- Provider-agnostic design for unified quality control
- `GptOssTemplateFilter` - Parser for gpt-oss template control tokens
- Channel-based content routing (analysis/final separation)

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

### Enhanced Schema Prompts
```python
from llm7shi import create_json_descriptions_prompt

# Automatically extract schema descriptions for better model compliance
enhanced_prompt = create_json_descriptions_prompt(your_schema)
response = generate_content_retry([user_input, enhanced_prompt], config=config)
```

### Multi-Provider Support
```python
from llm7shi.compat import generate_with_schema

# Works with all providers
response = generate_with_schema(
    contents=["Your prompt"],
    schema=YourModel,
    model="openai:gpt-4.1-mini"  # or "google:gemini-2.5-flash" or "ollama:qwen3:4b"
)
print(response.text)

# OpenAI-compatible providers (OpenRouter, Groq, X.AI)
response = generate_with_schema(
    contents=["Your prompt"],
    model="openrouter:"  # Uses default model: qwen/qwen3-4b:free
)

response = generate_with_schema(
    contents=["Your prompt"],
    model="groq:llama-3.3-70b-versatile"  # Specify a model
)

response = generate_with_schema(
    contents=["Your prompt"],
    model="grok:grok-4-1"  # X.AI Grok
)

# Multi-turn conversation with message format
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language."},
    {"role": "user", "content": "What makes it special?"}
]
response = generate_with_schema(messages, model="google:gemini-2.5-flash")

# Custom endpoint with authentication
response = generate_with_schema(
    contents=["Your prompt"],
    schema=YourModel,
    model="openai:gpt-4@http://my-proxy.com/v1|MY_PROXY_KEY"
)

# Local server without authentication (secure default)
response = generate_with_schema(
    contents=["Your prompt"],
    schema=YourModel,
    model="openai:gpt-4@http://localhost:11434/v1"
)

# Backward compatibility still works
response = generate_with_schema(
    contents=["Your prompt"],
    schema=YourModel,
    model="gemini-2.5-flash"  # or "gpt-4.1-mini"
)
```

## Architecture

The package follows a modular design with clear separation of concerns:

```
llm7shi/
├── __init__.py      # Public API exports
├── gemini.py        # Gemini-specific implementation
├── openai.py        # OpenAI-specific implementation
├── ollama.py        # Ollama-specific implementation
├── response.py      # Response data class
├── utils.py         # Shared utility functions
├── compat.py        # Multi-provider compatibility
├── terminal.py      # Output formatting
└── monitor.py       # Stream output monitoring
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

### Custom OpenAI-Compatible Endpoints
For authenticated custom endpoints, set a custom environment variable:
```bash
export MY_PROXY_KEY="your-proxy-api-key"
```

Then use with: `model="openai:gpt-4@http://my-proxy.com/v1|MY_PROXY_KEY"`

**Security Note**: When using `@base_url` without `|api_key_env`, the library automatically uses an empty API key to prevent accidentally leaking your `OPENAI_API_KEY` to untrusted servers.

### OpenAI-Compatible Providers
For pre-configured providers (OpenRouter, Groq, X.AI):
```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
export GROQ_API_KEY="your-groq-api-key"
export XAI_API_KEY="your-xai-api-key"
```

Then use with vendor prefixes: `model="openrouter:"`, `model="groq:llama-3.3-70b"`, `model="grok:grok-4-1"`

## Dependencies

- `google-genai` - Google's Gemini API client
- `openai` - OpenAI API client (for compat.py)
- `ollama` - Ollama API client (for ollama.py)
- `pydantic` - Data validation (for schema support)

See the main project README for installation instructions.
