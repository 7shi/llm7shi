# llm7shi Package

This directory contains the core modules of the llm7shi library for interacting with large language models.

## Core Modules

### [gemini.py](gemini.py) - Main API Wrapper
Main API wrapper for Google's Gemini AI models with retry logic, streaming support, and schema-based generation.

**Documentation**: [gemini.md](gemini.md)

**Key Features**:
- Automatic retry logic for API errors
- Streaming output support
- JSON schema and Pydantic model support
- Response dataclass with thoughts, text, and metadata
- File upload/delete operations

### [terminal.py](terminal.py) - Terminal Formatting
Terminal formatting utilities for converting Markdown to colored terminal output.

**Documentation**: [terminal.md](terminal.md)

**Key Features**:
- Convert Markdown bold formatting to terminal colors
- Streaming conversion support
- Windows console compatibility

### [\_\_init\_\_.py](__init__.py) - Package Interface
Package initialization and convenience imports for easy access to all public API functions.

**Exported Functions**:
- `generate_content_retry()` - Main generation function
- `Response` - Response dataclass
- `config_from_schema()` - Schema configuration
- `build_schema_from_json()` - JSON schema conversion
- Terminal formatting utilities

## Usage

Import the main functions directly from the package:

```python
from llm7shi import generate_content_retry, Response, config_from_schema
```

Or import specific modules:

```python
from llm7shi.gemini import generate_content_retry
from llm7shi.terminal import convert_markdown
```

## Architecture

The package follows a modular design:

- **gemini.py**: Core API functionality and business logic
- **terminal.py**: Presentation layer for terminal output
- **\_\_init\_\_.py**: Public API interface and convenience imports

Each module is self-contained with comprehensive documentation and can be used independently or together for complete functionality.