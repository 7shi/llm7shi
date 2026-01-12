# llm7shi

A simplified Python library for interacting with large language models. Supports Google's Gemini AI, OpenAI, and local Ollama models.

## Why llm7shi?

This library emerged from a common developer problem: reusing Gemini API code across multiple projects led to "secret sauce" code that became increasingly complex with error handling, retry logic, and other production necessities. Rather than continuing to copy-paste and modify the same code, we extracted it into a standalone library.

The name is admittedly a personal project identifier. If you find the name off-putting, please feel free to fork this project under a different name - it's released under CC0, so you have complete freedom to do so.

## Design Philosophy

llm7shi is intentionally a **thin wrapper** around LLM APIs - it doesn't attempt to abstract away the underlying APIs or create a complex universal interface. However, it does provide unified API access for specific workflows where they add clear value, which are isolated in the optional `compat` module. The core library focuses on:

- **Preserving provider capabilities**: Access provider-specific features like thinking process visualization
- **Solving real-world problems**: Built-in retry logic, error handling, and streaming support
- **Minimal learning curve**: If you know the underlying APIs, you know llm7shi
- **Production-ready**: Handle the tedious but essential aspects like rate limiting and error recovery

## Features

- **Minimal Wrapper**: Thin layer over LLM APIs without complex abstraction
- **Multi-Provider Support**: Works with Gemini, OpenAI, Ollama, and OpenAI-compatible endpoints (llama.cpp, LocalAI, etc.) through separate modules and unified `compat` interface
- **Secure Custom Endpoint Support**: Flexible API key management with `model@base_url|api_key_env` syntax prevents accidental key leakage to local servers
- **Production-Ready Error Handling**: Built-in retry logic for API errors (429, 500, 502, 503) respecting API-suggested retry delays
- **Streaming Output**: Both text and schema-based generation support real-time streaming
- **Thinking Process Visualization**: Leverage thinking capabilities in Gemini 2.5, Ollama models, and reasoning-capable custom endpoints
- **Schema-based Generation**: JSON schema and Pydantic model support for structured outputs
- **Terminal Formatting**: Convert Markdown formatting to colored terminal output
- **Repetition Detection**: Automatic detection and stopping of repetitive output patterns (configurable)
- **Battle-Tested**: Handles the tedious but essential production concerns

## Requirements

- Python >= 3.10
- API keys for desired providers:
  - Gemini API key from Google AI Studio
  - OpenAI API key (optional, for OpenAI models)
  - Local Ollama installation (optional, for local models)

## Installation

### As a library

To use llm7shi as a library in your project:

```bash
uv add https://github.com/7shi/llm7shi.git
```

### For development

To download and develop the project:

```bash
git clone https://github.com/7shi/llm7shi.git
cd llm7shi
uv sync
```

## Setup

Set your Gemini API key as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

For OpenAI API compatibility (via compat module):

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

For custom OpenAI-compatible endpoints with authentication:

```bash
# Set custom API key for authenticated proxy or custom endpoint
export MY_PROXY_KEY="your-proxy-api-key"

# Use in code with: model="openai:gpt-4@http://my-proxy.com/v1|MY_PROXY_KEY"
```

**Security Note**: When using `@base_url` syntax without `|api_key_env`, the library automatically uses an empty API key to prevent accidentally leaking your `OPENAI_API_KEY` to untrusted local servers.

For Ollama (local models, no API key needed):

```bash
# Install and start Ollama first: https://ollama.ai/
ollama pull qwen3:4b  # or your preferred model
```

## API Reference

See [llm7shi/README.md](llm7shi/README.md) for complete API documentation and module details.

## Examples

See [examples/README.md](examples/README.md) for complete examples and documentation.

### Basic Text Generation

```python
from llm7shi import generate_content_retry

generate_content_retry(["Hello, World!"])
```

### Pydantic Schema Example

```python
from typing import List
from pydantic import BaseModel, Field
from llm7shi import config_from_schema, generate_content_retry

class LocationTemperature(BaseModel):
    location: str
    temperature: float = Field(description="Temperature in Celsius")

class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]

generate_content_retry(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    config=config_from_schema(LocationsAndTemperatures),
)
```

## Important Notes

### llama.cpp Structured Output Behavior

When using llama.cpp server with the gpt-oss template and structured output (JSON schema), the server behaves differently from plain text mode:

- **Plain text mode**: Server emits control tokens (`<|channel|>`, `<|message|>`, etc.) to separate reasoning from final answer
- **Structured output mode** (when `response_format` is specified): Server returns direct JSON output **without control tokens**

This means:
- The `GptOssTemplateFilter` is automatically disabled for structured output (no control tokens to parse)
- Separation between reasoning and final answer via control tokens is not available in JSON mode
- If you want to capture reasoning in structured output, include dedicated fields (e.g., `reasoning`) in your JSON schema

Example schema with reasoning field:
```python
class LocationTemperature(BaseModel):
    reasoning: str  # Explicitly include reasoning field
    location: str
    temperature: float
```

See [llm7shi/openai.md](llm7shi/openai.md) for detailed information about gpt-oss template filter behavior.

## Testing

Run the test suite with:

```bash
uv run pytest
```

See [tests/README.md](tests/README.md) for detailed testing documentation.
