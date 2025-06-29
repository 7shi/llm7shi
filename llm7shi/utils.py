import json
import sys
import inspect
from typing import Dict, Any, List, Union, Type

from pydantic import BaseModel


def do_show_params(contents, *, model=None, file=sys.stdout, **kwargs):
    """Display generation parameters for debugging/logging.

    Args:
        contents: The content/prompts to display
        model: Model name being used
        file: File object to write output to (default: sys.stdout)
        **kwargs: Additional parameters to display
    """
    # Do nothing if file is None
    if file is None:
        return

    # Collect all parameters
    params = {"model": model, **kwargs}

    # Find the maximum key length for alignment
    max_key_len = max(len(k) for k in params.keys()) if params else 0

    # Print parameters with aligned colons
    for k, v in params.items():
        print(f"- {k:<{max_key_len}}: {v}", file=file)

    # Quote each line of contents
    for content in contents:
        print(file=file)
        for line in content.splitlines():
            print(">", line, file=file)
    print(file=file)


def contents_to_openai_messages(contents: List[str], system_prompt: str = None) -> List[Dict[str, str]]:
    """Convert contents and system prompt to OpenAI message format.
    
    Args:
        contents: List of user content strings
        system_prompt: System prompt as string
        
    Returns:
        List of OpenAI format messages
    """
    openai_messages = []
    
    if system_prompt:
        openai_messages.append({"role": "system", "content": system_prompt})
    
    for content in contents:
        openai_messages.append({"role": "user", "content": content})
    
    return openai_messages


def add_additional_properties_false(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Add additionalProperties: false to schema for OpenAI compatibility."""
    def process_schema(obj: Any) -> Any:
        if isinstance(obj, dict):
            obj = obj.copy()
            
            # Add additionalProperties: false to objects
            if obj.get("type") == "object":
                obj["additionalProperties"] = False
            
            # Recursively process all nested schemas
            for key, value in obj.items():
                if key == "properties" and isinstance(value, dict):
                    # Process each property
                    obj[key] = {k: process_schema(v) for k, v in value.items()}
                elif key == "items":
                    # Process array items
                    obj[key] = process_schema(value)
                elif isinstance(value, dict):
                    # Process any other nested dict
                    obj[key] = process_schema(value)
            
            return obj
        else:
            return obj
    
    return process_schema(schema)


def inline_defs(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Inline $defs references in JSON schema and remove title fields.
    
    Args:
        schema: JSON schema with $defs
        
    Returns:
        JSON schema with $defs inlined and titles removed
    """
    schema = schema.copy()
    defs = schema.pop("$defs", {})
    
    def resolve_ref(obj: Any) -> Any:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                if ref.startswith("#/$defs/"):
                    def_name = ref[8:]  # Remove "#/$defs/" prefix
                    if def_name in defs:
                        return resolve_ref(defs[def_name])
            
            # Recursively resolve in all values, excluding 'title'
            return {k: resolve_ref(v) for k, v in obj.items() if k != "title"}
        elif isinstance(obj, list):
            return [resolve_ref(item) for item in obj]
        else:
            return obj
    
    return resolve_ref(schema)


def _calculate_required_reps(pattern_len: int) -> int:
    """Calculate required repetitions for a given pattern length.
    
    Args:
        pattern_len: Length of the pattern to check
        
    Returns:
        int: Number of repetitions required for this pattern length
    """
    if pattern_len >= 31:
        return 10
    else:
        # Linear interpolation
        total_len = 100 + (pattern_len - 1) * 8
        return total_len // pattern_len


def detect_repetition(text: str, threshold: int = 200) -> bool:
    """Detect if text has repetitive patterns.
    
    Checks for patterns of 1-threshold characters that repeat based on
    pattern length: shorter patterns need more repetitions, longer patterns
    need fewer (minimum 10 repetitions for patterns >= 31 chars).
    
    Args:
        text: Text to check for repetitions
        threshold: Maximum pattern length to check (default: 200)
        
    Returns:
        bool: True if repetition detected, False otherwise
    """
    # Check patterns from 1 to 10 characters
    for pattern_len in range(1, min(10, threshold) + 1):
        # Calculate required repetitions
        required_reps = _calculate_required_reps(pattern_len)
        
        # Break early if text is too short based on pattern length
        if pattern_len * required_reps > len(text):
            break
        
        # Extract pattern from the end
        pattern = text[-pattern_len:]
        
        # Check if text ends with required repetitions
        if text.endswith(pattern * required_reps):
            return True
    
    # Handle patterns > 10 characters
    if threshold <= 10:
        return False
    
    # For patterns > 10, they must contain the 10-char pattern
    # Use rfind optimization
    suffix_marker = text[-10:]  # Last 10 characters as a marker
    
    # Find all occurrences of suffix_marker and check patterns
    search_end = len(text) - 10
    min_search_pos = max(search_end - threshold, 0)
    while True:
        pos = text[:search_end].rfind(suffix_marker)
        
        # Stop if we've gone beyond the threshold limit
        if pos < min_search_pos:
            break
        
        # Extract the candidate pattern from this position to end
        candidate_pattern = text[pos + 10:]
        
        # Check if text ends with candidate_pattern repeated required times
        required_reps = _calculate_required_reps(len(candidate_pattern))
        if text.endswith(candidate_pattern * required_reps):
            return True
        
        # Continue searching before this position
        search_end = pos
    
    return False
