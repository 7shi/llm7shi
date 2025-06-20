import os, sys, json, time, re
from pathlib import Path
from google import genai
from google.genai import types
from .terminal import convert_markdown, MarkdownStreamConverter

models = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

default_model = models[0]

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

config_text = types.GenerateContentConfig(
    response_mime_type="text/plain",
)

def build_schema_from_json(json_data):
    t = json_data.get("type")
    match t:
        case "object":
            properties = {}
            for prop_name, prop_data in json_data["properties"].items():
                properties[prop_name] = build_schema_from_json(prop_data)
            return genai.types.Schema(
                type=genai.types.Type.OBJECT,
                required=json_data.get("required", []),
                properties=properties
            )
        case "string":
            schema = genai.types.Schema(
                type=genai.types.Type.STRING,
                description=json_data.get("description", "")
            )
            # Enum support
            if "enum" in json_data:
                schema.enum = json_data["enum"]
            return schema
        case "boolean":
            return genai.types.Schema(
                type=genai.types.Type.BOOLEAN,
                description=json_data.get("description", "")
            )
        case "number":
            return genai.types.Schema(
                type=genai.types.Type.NUMBER,
                description=json_data.get("description", "")
            )
        case "integer":
            return genai.types.Schema(
                type=genai.types.Type.INTEGER,
                description=json_data.get("description", "")
            )
        case "array":
            return genai.types.Schema(
                type=genai.types.Type.ARRAY,
                description=json_data.get("description", ""),
                items=build_schema_from_json(json_data["items"])
            )
        case _:
            raise ValueError(f"Unsupported type: {t}")

def config_from_schema_string(schema_content: str):
    """Create GenerateContentConfig from schema string
    
    Args:
        schema_content: JSON schema as string
    
    Returns:
        types.GenerateContentConfig
    """
    schema_dict = json.loads(schema_content)
    schema = build_schema_from_json(schema_dict)
    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
    )


def config_from_schema(schema_filename):
    with open(schema_filename, 'r', encoding='utf-8') as f:
        schema_content = f.read()
    
    return config_from_schema_string(schema_content)

def generate_content_retry_with_thoughts(contents, *, model=None, config=None, include_thoughts=True, thinking_budget=None, file=sys.stdout):
    """Generate content with retry logic and return both thoughts and text as a tuple.
    
    Args:
        contents: The content to send
        model: The model to use (default: None)
        config: GenerateContentConfig object (default: None)
        include_thoughts: Whether to include thoughts in the response
        thinking_budget: Optional thinking budget
        file: Output file for streaming content (default: sys.stdout, None to disable)
    
    Returns:
        tuple: (thoughts, text) where thoughts is the thinking process and text is the final answer
    """
    # Add thinking configuration to config if requested
    if include_thoughts or thinking_budget is not None:
        thinking_config = types.ThinkingConfig(include_thoughts=include_thoughts)
        if thinking_budget is not None:
            thinking_config.thinking_budget = thinking_budget
        
        # Create new config with thinking configuration
        if config is None:
            config = types.GenerateContentConfig()
        config.thinking_config = thinking_config
    
    for attempt in range(5, 0, -1):
        try:
            response = client.models.generate_content_stream(
                model=model or default_model,
                config=config,
                contents=contents,
            )
            text = ""
            thoughts = ""
            thoughts_shown = False
            answer_shown = False
            converter = MarkdownStreamConverter()
            
            for chunk in response:
                if hasattr(chunk, "candidates") and chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                    for part in chunk.candidates[0].content.parts:
                        if not part.text:
                            continue
                        elif include_thoughts and part.thought:
                            if not thoughts_shown:
                                if file:
                                    print(converter.feed("\n🤔 **Thinking...**\n"), file=file)
                                thoughts_shown = True
                            thoughts += part.text
                        else:
                            if thoughts_shown and not answer_shown:
                                if file:
                                    print(converter.feed("💡 **Answer:**\n"), file=file)
                                answer_shown = True
                            text += part.text
                        # Convert markdown formatting for output
                        if file:
                            print(converter.feed(part.text), end="", flush=True, file=file)
                else:
                    # Fallback for older API responses
                    if hasattr(chunk, "text") and chunk.text:
                        text += chunk.text
                        # Convert markdown formatting for output
                        if file:
                            print(converter.feed(chunk.text), end="", flush=True, file=file)
            
            # Flush any remaining content
            remaining = converter.flush()
            if remaining and file:
                print(remaining, end="", flush=True, file=file)
            
            if file and not text.endswith("\n"):
                print(flush=True, file=file)  # Final newline
            return (thoughts, text)
        except genai.errors.APIError as e:
            if hasattr(e, "code") and e.code in [429, 500, 502, 503]:
                print(e, file=sys.stderr)
                # Skip waiting for the last attempt
                if attempt == 1:
                    continue
                delay = 15
                if e.code == 429:
                    details = e.details["error"]["details"]
                    if [rd for d in details if (rd := d.get("retryDelay"))]:
                        if m := re.match(r"^(\d+)s$", rd):
                            delay = int(m.group(1)) or delay
                for i in range(delay, -1, -1):
                    print(f"\rRetrying... {i}s ", end="", file=sys.stderr, flush=True)
                    time.sleep(1)
                print(file=sys.stderr)
                continue
            else:
                raise
    raise RuntimeError("Max retries exceeded.")


def generate_content_retry(contents, *, model=None, config=None, include_thoughts=True, thinking_budget=None, file=sys.stdout):
    """Compatibility wrapper for generate_content_retry_with_thoughts.
    
    This function maintains backward compatibility by returning only the text portion.
    
    Args:
        contents: The content to send
        model: The model to use (default: None)
        config: GenerateContentConfig object (default: None)
        include_thoughts: Whether to include thoughts in the response
        thinking_budget: Optional thinking budget
        file: Output file for streaming content (default: sys.stdout, None to disable)
    
    Returns:
        str: The generated text (without thoughts)
    """
    _, text = generate_content_retry_with_thoughts(
        contents,
        model=model,
        config=config,
        include_thoughts=include_thoughts,
        thinking_budget=thinking_budget,
        file=file
    )
    return text

def show_params(f, model, uri, prompt):
    print("- model:", model, file=f)
    print("- uri  :", uri, file=f)
    print(file=f)
    for line in prompt.splitlines():
        print(">", line, file=f)
    print(file=f)

def upload_file(path, mime_type):
    """Upload file to Gemini API with explicit mime_type"""
    file = client.files.upload(
        file=path,
        config=types.UploadFileConfig(
            display_name=os.path.basename(path),
            mime_type=mime_type,
        ),
    )
    while file.state.name == "PROCESSING":
        print("Waiting for file to be processed.")
        time.sleep(2)
        file = client.files.get(name=file.name)
    return file

def delete_file(file):
    """Delete uploaded file"""
    return client.files.delete(name=file.name)
