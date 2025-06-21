# llm7shi

A simplified Python library for interacting with large language models. Currently supports Google's Gemini AI models.

## Features

- **Simple API**: Easy-to-use wrapper for Gemini models
- **Automatic Retry**: Built-in retry logic for API errors (429, 500, 502, 503) with exponential backoff
- **Streaming Support**: Real-time output streaming for interactive experiences
- **Schema-based Generation**: JSON schema support for structured outputs
- **Terminal Formatting**: Convert Markdown formatting to colored terminal output
- **Error Resilience**: Robust error handling for production use

## Requirements

- Python >= 3.10
- Gemini API key from Google AI Studio

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

## Usage

### Basic Text Generation

```python
from llm7shi.gemini import generate_content_retry

generate_content_retry(["Hello, World!"])
```

### Structured JSON Output

```python
from pathlib import Path
from llm7shi.gemini import config_from_schema, generate_content_retry

# Load a JSON schema file
schema = Path("schema.json")
generate_content_retry(
    ["The temperature in Tokyo is 90 degrees Fahrenheit."],
    config=config_from_schema(schema),
)
```

Example schema file (`schema.json`):

```json
{
  "type": "object",
  "properties": {
    "locations_and_temperatures": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string"
          },
          "temperature": {
            "type": "number",
            "description": "Temperature in Celsius"
          }
        },
        "required": ["location", "temperature"]
      }
    }
  }
}
```

## API Reference

### Core Functions

- `generate_content_retry(messages, config=None, file=None)`: Main function for generating content with automatic retry
- `config_from_schema(schema_path)`: Create a generation config from a JSON schema file

### Supported Models

- `gemini-2.5-flash` (default)
- `gemini-2.5-pro`

## Architecture

### Core Modules

- **`llm7shi/gemini.py`**: Main API wrapper with retry logic and schema support
- **`llm7shi/terminal.py`**: Terminal formatting utilities for Markdown conversion

### Key Features

- **Streaming Output**: Both text and schema-based generation support real-time streaming
- **Thinking Process**: Automatic thinking budget optimization for Gemini 2.5 models
- **Cross-platform**: Windows console compatibility included

## Examples

Run the included examples:

```bash
# Basic text generation
uv run examples/hello.py

# Schema-based structured output
uv run examples/schema.py
```

## Dependencies

- `colorama>=0.4.6`: Cross-platform colored terminal output
- `google-genai>=1.21.1`: Official Google Generative AI client

## License

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication
