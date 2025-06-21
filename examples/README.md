# Examples

This directory contains practical examples demonstrating various features of llm7shi.

## Basic Usage

### [hello.py](hello.py) - Basic Text Generation
Simple text generation example showing the most basic usage of the library.

**Documentation**: [hello.md](hello.md)

```bash
uv run examples/hello.py
```

## Structured Output

### [schema1.py](schema1.py) - JSON Schema Example
Demonstrates structured JSON output using manual JSON schema definition with validation.

**Documentation**: [schema1.md](schema1.md)

```bash
uv run examples/schema1.py
```

### [schema2.py](schema2.py) - Pydantic Schema Example
Shows how to use Pydantic models for type-safe schema definition and simpler code.

**Documentation**: [schema2.md](schema2.md)

```bash
uv run examples/schema2.py
```

## Quick Start

To run any example:

1. Set your API key: `export GEMINI_API_KEY="your-key"`
2. Run the example: `uv run examples/[filename].py`

Each example includes detailed documentation explaining the concepts and implementation details.