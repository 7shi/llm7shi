# llm7shi

A simplified Python library for interacting with large language models. Currently supports Google's Gemini AI models.

## Features

- **Simple API**: Easy-to-use wrapper for Gemini models
- **Automatic Retry**: Built-in retry logic for API errors (429, 500, 502, 503) with exponential backoff
- **Streaming Output**: Both text and schema-based generation support real-time streaming
- **Thinking Process**: Automatic thinking budget optimization for Gemini 2.5 models
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

## API Reference

- [llm7shi/gemini.md](llm7shi/gemini.md): Main API wrapper with retry logic and schema support
- [llm7shi/terminal.md](llm7shi/terminal.md): Terminal formatting utilities for Markdown conversion

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
