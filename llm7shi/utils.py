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


def extract_descriptions(schema: Dict[str, Any]) -> Dict[str, str]:
    """Extract description values with their parent keys from JSON schema.
    
    Args:
        schema: JSON schema dictionary
        
    Returns:
        Dictionary mapping parent keys to their description values
    """
    descriptions = {}
    
    def traverse_schema(obj: Any, parent_key: str = None) -> None:
        if isinstance(obj, dict):
            # If this object has a description and we have a parent key
            if "description" in obj and parent_key:
                descriptions[parent_key] = obj["description"]
            
            # Traverse properties
            if "properties" in obj and isinstance(obj["properties"], dict):
                for prop_key, prop_value in obj["properties"].items():
                    traverse_schema(prop_value, prop_key)
            
            # Handle array items separately - don't pass parent_key to avoid overwriting
            if "items" in obj and isinstance(obj["items"], dict):
                traverse_schema(obj["items"], None)
            
            # Traverse other nested structures (excluding properties, items, and description)
            for key, value in obj.items():
                if key not in ["properties", "items", "description"]:
                    if isinstance(value, (dict, list)):
                        traverse_schema(value, None)
        
        elif isinstance(obj, list):
            for item in obj:
                traverse_schema(item, parent_key)
    
    traverse_schema(schema)
    return descriptions
