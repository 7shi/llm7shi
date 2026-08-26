# test_utils_descriptions.py - Schema Description Processing Tests

## Why These Tests Exist

Testing schema description processing functions required addressing specific multi-provider compatibility and prompt enhancement challenges:

### Multi-Provider Consistency Validation
**Problem**: The effectiveness of schema description enhancement needed to be verified across different LLM providers, particularly those like Ollama that completely ignore schema descriptions in their native processing.

**Solution**: Tests validate that the generated prompts maintain consistent format and content regardless of the input schema type (JSON vs Pydantic), ensuring that the same enhancement technique works uniformly across all supported providers.