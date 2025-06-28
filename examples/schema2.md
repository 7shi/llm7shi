# schema2.py - Pydantic Schema Example

## Why This Example Exists

This example demonstrates the advantages of using Pydantic models for schema definition in modern Python development.

### Type-Safe Schema Definition
**Problem**: JSON Schema files are external, untyped, and don't provide IDE support or compile-time validation. They're error-prone and harder to maintain in larger codebases.

**Solution**: Uses Pydantic models with Python type hints, providing IDE auto-completion, type checking, and better integration with modern Python development workflows.

### Developer Experience Priority
**Problem**: Writing and maintaining JSON Schema files manually is tedious and error-prone, especially for complex nested structures.

**Solution**: Demonstrates how Python classes with type hints can automatically generate schemas while providing better tooling support, making structured LLM output more accessible to Python developers.