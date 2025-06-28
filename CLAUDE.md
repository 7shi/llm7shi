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

### Documentation Guidelines
- **Two-tier documentation structure**: Each Python module has a paired `.md` file (1:1 pairing)
- **Module `.md` files**: Focus on **implementation rationale and design decisions** - explain WHY the code was written, what problems it solves, and key design choices. Avoid code examples and detailed usage instructions.
- **Directory `README.md` files**: Provide practical information for users - usage examples, file organization, running instructions, environment setup
- **Rationale over implementation**: Code can be understood by reading it; documentation should explain the thought process behind it

## Project Overview

llm7shi is a simplified Python library for interacting with large language models. Currently supports Google's Gemini AI models, with potential for future expansion to other LLM providers.

## Development Setup

### Package Management
This project uses `uv` as the package manager (evident from `uv.lock`). To install dependencies:
```bash
uv sync
```

### Environment Configuration
Set your API keys:
```bash
export GEMINI_API_KEY="your-api-key-here"
export OPENAI_API_KEY="your-api-key-here"
```

## Architecture

### Design Philosophy

The library follows a **simplicity-first approach** with **optional complexity**:

- **Core simplicity**: Basic text generation requires minimal configuration
- **Layered functionality**: Advanced features (schemas, multi-provider) are opt-in
- **Streaming by default**: Real-time output for better user experience
- **Error resilience**: Automatic retry logic handles transient API failures
- **Provider independence**: Optional compatibility layer enables vendor flexibility

### Module Organization

Each module addresses specific architectural concerns:

- **gemini.py**: Core API interaction and reliability
- **terminal.py**: User experience and cross-platform output formatting  
- **utils.py**: Cross-cutting concerns and provider compatibility
- **compat.py**: Optional multi-provider abstraction layer
- **response.py**: Unified data structure for all generation results

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

### Testing Philosophy
- **Mock-first approach**: No real API calls to ensure fast, reliable CI/CD
- **Comprehensive coverage**: All examples and core functionality tested
- **Error scenario validation**: Retry logic and edge cases thoroughly tested

### Development Principles
- **Simplicity first**: New features should maintain the library's ease-of-use
- **Backward compatibility**: Always maintain existing API contracts
- **Streaming support**: New features should work with real-time output where applicable
- **Documentation rationale**: Focus on WHY decisions were made, not HOW code works
- **Two-tier docs**: Module `.md` for rationale, directory `README.md` for usage

## Key Decisions

- **Gemini 2.5 focus**: Primary support for latest models with thinking capabilities
- **Documentation philosophy**: Rationale over implementation details
- **Extensible architecture**: Designed for future multi-provider expansion
- **User experience priority**: Streaming output and terminal formatting included by default
