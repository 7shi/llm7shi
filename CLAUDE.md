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
- Focus on "why" rather than "how" in module documentation
- See [DOCUMENTATION.md](DOCUMENTATION.md) for detailed guidelines

## Quick Project Context

llm7shi is a thin wrapper around the Gemini API that provides production-ready error handling, retry logic, and streaming support. The project uses `uv` as the package manager and follows a simplicity-first design philosophy.

## Architecture Overview

The project follows a modular architecture with clear separation of concerns. Each module has a specific purpose documented in its paired `.md` file. The core library remains a thin wrapper while optional modules provide additional functionality.

## Development Guidelines

### Testing Philosophy
- **Mock-first approach**: No real API calls to ensure fast, reliable CI/CD
- **Comprehensive coverage**: All examples and core functionality tested
- **Error scenario validation**: Retry logic and edge cases thoroughly tested

### Development Principles
- **Simplicity first**: New features should maintain the library's ease-of-use
- **Backward compatibility**: Always maintain existing API contracts
- **Streaming support**: New features should work with real-time output where applicable

### Key Architectural Decisions
- **Gemini 2.5 focus**: Primary support for latest models with thinking capabilities
- **Extensible architecture**: Designed for future multi-provider expansion
- **User experience priority**: Streaming output and terminal formatting included by default

For setup instructions, API reference, and examples, see the main [README.md](README.md).
