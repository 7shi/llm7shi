import json
import sys
import inspect
from typing import Dict, Any, List, Union, Type

from pydantic import BaseModel


def do_show_params(contents, *, model=None, file=sys.stdout, **kwargs):
    """Display generation parameters for debugging/logging.

    Args:
        contents: The content/prompts to display (List[str] or List[Dict[str, str]])
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

    # Display contents based on format
    if contents and isinstance(contents[0], dict):
        # OpenAI message format
        for msg in contents:
            print(file=file)
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            print(f"> [{role}]", file=file)
            for line in content.splitlines():
                print(">", line, file=file)
    else:
        # Legacy List[str] format - quote each line of contents
        for content in contents:
            print(file=file)
            for line in content.splitlines():
                print(">", line, file=file)
    print(file=file)


def contents_to_openai_messages(
    contents: Union[List[str], List[Dict[str, str]]],
    system_prompt: str = None
) -> List[Dict[str, str]]:
    """Convert contents and system prompt to OpenAI message format.

    Args:
        contents: List of user content strings OR OpenAI message format
        system_prompt: System prompt as string (only used if contents is List[str])

    Returns:
        List of OpenAI format messages

    Raises:
        ValueError: If system prompt provided in both places
    """
    # Detect format
    if is_openai_messages(contents):
        # Already in OpenAI format
        if system_prompt:
            # Check for conflict with message-embedded system prompt
            system_messages = [msg for msg in contents if msg["role"] == "system"]
            if system_messages:
                raise ValueError(
                    "System prompt provided in both messages (role='system') and system_prompt parameter. "
                    "Please use only one method."
                )
            # Add system_prompt to the beginning
            openai_messages = [{"role": "system", "content": system_prompt}]
            openai_messages.extend(contents)
            return openai_messages
        else:
            # Return contents as-is
            return contents
    else:
        # Legacy List[str] format
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
        
    Raises:
        ValueError: If a circular reference is detected in the schema.
    """
    schema = schema.copy()
    defs = schema.pop("$defs", {})
    
    def resolve_ref(obj: Any, seen_defs: set) -> Any:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                if ref.startswith("#/$defs/"):
                    def_name = ref[8:]
                    if def_name in seen_defs:
                        # Cycle detected, raise an error
                        raise ValueError(f"Circular reference detected in schema: {def_name}")
                    if def_name in defs:
                        # Add current def to seen set for this path and recurse
                        return resolve_ref(defs[def_name], seen_defs | {def_name})
            
            # Recursively resolve in all values, excluding 'title'
            return {k: resolve_ref(v, seen_defs) for k, v in obj.items() if k != "title"}
        elif isinstance(obj, list):
            return [resolve_ref(item, seen_defs) for item in obj]
        else:
            return obj
    
    # Start resolution with an empty set of seen definitions
    return resolve_ref(schema, set())


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


def create_json_descriptions_prompt(schema: Union[Dict[str, Any], Type[BaseModel]]) -> str:
    """Create a prompt with JSON field descriptions for better schema compliance.

    Args:
        schema: JSON schema dictionary or Pydantic model class

    Returns:
        String prompt with field descriptions
    """
    # Convert Pydantic model to JSON schema if needed
    if inspect.isclass(schema) and issubclass(schema, BaseModel):
        schema = schema.model_json_schema()

    descriptions = extract_descriptions(schema)
    if not descriptions:
        return ""

    description_text = "\n".join([f"- {key}: {value}" for key, value in descriptions.items()])
    return f"Please extract information to the following JSON fields.\n{description_text}"


def is_openai_messages(contents: Union[List[str], List[Dict[str, str]]]) -> bool:
    """Detect if contents is in OpenAI message format.

    Args:
        contents: Either List[str] or List[Dict[str, str]]

    Returns:
        True if OpenAI message format, False if List[str]

    Raises:
        ValueError: If format is ambiguous or invalid
    """
    if not contents:
        return False

    if isinstance(contents[0], str):
        # Verify all items are strings
        if not all(isinstance(item, str) for item in contents):
            raise ValueError("Mixed format: contents must be either all strings or all dicts")
        return False
    elif isinstance(contents[0], dict):
        # Verify all items are dicts with required keys
        for i, item in enumerate(contents):
            if not isinstance(item, dict):
                raise ValueError(f"Mixed format: contents must be either all strings or all dicts")
            if "role" not in item or "content" not in item:
                raise ValueError(f"Invalid message format at index {i}: missing 'role' or 'content' key")
            if not isinstance(item["role"], str) or not isinstance(item["content"], str):
                raise ValueError(f"Invalid message format at index {i}: 'role' and 'content' must be strings")
            # Validate role values
            if item["role"] not in ["system", "user", "assistant"]:
                raise ValueError(f"Invalid role at index {i}: '{item['role']}' (must be 'system', 'user', or 'assistant')")
        return True
    else:
        raise ValueError("Invalid contents format: must be List[str] or List[Dict[str, str]]")


def openai_messages_to_contents(messages: List[Dict[str, str]]) -> tuple[List, Union[str, None]]:
    """Convert OpenAI message format to Gemini Content objects and extract system prompt.

    Args:
        messages: OpenAI format messages with 'role' and 'content' keys

    Returns:
        Tuple of (List of Gemini Content objects, system_prompt or None)

    Raises:
        ValueError: If multiple system messages are found

    Note:
        - 'user' role maps to role='user'
        - 'assistant' role maps to role='model' (Gemini terminology)
        - 'system' role is extracted and returned separately
    """
    from google.genai import types

    contents = []
    system_prompt = None

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            # Extract system prompt
            if system_prompt is not None:
                raise ValueError("Multiple system messages found in messages list")
            system_prompt = content
        elif role == "user":
            # Map to Gemini user role
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=content)]
                )
            )
        elif role == "assistant":
            # Map to Gemini model role
            contents.append(
                types.Content(
                    role="model",
                    parts=[types.Part(text=content)]
                )
            )
        else:
            raise ValueError(f"Unsupported role: {role}")

    return contents, system_prompt
