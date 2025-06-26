# Standard library imports
import os, sys, json, time, re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Any

# Google Gemini API imports
from google import genai
from google.genai import types

# Local imports for terminal formatting
from .terminal import convert_markdown, MarkdownStreamConverter
from .utils import do_show_params


@dataclass
class Response:
    """Response object containing the results from generate_content_retry.
    
    Attributes:
        model: The model used for generation
        config: The GenerateContentConfig used
        contents: The input contents sent to the API
        response: The raw API response object
        chunks: List of all streaming chunks received
        thoughts: The thinking process text (if include_thoughts=True)
        text: The final generated text
    """
    model: Optional[str] = None
    config: Optional[types.GenerateContentConfig] = None
    contents: Optional[List[Any]] = None
    response: Optional[Any] = None
    chunks: List[Any] = field(default_factory=list)
    thoughts: str = ""
    text: str = ""
    
    def __str__(self) -> str:
        """Return the text content when converting to string."""
        return self.text
    
    def __repr__(self) -> str:
        """Return a concise representation showing contents and text."""
        if self.contents is None:
            contents_repr = "None"
        else:
            contents_repr = str(self.contents[0])
            if len(contents_repr) > 10:
                contents_repr = contents_repr[:10] + "..."
        
        text_repr = self.text
        if len(text_repr) > 10:
            text_repr = text_repr[:10] + "..."
        
        return f"Response(contents={contents_repr!r}, text={text_repr!r})"

# Available Gemini models
models = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

# Default model to use when none specified
DEFAULT_MODEL = models[0]

# Initialize Gemini API client with API key from environment
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# Default configuration for plain text responses
config_text = types.GenerateContentConfig(
    response_mime_type="text/plain",
)


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
                description=json_data.get("description", "")
            )
            # Add enum constraint if specified
            if "enum" in json_data:
                schema.enum = json_data["enum"]
            return schema
        case "boolean":
            return types.Schema(
                type=types.Type.BOOLEAN,
                description=json_data.get("description", "")
            )
        case "number":
            return types.Schema(
                type=types.Type.NUMBER,
                description=json_data.get("description", "")
            )
        case "integer":
            return types.Schema(
                type=types.Type.INTEGER,
                description=json_data.get("description", "")
            )
        case "array":
            # Array type with recursive item schema
            return types.Schema(
                type=types.Type.ARRAY,
                description=json_data.get("description", ""),
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
    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
    )


def generate_content_retry(contents, *, model=None, config=None, include_thoughts=True, thinking_budget=None, file=sys.stdout, show_params=True):
    """Generate content with retry logic and return a Response object.
    
    Args:
        contents: The content to send
        model: The model to use (default: None)
        config: GenerateContentConfig object (default: None)
        include_thoughts: Whether to include thoughts in the response
        thinking_budget: Optional thinking budget
        file: Output file for streaming content (default: sys.stdout, None to disable)
        show_params: Whether to display parameters before generation (default: False)
    
    Returns:
        Response: Object containing thoughts, text, response, and chunks
    """
    # Use default model if none specified
    if model is None:
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
            config = types.GenerateContentConfig()
        config.thinking_config = thinking_config
    
    # Retry loop with exponential backoff for API errors
    for attempt in range(5, 0, -1):
        try:
            # Stream response from Gemini API
            response = client.models.generate_content_stream(
                model=model,
                config=config,
                contents=contents,
            )
            
            # Initialize response tracking variables
            text = ""  # Final answer text
            thoughts = ""  # Thinking process text
            thoughts_shown = False  # Track if thinking header was shown
            answer_shown = False  # Track if answer header was shown
            converter = MarkdownStreamConverter()  # For terminal formatting
            chunks = []  # Collect all chunks
            
            # Process streaming response chunks
            for chunk in response:
                chunks.append(chunk)
                if hasattr(chunk, "candidates") and chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                    for part in chunk.candidates[0].content.parts:
                        if not part.text:
                            continue
                        elif include_thoughts and part.thought:
                            # Handle thinking process output
                            if not thoughts_shown:
                                if file:
                                    print(converter.feed("\n🤔 **Thinking...**\n"), file=file)
                                thoughts_shown = True
                            thoughts += part.text
                        else:
                            # Handle final answer output
                            if thoughts_shown and not answer_shown:
                                if file:
                                    print(converter.feed("💡 **Answer:**\n"), file=file)
                                answer_shown = True
                            text += part.text
                        # Stream formatted output to terminal
                        if file:
                            print(converter.feed(part.text), end="", flush=True, file=file)
                else:
                    # Fallback for older API response format
                    if hasattr(chunk, "text") and chunk.text:
                        text += chunk.text
                        # Stream formatted output to terminal
                        if file:
                            print(converter.feed(chunk.text), end="", flush=True, file=file)
            
            # Flush any remaining markdown formatting
            remaining = converter.flush()
            if remaining and file:
                print(remaining, end="", flush=True, file=file)
            
            # Ensure output ends with newline
            if file and not text.endswith("\n"):
                print(flush=True, file=file)
            
            return Response(
                model=model,
                config=config,
                contents=contents,
                response=response,
                chunks=chunks,
                thoughts=thoughts,
                text=text,
            )
        except genai.errors.APIError as e:
            # Handle retryable API errors (rate limit, server errors)
            if hasattr(e, "code") and e.code in [429, 500, 502, 503]:
                print(e, file=sys.stderr)
                # Skip waiting on last attempt
                if attempt == 1:
                    continue
                
                # Calculate retry delay
                delay = 15  # Default delay in seconds
                if e.code == 429:  # Rate limit error
                    # Extract retry delay from error details if available
                    details = e.details["error"]["details"]
                    if [rd for d in details if (rd := d.get("retryDelay"))]:
                        if m := re.match(r"^(\d+)s$", rd):
                            delay = int(m.group(1)) or delay
                
                # Countdown with progress display
                for i in range(delay, -1, -1):
                    print(f"\rRetrying... {i}s ", end="", file=sys.stderr, flush=True)
                    time.sleep(1)
                print(file=sys.stderr)
                continue
            else:
                # Re-raise non-retryable errors
                raise
    raise RuntimeError("Max retries exceeded.")


def upload_file(path, mime_type):
    """Upload file to Gemini API with explicit mime_type.
    
    Args:
        path: Path to the file to upload
        mime_type: MIME type of the file (e.g., 'image/jpeg', 'application/pdf')
        
    Returns:
        File object from Gemini API after processing is complete
    """
    # Upload file to Gemini
    file = client.files.upload(
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
        file = client.files.get(name=file.name)
    
    return file


def delete_file(file):
    """Delete uploaded file from Gemini storage.
    
    Args:
        file: File object returned from upload_file()
        
    Returns:
        Delete operation result
    """
    return client.files.delete(name=file.name)
