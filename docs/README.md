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

## Document Naming Convention

Documents follow the format: `YYYYMMDD-topic-name.md`

This convention ensures:
- Chronological ordering of ideas
- Easy tracking of when concepts were explored
- Clear topic identification

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