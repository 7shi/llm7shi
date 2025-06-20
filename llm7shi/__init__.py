"""
llm7shi - A simplified Python library for interacting with large language models.

Currently supports Google's Gemini AI models with features including:
- Simple API wrapper with automatic retry logic
- Streaming support for real-time output
- JSON schema-based structured generation
- Terminal formatting utilities
- Robust error handling

Example usage:
    from llm7shi.gemini import generate_content_retry
    
    # Basic text generation
    response = generate_content_retry(["Hello, World!"])
    
    # Schema-based structured output
    from llm7shi.gemini import config_from_schema
    config = config_from_schema("schema.json")
    response = generate_content_retry(["Question"], config=config)
"""

__name__ = "llm7shi"

from importlib.metadata import version
__version__ = version("llm7shi")

# Import main functions for convenience
from .gemini import (
    DEFAULT_MODEL,
    build_schema_from_json,
    config_from_schema,
    config_from_schema_string,
    generate_content_retry,
    generate_content_retry_with_thoughts,
    show_params,
    upload_file,
    delete_file,
)

from .terminal import (
    bold,
    convert_markdown,
    MarkdownStreamConverter,
)

__all__ = [
    "DEFAULT_MODEL",
    "build_schema_from_json",
    "config_from_schema",
    "config_from_schema_string",
    "generate_content_retry",
    "generate_content_retry_with_thoughts",
    "show_params",
    "upload_file",
    "delete_file",
    "bold",
    "convert_markdown",
    "MarkdownStreamConverter",
]
