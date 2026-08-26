# Standard library imports
import os, sys, json, time, re
from pathlib import Path
from typing import List, Optional, Any

# Google Gemini API imports
from google import genai
from google.genai import types

# Local imports for terminal formatting and response object
from .utils import do_show_params
from .response import Response
from .monitor import StreamProcessor
from .stream import StreamGenerator

# Available Gemini models
models = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

# Default model to use when none specified
DEFAULT_MODEL = models[0]

# Lazy singleton for Gemini API client — initialized on first use to avoid
# requiring GEMINI_API_KEY at import time when only other providers are used.
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    return _client

def _disable_afc(config):
    """Disable automatic function calling on a GenerateContentConfig.

    Avoids AFC warning: "Direct use of automatic function calling (AFC) in
    Models.generate_content_stream is not recommended..."
    """
    config.automatic_function_calling = types.AutomaticFunctionCallingConfig(disable=True)
    return config


# config_text is dynamically generated via __getattr__ to prevent mutation
def _make_config_text():
    return _disable_afc(types.GenerateContentConfig(
        response_mime_type="text/plain",
    ))


def build_schema_from_json(json_data):
    """Convert JSON schema definition to Gemini Schema object.
    
    Args:
        json_data: Dictionary containing JSON schema definition
        
    Returns:
        types.Schema: Gemini schema object for structured output
    """
    t = json_data.get("type")
    match t:
        case "object":
            # Recursively build schema for object properties
            properties = {}
            for prop_name, prop_data in json_data["properties"].items():
                properties[prop_name] = build_schema_from_json(prop_data)
            return types.Schema(
                type=types.Type.OBJECT,
                required=json_data.get("required", []),
                properties=properties
            )
        case "string":
            # String type with optional enum values
            schema = types.Schema(
                type=types.Type.STRING,
                description=json_data.get("description")
            )
            # Add enum constraint if specified
            if "enum" in json_data:
                schema.enum = json_data["enum"]
            return schema
        case "boolean":
            return types.Schema(
                type=types.Type.BOOLEAN,
                description=json_data.get("description")
            )
        case "number":
            schema = types.Schema(
                type=types.Type.NUMBER,
                minimum=json_data.get("minimum"),
                maximum=json_data.get("maximum"),
                description=json_data.get("description")
            )
            return schema
        case "integer":
            schema = types.Schema(
                type=types.Type.INTEGER,
                minimum=json_data.get("minimum"),
                maximum=json_data.get("maximum"),
                description=json_data.get("description")
            )
            return schema
        case "array":
            # Array type with recursive item schema
            return types.Schema(
                type=types.Type.ARRAY,
                description=json_data.get("description"),
                items=build_schema_from_json(json_data["items"])
            )
        case _:
            raise ValueError(f"Unsupported type: {t}")


def config_from_schema(schema):
    """Create GenerateContentConfig for JSON output with schema validation.
    
    Args:
        schema: types.Schema object defining the expected JSON structure
        
    Returns:
        types.GenerateContentConfig: Configuration for structured JSON output
    """
    return _disable_afc(types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
    ))
class GeminiStreamGenerator(StreamGenerator):
    """Gemini-specific stream generator."""

    def __init__(self, *args, include_thoughts: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.include_thoughts = include_thoughts

    def make_stream(self):
        return _get_client().models.generate_content_stream(
            model=self.model,
            config=self.config,
            contents=self.contents,
        )

    def process_chunk(self, chunk, processor) -> bool:
        if hasattr(chunk, "candidates") and chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
            for part in chunk.candidates[0].content.parts:
                if not part.text:
                    continue
                elif part.thought:
                    # Suppress thinking process output if include_thoughts=False
                    if self.include_thoughts and not processor.add_thought(part.text):
                        return False
                else:
                    if not processor.add_text(part.text):
                        return False
        else:
            if hasattr(chunk, "text") and chunk.text:
                if not processor.add_text(chunk.text):
                    return False
        return True

    def handle_error(self, e: Exception) -> Optional[dict]:
        # 429/500/502/503 are transient; other errors fail immediately (not retried)
        if isinstance(e, genai.errors.APIError) and hasattr(e, "code") and e.code in [429, 500, 502, 503]:
            delay = None
            if e.code == 429:
                # 429 carries an explicit retryDelay; other codes fall back to DEFAULT_RETRY_DELAY
                details = e.details["error"]["details"]
                for d in details:
                    if (rd := d.get("retryDelay")) and (m := re.match(r"^(\d+)s$", rd)):
                        delay = int(m.group(1))
                        break
            return {"status_code": e.code, "delay": delay}
        return None


def generate_content_retry(
    contents,
    *,
    model="",
    config=None,
    include_thoughts=True,
    thinking_budget=None,
    file=sys.stdout,
    show_params=True,
    max_length=None,
    check_repetition=True,
):
    """Generate content with retry logic and return a Response object."""
    # Use default model if none specified
    if not model:
        model = DEFAULT_MODEL
    
    # Display parameters if requested
    if show_params:
        # Call the show_params function (defined later in this module)
        do_show_params(contents, model=model, file=file)
    
    # Configure thinking process visibility for Gemini 2.5 models
    if include_thoughts or thinking_budget is not None:
        thinking_config = types.ThinkingConfig(include_thoughts=include_thoughts)
        if thinking_budget is not None:
            thinking_config.thinking_budget = thinking_budget
        
        # Create new config with thinking configuration
        if config is None:
            config = _make_config_text()
        config.thinking_config = thinking_config
    
    generator = GeminiStreamGenerator(
        model=model,
        config=config,
        contents=contents,
        file=file,
        max_length=max_length,
        check_repetition=check_repetition,
        include_thoughts=include_thoughts,
    )
    return generator.generate()


def upload_file(path, mime_type):
    """Upload file to Gemini API with explicit mime_type.

    Args:
        path: Path to the file to upload
        mime_type: MIME type of the file (e.g., 'image/jpeg', 'application/pdf')

    Returns:
        File object from Gemini API after processing is complete
    """
    # Gemini requires files to be uploaded first and referenced by name in requests
    # Upload file to Gemini
    file = _get_client().files.upload(
        file=path,
        config=types.UploadFileConfig(
            display_name=os.path.basename(path),
            mime_type=mime_type,
        ),
    )
    
    # Wait for file processing to complete
    while file.state.name == "PROCESSING":
        print("Waiting for file to be processed.")
        time.sleep(2)
        file = _get_client().files.get(name=file.name)
    
    return file


def delete_file(file):
    """Delete uploaded file from Gemini storage.

    Args:
        file: File object returned from upload_file()

    Returns:
        Delete operation result
    """
    return _get_client().files.delete(name=file.name)


def __getattr__(name):
    """Module-level attribute access handler.

    Exposes client lazily so external code can access llm7shi.gemini.client without
    requiring GEMINI_API_KEY at import time.
    Dynamically generates config_text on each access to prevent mutation issues.
    """
    if name == "client":
        return _get_client()
    if name == "config_text":
        return _make_config_text()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
