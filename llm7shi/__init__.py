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
    config_text,
    generate_content_retry,
    upload_file,
    delete_file,
)

from .response import Response

from .terminal import (
    bold,
    convert_markdown,
    MarkdownStreamConverter,
)

from .utils import (
    do_show_params,
    contents_to_openai_messages,
    add_additional_properties_false,
    inline_defs,
    extract_descriptions,
    create_json_descriptions_prompt,
    is_openai_messages,
    openai_messages_to_contents,
)

from .monitor import (
    StreamMonitor,
    detect_repetition,
)

__all__ = [
    # gemini.py
    "DEFAULT_MODEL",
    "build_schema_from_json",
    "config_from_schema",
    "config_text",
    "generate_content_retry",
    "upload_file",
    "delete_file",
    # response.py
    "Response",
    # terminal.py
    "bold",
    "convert_markdown",
    "MarkdownStreamConverter",
    # utils.py
    "do_show_params",
    "contents_to_openai_messages",
    "add_additional_properties_false",
    "inline_defs",
    "extract_descriptions",
    "create_json_descriptions_prompt",
    "is_openai_messages",
    "openai_messages_to_contents",
    # monitor.py
    "StreamMonitor",
    "detect_repetition",
]
