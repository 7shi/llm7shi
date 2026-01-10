# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2026-01-10

### Added
- **Multi-format message support** - Accept both `List[str]` and OpenAI-compatible `List[Dict[str, str]]` message formats

### Fixed
- **Temperature parameter passing** in Ollama API

## [0.8.0] - 2026-01-02

### Changed
- **Ollama thinking with structured output** can now be used concurrently - removed restriction after Ollama API improvements resolved JSON formatting issues

## [0.7.1] - 2025-12-07

### Changed
- **Optimized quasi-repetition detection** with efficient backward searching using `rfind()`

## [0.7.0] - 2025-12-07

### Added
- **Quasi-repetition detection** for patterns with gaps - detects "foo1foo2foo3..." where counters change, using gap constraint (gap_length < pattern_length)

## [0.6.1] - 2025-12-07

### Changed
- **Adjusted repetition detection threshold** to coordinate with weighted whitespace detection - reduced false positives while maintaining effective detection (base increased from 100 to 340)

## [0.6.0] - 2025-12-06

### Changed
- **Improved whitespace detection** with weighted calculation - newlines: 8×, tabs: 4×, spaces: 1× (threshold: 512 weighted units = 512 spaces or 128 tabs or 64 newlines)

### Fixed
- **Ollama stream interruption** with explicit connection cleanup
- **Rate limit retry** variable reference in delay extraction

## [0.5.0] - 2025-10-23

### Added
- **Custom endpoint support** for OpenAI-compatible APIs
- **gpt-oss template filter** for llama.cpp structured output parsing
- **Adaptive threshold calculation** for repetition detection

### Changed
- **Improved essay evaluation** with reasoning-first schema approach

## [0.4.0] - 2025-07-03

### Added
- **Ollama integration** with full multi-provider support through compat module
- **Schema description prompts** via `create_json_descriptions_prompt()` utility

### Changed
- **Three-provider compatibility** - Gemini, OpenAI, and Ollama with unified interface
- **Improved examples** demonstrating consistent behavior across all providers

## [0.3.0] - 2025-06-30

### Added
- New `monitor.py` module centralizing stream monitoring logic
- **StreamMonitor class** for unified output quality control

### Changed
- **Eliminated code duplication** between Gemini and OpenAI implementations
- **Optimized detection frequency** - every 512 characters for repetition, 128 for whitespace

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
