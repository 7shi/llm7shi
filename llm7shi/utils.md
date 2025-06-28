# utils.py - Utility Functions

This module provides utility functions for parameter display, message formatting, and schema transformations used across the llm7shi package.

## Functions

### do_show_params()

Display generation parameters in a formatted way for debugging and logging purposes.

```python
def do_show_params(contents, *, model=None, file=sys.stdout, **kwargs)
```

**Parameters:**
- `contents`: The content/prompts to display
- `model`: Model name being used
- `file`: File object to write output to (default: sys.stdout, None to skip)
- `**kwargs`: Additional parameters to display

**Features:**
- Aligns parameter names for clean output
- Quotes content lines with `>` prefix
- Skips output if file is None

**Example:**
```python
do_show_params(
    ["Hello, World!", "How are you?"],
    model="gemini-2.5-flash",
    temperature=0.7,
    file=sys.stdout
)
```

**Output:**
```
- model      : gemini-2.5-flash
- temperature: 0.7

> Hello, World!

> How are you?
```

### contents_to_openai_messages()

Convert a simple contents array and optional system prompt to OpenAI's message format.

```python
def contents_to_openai_messages(
    contents: List[str], 
    system_prompt: str = None
) -> List[Dict[str, str]]
```

**Parameters:**
- `contents`: List of user content strings
- `system_prompt`: Optional system prompt string

**Returns:**
- List of message dictionaries in OpenAI format

**Example:**
```python
messages = contents_to_openai_messages(
    ["Question 1", "Question 2"],
    system_prompt="You are a helpful assistant"
)

# Result:
# [
#   {"role": "system", "content": "You are a helpful assistant"},
#   {"role": "user", "content": "Question 1"},
#   {"role": "user", "content": "Question 2"}
# ]
```

### add_additional_properties_false()

Recursively add `additionalProperties: false` to all objects in a JSON schema for OpenAI API compatibility.

```python
def add_additional_properties_false(
    schema: Dict[str, Any]
) -> Dict[str, Any]
```

**Parameters:**
- `schema`: JSON schema dictionary

**Returns:**
- Modified schema with `additionalProperties: false` added to all objects

**Features:**
- Recursively processes nested objects
- Handles array items
- Preserves all other schema properties
- Creates a copy to avoid modifying the original

**Example:**
```python
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "address": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"}
            }
        }
    }
}

result = add_additional_properties_false(schema)

# Result adds additionalProperties: false to both root and nested objects
```

### inline_defs()

Inline `$defs` references in JSON schemas and remove title fields.

```python
def inline_defs(
    schema: Dict[str, Any]
) -> Dict[str, Any]
```

**Parameters:**
- `schema`: JSON schema with `$defs` section

**Returns:**
- JSON schema with all `$defs` references resolved and titles removed

**Features:**
- Resolves `$ref` references like `#/$defs/MyType`
- Removes all `title` fields during processing
- Recursively handles nested references
- Essential for Pydantic model compatibility with OpenAI

**Example:**
```python
schema = {
    "$defs": {
        "Address": {
            "type": "object",
            "title": "Address",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"}
            }
        }
    },
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "address": {"$ref": "#/$defs/Address"}
    }
}

result = inline_defs(schema)

# Result:
# {
#   "type": "object",
#   "properties": {
#     "name": {"type": "string"},
#     "address": {
#       "type": "object",
#       "properties": {
#         "street": {"type": "string"},
#         "city": {"type": "string"}
#       }
#     }
#   }
# }
```

### detect_repetition()

Detect if text has repetitive patterns, useful for identifying LLM output loops.

```python
def detect_repetition(
    text: str,
    threshold: int = 50
) -> bool
```

**Parameters:**
- `text`: Text to check for repetitions
- `threshold`: Maximum pattern length to check (default: 50)

**Returns:**
- `True` if repetition detected, `False` otherwise

**Algorithm:**
- Checks for patterns of 1 to `threshold` characters
- Each pattern of length `n` must repeat at least `threshold - n // 2` times
- Only checks patterns at the end of the text
- Stops checking when text is too short for larger patterns

**Examples:**
```python
# Single character repetition
detect_repetition("a" * 50)  # True (50 repetitions of 'a')
detect_repetition("a" * 49)  # False (not enough repetitions)

# Multi-character patterns
detect_repetition("abc" * 49)  # True (49 repetitions, needs 49)
detect_repetition("hello " * 50)  # True (pattern length 6, needs 47)

# No repetition
detect_repetition("This is normal text")  # False

# Custom threshold
detect_repetition("xy" * 5, threshold=10)  # True (needs 9 repetitions)
```

**Use Cases:**
- Detecting when LLMs get stuck in repetitive loops
- Stopping generation when output becomes repetitive
- Quality control for generated text

## Usage Context

### In gemini.py

Functions are used in `generate_content_retry()`:

```python
# Parameter display when show_params=True
if show_params:
    do_show_params(contents, model=model, file=file)

# Repetition detection when check_repetition=True
if check_repetition and len(text) >= next_check_size:
    if detect_repetition(text):
        # Stop generation and show warning
```

### In compat.py

All functions are used for API compatibility:

```python
# Convert message format
openai_messages = contents_to_openai_messages(contents, system_prompt)

# Process Pydantic schema for OpenAI
if inspect.isclass(schema) and issubclass(schema, BaseModel):
    schema = schema.model_json_schema()
    schema = inline_defs(schema)  # Inline references
    
# Add required fields for OpenAI
schema_for_openai = add_additional_properties_false(schema)
```

## Design Principles

1. **Non-invasive**: Functions create copies rather than modifying inputs
2. **Recursive**: Schema transformations handle deeply nested structures
3. **Flexible**: Parameter display skips when output is disabled
4. **Compatible**: Transformations ensure cross-API compatibility

## Import

These utilities are available from the main package:

```python
from llm7shi import (
    do_show_params,
    contents_to_openai_messages,
    add_additional_properties_false,
    inline_defs,
    detect_repetition
)
```

Or import directly from the module:

```python
from llm7shi.utils import do_show_params, detect_repetition
```