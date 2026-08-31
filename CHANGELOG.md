# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.15.1] - 2026-08-31

### Changed
- **`Client.__call__` accepts multiple prompt messages** - `prompt` can now be a single string or a list of strings, each sent as its own user-role message in the same turn (e.g. `client(["Essay:\n" + essay, question])`), instead of requiring the caller to push earlier turns onto `history` beforehand
- **essay example rewritten on `Client`** - `examples/essay.py` now builds its evaluation schema dynamically as a Pydantic model and folds the criteria descriptions into the prompt via `create_json_descriptions_prompt()`, matching `statusline.py`'s use of `Client`, and reads the parsed evaluation from `result.data` instead of re-parsing the text

### Added
- **statusline example** - `examples/statusline.py` demonstrates a progress bar over a batch of independent questions, streaming each answer to the terminal without subclassing

## [0.15.0] - 2026-08-31

### Added
- **Customizable progress bar** - The bar's columns can be adapted by subclassing (`ProgressContext.columns()`, `StatusLine.progress_context_class`); `StatusLine(console=...)` takes a Rich `Console` and `StatusLine.progress(started_at=...)` shows elapsed time for a run spanning several processes

### Fixed
- **Progress display glitches** - Rich markup is no longer parsed in streamed model output (a `[...]` in the text used to vanish or raise `MarkupError`), retry countdowns now render as a bar of their own when none is active, and leaving a nested bar no longer deregisters the enclosing one

### Changed
- **Public column classes** - `_MofNColumn`, `_ProcessElapsedColumn` and `_ProgressContext` are renamed without the leading underscore, breaking code that imported the private names

## [0.14.5] - 2026-08-28

### Added
- **Retry-After support for OpenAI-compatible errors** - Rate limit (429) and server error retries now honor the provider's requested wait time from the `Retry-After` response header, falling back to OpenRouter's `error.metadata.headers.Retry-After` field when the header itself isn't present

## [0.14.4] - 2026-08-27

### Fixed
- **OpenAI retryable error detection** - Retry-on-error check now uses `openai.APIStatusError` instead of `openai.APIError`; the base `APIError` class (e.g. connection/timeout errors) has no `status_code` attribute, causing an `AttributeError` when a non-HTTP error occurred

## [0.14.3] - 2026-08-25

### Fixed
- **Automatic function calling warning** - Gemini configs now explicitly disable automatic function calling, suppressing the `google-genai` library's "Direct use of automatic function calling (AFC) ... is not recommended" warning

## [0.14.2] - 2026-08-24

### Changed
- **Safety margin in retry countdown** - `ConsoleStream.wait_retry` and `StatusLineConsoleStream.wait_retry` now sleep for 1 second on 0s as well to provide a 1-second safety margin before retrying

## [0.14.1] - 2026-07-03

### Added
- **Overridable retry judgment in `Client`** - New `should_retry(resp, schema)` method factors out the quality-retry decision so subclasses can customize it; when a `schema` is passed to `Client.__call__`, it validates the response as JSON against the schema instead of the plain-text quality checks
- **`Response.data` field** - Holds the parsed JSON (or validated Pydantic instance) when `Client.__call__` is given a schema

## [0.14.0] - 2026-07-03

### Added
- **statusline module** (optional `statusline` extra) - Rich-based `StatusLine`/`StatusLineConsoleStream` for progress bars that coexist with streamed model output, promoted from dante-corpus

### Fixed
- **Retry count in retry message** - The default retry message now counts retries (`Retrying (1/4)...` through `(4/4)...`) instead of attempts, so the counter can actually reach its maximum; previously it counted failed attempts out of `DEFAULT_MAX_ATTEMPTS`, which never reached that number since the final attempt is not followed by a retry

## [0.13.1] - 2026-07-03

### Changed
- **Attempt count in retry message** - The default retry message now reads `Retrying (1/5)...` etc., showing the failed attempt number out of `DEFAULT_MAX_ATTEMPTS`

## [0.13.0] - 2026-06-27

### Added
- **Stateful Client** - New `Client` class managing conversational history, system prompt updates, quality retries, and XML persistence (`to_xml`/`load_xml`)
- **XML Serialization** - New `xml.py` utilities for serializing/deserializing chat logs to XML with CDATA escaping
- **StreamGenerator base class** - Unified streaming, monitoring, and retry logic across all providers (Gemini, OpenAI, Ollama) via a shared `stream.py` base class; extends rate-limit and connection error retries with countdown display to OpenAI
- **ConsoleStream** - Line-buffered terminal stream utility in `llm7shi.terminal` for coordinating retries and error logs with progress bars via subclassing
- **Dynamic countdown alignment** - Countdown digits aligned right with dynamic width for clean display as values decrease

## [0.12.0] - 2026-06-17

### Fixed
- **Terminal formatting after interrupted streaming** - When an exception or interrupt breaks off generation mid-stream, terminal formatting (bold/color/code-block background) is now reset and the line is properly terminated, so the terminal is no longer left in a colored state and the following traceback stays readable

## [0.11.9] - 2026-06-12

### Fixed
- **Gemini import without API key** - `import llm7shi` no longer fails when `GEMINI_API_KEY` is not set; the Gemini client is now initialized lazily on first use, matching the behavior of the OpenAI and Ollama providers

## [0.11.8] - 2026-06-07

### Fixed
- **Gemini thinking leak with `include_thoughts=False`** - Thought parts are now always identified by `part.thought`; previously, with `include_thoughts=False`, models that keep emitting thoughts (e.g. Gemma) had their reasoning leak into the answer body. It is now discarded instead

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
