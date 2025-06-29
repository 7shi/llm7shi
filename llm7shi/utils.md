# utils.py - Utility Functions

## Why These Utilities Exist

These utility functions solve specific cross-cutting concerns that emerged while building the llm7shi library:

### Parameter Display (`do_show_params`)
**Problem**: When debugging LLM interactions, it's crucial to see exactly what parameters and content are being sent to the API. However, this display should be optional and cleanly formatted.

**Solution**: Created a unified parameter display function that formats both key-value parameters and content arrays consistently, with proper alignment and quote prefixes for content.

### Message Format Conversion (`contents_to_openai_messages`)
**Problem**: Our simple content array format needed to be converted to OpenAI's message-based format for API compatibility.

**Solution**: Automatic conversion that handles system prompts separately and treats all content items as user messages.

### Schema Compatibility (`add_additional_properties_false`, `inline_defs`)
**Problem**: Different LLM APIs have different schema requirements:
- OpenAI requires `additionalProperties: false` for strict mode
- Pydantic generates schemas with `$defs` references that OpenAI doesn't accept
- Title fields from Pydantic can cause validation issues

**Solution**: Created transformation functions that modify schemas to meet each API's specific requirements while preserving the original structure.

### Repetition Detection (`detect_repetition`)
**Problem**: Large language models occasionally get stuck in repetitive output loops, which wastes tokens and provides poor user experience. This was particularly noticeable during long generations.

**Solution**: Implemented a pattern detection algorithm that checks for repeating sequences at the end of generated text, with adjustable thresholds based on pattern complexity.

#### Threshold and Formula Update (2025-01)
**Problem**: The original formula (`threshold - pattern_len // 2`) with `threshold=50` was too sensitive for English text, where repetitive patterns can naturally occur over longer sequences without indicating a generation loop.

**Solution**: After empirical analysis, updated to `threshold=200` and implemented a new formula based on linear interpolation:
- For patterns < 31 chars: `total_len = 100 + (pattern_len - 1) * 8`, then `required_reps = total_len // pattern_len`
- For patterns ≥ 31 chars: `required_reps = 10` (fixed)

This ensures that single character repetitions need 100 occurrences (e.g., "aaaa..."), while longer patterns need proportionally fewer repetitions, with a minimum of 10 for patterns of 31+ characters.

**Rationale**: The formula was designed to make `pattern_len * required_reps` increase roughly linearly, preventing false positives in normal English text while still catching actual generation loops. The boundary at 31 characters was chosen based on analysis showing diminishing returns beyond this point.

**Note on Edge Cases**: Due to integer division, the formula produces minor reversals at certain points (e.g., pattern_len 15→16, 18→19, 23→24, 30→31) where `pattern_len * required_reps` slightly decreases. These reversals were deemed acceptable as they don't significantly impact the detection effectiveness and avoiding them would require more complex formulas.

**Early Termination Optimization**: The implementation includes an early termination condition: if the text is too short by more than `pattern_len` characters (for patterns < 31) or any amount (for patterns ≥ 31), the search stops. This optimization is particularly effective because of the reversals - when a reversal occurs, the subsequent pattern often requires even more text, making further checks unnecessary.

## Key Design Decisions

### Non-Destructive Operations
All schema transformation functions create copies rather than modifying input objects. This prevents unexpected side effects when the same schema is used multiple times.

### Recursive Processing
Schema transformations handle deeply nested structures automatically, ensuring that all objects (including those in arrays and nested properties) receive the necessary modifications.

### Conditional Output
The parameter display function respects file output settings, allowing it to be easily disabled for silent operation modes.