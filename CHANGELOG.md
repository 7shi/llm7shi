# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.11.7] - 2026-06-07

### Fixed
- **OpenRouter reasoning with `include_thoughts=True`** - The compat layer now sends `reasoning.enabled` explicitly for both states, so models that do not emit reasoning by default (e.g. `google/gemma`) now return their thinking process when requested

## [0.11.6] - 2026-06-06

### Added
- **Italic formatting** - Terminal output now renders `*italic*` text in yellow (`ITALIC_ON = Fore.YELLOW`); a `* `/`  * ` list marker stays literal, and `*italic*` composes inside `**bold**`

### Changed
- **Leading blank-line trimming** - Streaming display now drops leading blank lines at the start of the thinking and answer sections (symmetric with existing trailing-newline trimming); the returned `thoughts`/`text` remain verbatim

## [0.11.5] - 2026-06-05

### Added
- **Nested inline formatting** - Inline `` `code` `` inside `**bold**` now restores the bold color once the code closes, using a general stack so future inline elements compose the same way; markup inside inline code is left literal

### Changed
- **Markdown newline handling** - A single (soft) newline now keeps inline formatting active across the line; bold/inline code are reset only at a blank line (whitespace-only counts) or end of text, instead of at every newline

## [0.11.4] - 2026-06-04

### Fixed
- **Indented code-fence closing** - A closing ` ``` ` with leading whitespace no longer gets a gray background; the indent is buffered alongside the held newline and emitted after `BLOCK_OFF`

## [0.11.3] - 2026-06-04

### Added
- **Inline code and code-fence formatting** - Terminal output now renders inline `` `code` `` in bright blue and fenced ` ``` ` code blocks with the inner lines on a gray background, distinguishing them from `**bold**`; customize via `CODE_ON`/`CODE_OFF`/`BLOCK_ON`/`BLOCK_OFF`
- **Command-line entry point** - `uv run -m llm7shi md <file>` renders a Markdown file to the terminal for checking formatting

## [0.11.2] - 2026-06-04

### Fixed
- **OpenRouter reasoning disable** - `include_thoughts=False` now sets `reasoning.enabled=False` to fully skip the thinking process; `exclude: True` only hides reasoning tokens from the response while the model still thinks

### Added
- **OpenRouter example** - New `examples/openrouter.py` demonstrating `include_thoughts=True/False` with a free tier model

## [0.11.1] - 2026-06-04

### Fixed
- ~~**OpenRouter reasoning disable** - `include_thoughts=False` now sets `reasoning.max_tokens=0` to fully skip the thinking process; previously used `exclude: True` which hid the output but still consumed reasoning tokens~~ (incorrect: use `enabled=False` instead)

## [0.11.0] - 2026-06-04

### Added
- **OpenRouter reasoning support** - Reasoning output is now displayed and captured (`Response.thoughts`) for OpenAI-compatible providers; ~~`include_thoughts=False` suppresses it for `openrouter:` models~~ (incorrect: used `exclude: True` which only hid output)

### Changed
- **Unified stream processing** - Thinking/answer display, streaming, and monitoring are now shared across all providers via `StreamProcessor`, ensuring exactly one blank line between the thinking and answer sections regardless of provider
- **Bold text color** - Terminal bold formatting now renders in bright red (`Style.BRIGHT + Fore.RED`) for improved visibility on both dark and light backgrounds; customize via `BOLD_ON`/`BOLD_OFF` variables

## [0.10.2] - 2026-05-01

### Fixed
- **Repetition detection in thinking content** - Repetition checks now apply to thinking/reasoning output in all providers (Gemini, OpenAI, Ollama)

## [0.10.1] - 2026-01-14

### Added
- **Cerebras support** - Added `cerebras` vendor prefix for OpenAI-compatible API access

## [0.10.0] - 2026-01-12

### Added
- **OpenAI-compatible vendor prefixes** - Added support for `openrouter`, `groq`, and `grok` prefixes
- **Secure API key management** for custom OpenAI endpoints

### Changed
- **Default model updates** - Examples now use Ollama by default

### Fixed
- **Config mutation bug** - Prevented `config_text` mutation by ensuring fresh instances are generated

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
