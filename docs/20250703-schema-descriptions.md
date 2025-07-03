# Schema Descriptions and Multi-Provider Compatibility

This document explores the challenges and solutions for ensuring consistent schema-based structured output across different LLM providers, particularly addressing the issue where schema descriptions are ignored by some providers like Ollama.

## Problem Statement

When using JSON schema-based structured output with LLMs, different providers handle schema metadata differently:

1. **OpenAI/GPT models**: Generally respect schema `description` fields but may still misinterpret instructions
2. **Google Gemini**: Similar to OpenAI, with reasonable adherence to descriptions
3. **Ollama models**: Completely ignore schema `description` fields, treating them as if they don't exist

This inconsistency creates challenges for multi-provider applications that need reliable structured output behavior.

## Investigation Methodology

We conducted a systematic experiment using a temperature conversion task to evaluate how different instruction formats affect model compliance across providers. The test involved converting "90 degrees Fahrenheit in Tokyo" to Celsius, with models expected to output JSON containing location and temperature data.

### Test Setup

**Input**: "The temperature in Tokyo is 90 degrees Fahrenheit."

**Expected Output**: JSON with Tokyo as location and 32.22°C as temperature

**Schema**: Contains a `temperature` field with `"description": "Temperature in Celsius"`

### Experimental Patterns

We tested five different approaches for conveying schema information:

1. **Baseline**: No explicit instructions about field meanings
2. **Description-only**: Instructions only in schema `description` fields
3. **Field-name instructions**: Field names contain the full instruction text
4. **Dual instructions**: Both prompt and field names contain instructions
5. **Key-value mapping**: Prompt maps short keys to instruction text

## Results and Analysis

### Original Problem (qwen3:4b)

Initially, the qwen3:4b model consistently failed to perform temperature conversion:

```json
{
  "locations_and_temperatures": [
    {
      "location": "Tokyo",
      "temperature": 90  // Should be 32.22°C
    }
  ]
}
```

The model was outputting the original Fahrenheit value instead of converting to Celsius.

### Root Cause

The issue stemmed from Ollama's complete disregard for schema `description` fields. While other providers like Gemini and GPT could partially interpret the schema description, Ollama models had no indication that the `temperature` field should contain Celsius values.

### Solution Implementation

