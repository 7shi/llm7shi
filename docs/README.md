# Documentation

This directory contains design notes, implementation insights, and technical discussions about llm7shi development.

## Overview

These documents capture important design decisions, experimental ideas, and technical explorations that inform the library's evolution. They complement the module-level documentation by providing broader context and future-looking perspectives.

## Available Documents

### [20250629-repetition-detection.md](20250629-repetition-detection.md) - Repetition Detection in Streaming Output
Technical exploration of detecting and handling repetitive patterns in LLM streaming output.

Key topics:
- Pattern detection algorithms for streaming text
- Performance considerations for real-time processing
- Integration with quality control mechanisms

### [20250630-schema-jsx.md](20250630-schema-jsx.md) - Thoughts on Schema Generation and JSX-like Syntax
Design exploration for more intuitive schema definition approaches.

Key topics:
- Dynamic schema generation from dictionaries
- JSX-like declarative syntax proposals
- Python-idiomatic alternatives (decorators, classes)
- Generation order considerations for better LLM output

### [20250702-ollama-thinking.md](20250702-ollama-thinking.md) - Ollama Thinking and JSON Format Conflict
Investigation and resolution of JSON malformation when combining Ollama's thinking functionality with structured output.

Key topics:
- Systematic debugging methodology for multi-provider issues
- Ollama API behavior with think=True and format parameters
- Automatic thinking disabling for structured output scenarios (Resolved in later Ollama versions)
- API limitation workarounds and design trade-offs

### [20250703-schema-descriptions.md](20250703-schema-descriptions.md) - Schema Descriptions and Multi-Provider Compatibility
Exploration of challenges and solutions for consistent schema-based structured output across different LLM providers.

Key topics:
- Provider-specific handling of schema metadata and descriptions
- Systematic evaluation of instruction formats for schema compliance
- Client-side solution for Ollama's schema description limitations
- Best practices for multi-provider structured output reliability

### [20251204-ollama-cleanup.md](20251204-ollama-cleanup.md) - Ollama Streaming Cleanup and Connection Management
Investigation and resolution of persistent server-side sessions when interrupting Ollama streaming responses.

Key topics:
- HTTP client connection pooling and session persistence issues
- Ollama API limitations for server-side cancellation
- Explicit client cleanup with try...finally pattern
- Implementation changes in llm7shi for proper resource cleanup

### [20251206-repetition-threshold.md](20251206-repetition-threshold.md) - Repetition Detection Threshold Adjustment
Adjustment of repetition detection thresholds following weighted whitespace detection enhancement.

Key topics:
- Dynamic base algorithm for threshold calculation
- Monotonic non-decreasing constraint for early termination
- Coordination with whitespace detection thresholds
- Selection of base=340 and pattern_len>=21 threshold

### [20251207-quasi-repetition.md](20251207-quasi-repetition.md) - Quasi-Repetition Detection Algorithm
Gap-tolerant detection for patterns with small variations like "foo1foo2foo3...".

Key topics:
- Gap constraint: `gap_length < pattern_length` for valid quasi-repetition
- Backward scanning algorithm for efficient detection
- Integration with existing exact-match algorithm
- Variable-length gap handling (e.g., "9", "10", "100")

## Document Naming Convention

Documents follow the format: `YYYYMMDD-topic-name.md`

Where:
- `YYYYMMDD` is the date of creation or primary investigation
- `topic-name` should be 2 words maximum, using hyphens to separate words
- Examples: `ollama-thinking`, `schema-jsx`, `repetition-detection`

This convention ensures:
- Chronological ordering of ideas
- Easy tracking of when concepts were explored
- Clear, concise topic identification
- Consistent filename lengths

## Purpose

These documents serve multiple purposes:
1. **Design History**: Capture the evolution of key features
2. **Future Direction**: Explore potential improvements
3. **Technical Rationale**: Document non-obvious implementation choices
4. **Experimental Ideas**: Test concepts before implementation

## Contributing

When adding new documentation:
- Use the date-based naming convention
- Focus on "why" rather than "how"
- Include code examples for clarity
- Link to related implementations when applicable