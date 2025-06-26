# Examples

This directory contains practical examples demonstrating various features of llm7shi.

## Quick Start

To run any example:

1. Set your API key(s):
   - Gemini only: `export GEMINI_API_KEY="your-key"`
   - OpenAI compatibility: `export OPENAI_API_KEY="your-key"`
2. Run the example: `uv run examples/[filename].py`

## Example Categories

| Original | Compatibility | Purpose |
|----------|--------------|---------|
| `hello.py` | `compat0.py` | Basic text generation |
| `schema1.py` | `compat1.py` | JSON schema output |
| `schema2.py` | `compat2.py` | Pydantic model output |

The compatibility versions use `llm7shi.compat.generate_with_schema()` to work seamlessly with both Gemini and OpenAI models, while the original versions use Gemini-specific functions.

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
**Schema**: [schema1.json](schema1.json)

```bash
uv run examples/schema1.py
```

### [schema2.py](schema2.py) - Pydantic Schema Example
Shows how to use Pydantic models for type-safe schema definition and simpler code.

**Documentation**: [schema2.md](schema2.md)

```bash
uv run examples/schema2.py
```

## Multi-Provider Compatibility

### [compat0.py](compat0.py) - Multi-Provider Hello World
Compatibility version of hello.py that works with both Gemini and OpenAI models.

**Documentation**: [compat0.md](compat0.md)

```bash
uv run examples/compat0.py
```

### [compat1.py](compat1.py) - Multi-Provider JSON Schema
Compatibility version of schema1.py using the same JSON schema with both providers.

**Documentation**: [compat1.md](compat1.md)  
**Schema**: [schema1.json](schema1.json)

```bash
uv run examples/compat1.py
```

### [compat2.py](compat2.py) - Multi-Provider Pydantic Schema
Compatibility version of schema2.py using Pydantic models with both providers.

**Documentation**: [compat2.md](compat2.md)

```bash
uv run examples/compat2.py
```