We implemented a client-side solution using the **key-value mapping approach** (equivalent to experimental pattern #5):

```python
def create_json_descriptions_prompt(schema: Union[Dict[str, Any], Type[BaseModel]]) -> str:
    """Create a prompt with JSON field descriptions for better schema compliance."""
    if inspect.isclass(schema) and issubclass(schema, BaseModel):
        schema = schema.model_json_schema()
    
    descriptions = extract_descriptions(schema)
    if not descriptions:
        return ""
    
    description_text = "\n".join([f"- {key}: {value}" for key, value in descriptions.items()])
    return f"Please extract information to the following JSON fields.\n{description_text}"
```

### Implementation Example

```python
# Before: Manual extraction
descriptions = extract_descriptions(schema)
description_text = "\n".join([f"- {key}: {value}" for key, value in descriptions.items()])
json_descriptions = f"Please extract information to the following JSON fields.\n{description_text}"

# After: Utility function
json_descriptions = create_json_descriptions_prompt(schema)

# Usage in multi-message format
generate_with_schema(
    ["The temperature in Tokyo is 90 degrees Fahrenheit.", json_descriptions],
    schema=schema,
    model=model,
)
```

## Results After Implementation

All models now correctly convert temperatures:

**gemini-2.5-flash**:
```json
{
  "reasoning": "The temperature for Tokyo was provided in Fahrenheit and converted to Celsius using the formula C = (F - 32) * 5/9.",
  "locations_and_temperatures": [{"location": "Tokyo", "temperature": 32.22}]
}
```

**gpt-4.1-mini**:
```json
{
  "reasoning": "The given temperature is 90 degrees Fahrenheit. To convert Fahrenheit to Celsius, use the formula: C = (F - 32) * 5/9. So, C = (90 - 32) * 5/9 = 58 * 5/9 ≈ 32.22 degrees Celsius.",
  "locations_and_temperatures": [{"location": "Tokyo", "temperature": 32.22}]
}
```

**qwen3:4b** (with item-level reasoning):
```json
{
  "locations_and_temperatures": [
    {
      "reasoning": "The temperature in Tokyo is given as 90 degrees Fahrenheit. To convert this to Celsius, the formula $ C = (F - 32) \\times \\frac{5}{9} $ is used. Plugging in 90 for F, we get $ C = (90 - 32) \\times \\frac{5}{9} = 58 \\times \\frac{5}{9} \\times 10 = 32.22 $ degrees Celsius.",
      "location": "Tokyo",
      "temperature": 32.22
    }
  ]
}
```

## Key Insights

### 1. Provider-Agnostic Approach Required

Relying solely on schema `description` fields is insufficient for multi-provider compatibility. The most robust approach is to explicitly include field descriptions in the prompt text.

### 2. Reasoning Field Benefits

Adding a `reasoning` field to schemas provides multiple benefits:
- **Debugging**: Reveals the model's thought process
- **Quality**: Encourages more thoughtful processing
- **Thinking substitute**: For providers like Ollama that disable thinking in structured output mode

### 3. Client-Side Implementation

Rather than building automatic description extraction into the provider-specific code, implementing this as a client-side utility function provides:
- **Flexibility**: Users can choose when to apply enhanced prompts
- **Transparency**: Clear about what additional instructions are being added
- **Maintainability**: Single implementation for all providers

### 4. Item-Level Reasoning Strategy

Further investigation revealed that reasoning field placement significantly impacts output quality:
- **Top-level reasoning**: Creates disconnect between thought process and item-specific processing
- **Item-level reasoning**: Enables contextual thinking for each data item
- **Reasoning-first ordering**: Positioning reasoning as the first property within items ensures models think before deciding values, leading to more accurate transformations

## Best Practices

### 1. Always Include Field Descriptions

When defining schemas, always include meaningful `description` fields:

```json
{
  "type": "object",
  "properties": {
    "temperature": {
      "type": "number",
      "description": "Temperature in Celsius"
    },
    "location": {
      "type": "string",
      "description": "Geographic location name"
    }
  }
}
```

### 2. Use Description Enhancement for Critical Fields

For fields where precise interpretation is crucial, use `create_json_descriptions_prompt()`:

```python
json_descriptions = create_json_descriptions_prompt(schema)
contents = [user_input, json_descriptions]
```

### 3. Include Reasoning Fields for Complex Tasks

Add reasoning fields to schemas for tasks requiring calculation or interpretation. For multi-item processing, place reasoning at the item level as the first property:

```json
{
  "type": "array",
  "items": {
    "type": "object", 
    "properties": {
      "reasoning": {"type": "string"},
      "location": {"type": "string"},
      "temperature": {"type": "number", "description": "Temperature in Celsius"}
    },
    "required": ["reasoning", "location", "temperature"]
  }
}
```

## Integration with llm7shi

This solution has been integrated into the llm7shi library as a utility function:

```python
from llm7shi import create_json_descriptions_prompt
```

The function supports both JSON schema dictionaries and Pydantic model classes, making it compatible with all the library's structured output features.

## Future Considerations

### 1. Automatic Enhancement

Future versions might include options for automatic prompt enhancement in provider-specific code, with user controls for when to apply this behavior.

### 2. Provider-Specific Optimizations

Different providers might benefit from different instruction formats. The current approach uses a universally effective format, but provider-specific optimizations could yield better results.

### 3. Schema Validation

Enhanced validation could verify that critical fields have descriptions before applying schema-based generation, preventing silent failures.

## Conclusion

The key-value mapping approach using explicit field descriptions in prompts provides the most reliable way to ensure consistent structured output across different LLM providers. This solution:

- **Solves the Ollama description problem** completely
- **Improves compliance** for all providers
- **Maintains simplicity** through client-side implementation
- **Provides debugging capabilities** through reasoning fields

This approach should be considered standard practice for applications requiring robust multi-provider structured output.