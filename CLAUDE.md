# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Guidelines

**Conversation Language**: While the assistant may converse with users in their preferred language, all code and documentation should be written in English unless specifically instructed otherwise.

### Git Commit Messages
- Use clear, concise commit messages in English
- Do not include promotional text or AI-generated signatures

### CHANGELOG Guidelines
- Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
- Keep entries concise and user-focused
- Use **bold** for feature names, avoid technical implementation details
- Focus on user-visible changes and benefits
- Group changes under Added/Changed/Fixed sections as appropriate

## Project Overview

llm7shi is a simplified Python library for interacting with large language models. Currently supports Google's Gemini AI models, with potential for future expansion to other LLM providers.

## Development Setup

### Package Management
This project uses `uv` as the package manager (evident from `uv.lock`). To install dependencies:
```bash
uv sync
```

### Environment Configuration
Set your Gemini API key:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Architecture

### Core Modules

1. **llm7shi/gemini.py**: Main API wrapper
   - Handles Gemini API client initialization
   - Provides retry logic for API errors (429, 500, 502, 503)
   - Supports both text generation and structured JSON output via schemas
   - Includes thinking process visualization for Gemini 2.5 models
   - Returns Response dataclass containing thoughts, text, response, chunks, model, config, and contents

2. **llm7shi/terminal.py**: Terminal formatting utilities
   - Converts Markdown bold (`**text**`) to terminal colors
   - Provides both one-shot and streaming conversion
   - Handles Windows console compatibility

3. **llm7shi/__init__.py**: Package initialization and convenience imports
   - Provides package-level imports for easy access
   - Dynamic version retrieval from package metadata
   - Centralizes all public API functions

### Key Design Patterns

- **Streaming Support**: Both modules support real-time output streaming
- **Error Resilience**: Automatic retry with exponential backoff for API errors
- **Flexible Output**: Supports output to console, files, or silent operation via `file` parameter
- **Schema-based Generation**: JSON schema and Pydantic model support for structured outputs
- **Response Object**: Comprehensive dataclass containing all generation results and metadata
- **Pydantic Integration**: Direct support for Pydantic models in `config_from_schema()`
- **Package Structure**: Proper Python package with `__init__.py` and convenient imports
- **Documentation Pairing**: Each `.py` file has a corresponding `.md` documentation file

## Common Development Tasks

### Running Examples
```bash
uv run examples/hello.py        # Basic text generation
uv run examples/schema1.py      # JSON schema-based generation
uv run examples/schema2.py      # Pydantic schema-based generation
```

### Running Tests
```bash
uv run pytest                   # Run all tests
uv run pytest -v              # Verbose output
uv run pytest tests/test_hello.py  # Run specific test
```

### Testing Strategy
- All tests use mocked API calls (no real API keys needed)
- Set GEMINI_API_KEY=dummy for testing
- Comprehensive coverage of examples and core functionality

### Testing API Integration
When testing Gemini API integration:
1. Check for proper error handling (rate limits, server errors)
2. Verify streaming output works correctly
3. Test schema validation for structured outputs

### Adding New Features
- Follow the existing pattern of separating API logic from presentation
- Maintain backward compatibility (see how `generate_content_retry` wraps the newer function)
- Include documentation for new features
- Support both streaming and non-streaming modes where applicable
- Create corresponding `.md` documentation file for any new `.py` module
- Update `__init__.py` to export new public functions
- Add examples in the `examples/` directory with matching documentation

## Important Notes

- The project supports Gemini 2.5 models (`gemini-2.5-flash`, `gemini-2.5-pro`)
- Documentation exists in `.md` files alongside Python modules (1:1 pairing)
- The API automatically handles thinking budget for optimal response times
- Windows console fixes are included in terminal.py
- Package uses dynamic version management via `importlib.metadata`
- Designed for future extensibility to support additional LLM providers
