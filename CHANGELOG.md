# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.3] - 2025-06-29

### Changed
- **Improved repetition detection** for English text with new threshold (200) and formula
- Better handling of longer repetitive patterns with linear interpolation
- Added early termination optimization for short text inputs

## [0.2.2] - 2025-06-28

### Added
- **Repetition detection** to prevent LLM output loops
- `check_repetition` parameter in generation functions (default: True)

### Changed
- Improved OpenAI streaming with `MarkdownStreamConverter` for consistent formatting

## [0.2.1] - 2025-06-27

### Added
- **Length limitation** via `max_length` parameter in generation functions
- Early termination during streaming when output reaches specified length

## [0.2.0] - 2025-06-26

### Added
- **Multi-provider compatibility** through new `compat` module
- **OpenAI integration** with unified interface via `generate_with_schema()`

### Changed
- Refactored Response class from gemini.py to response.py for better modularity

## [0.1.0] - 2025-06-21

### Added
- Initial release with Gemini API wrapper
- Response dataclass with comprehensive generation results
- Automatic retry logic and error handling
- Streaming support and schema-based generation
- Pydantic model integration
- Terminal formatting utilities
- Thinking process visualization
- File upload/delete operations
