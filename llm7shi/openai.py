import sys
from typing import List, Dict, Any
from openai import OpenAI

from .response import Response
from .terminal import MarkdownStreamConverter
from .monitor import StreamMonitor, GptOssTemplateFilter

DEFAULT_MODEL = "gpt-4.1-mini"


def generate_content(
    messages: List[Dict[str, Any]],
    model: str = "",
    file=sys.stdout,
    max_length=None,
    check_repetition: bool = True,
    base_url: str = None,
    **kwargs
) -> Response:
    """Generate with OpenAI API with streaming and monitoring."""

    # Use default model if not provided
    if not model:
        model = DEFAULT_MODEL

    # Detect if model uses gpt-oss template (needs filtering)
    # Only activate filter for exact match of "llama.cpp/gpt-oss"
    needs_gpt_oss_filter = (model == "llama.cpp/gpt-oss")

    # Create OpenAI client (with optional base_url for custom endpoints)
    client = OpenAI(base_url=base_url) if base_url else OpenAI()

    # Call API with streaming
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        **kwargs
    )

    # Collect streamed response and chunks
    collected_content = ""
    thoughts = ""
    thoughts_shown = False  # Track if thinking header was shown
    answer_shown = False  # Track if answer header was shown
    chunks = []
    converter = MarkdownStreamConverter()  # For terminal formatting
    content_filter = GptOssTemplateFilter() if needs_gpt_oss_filter else None
    monitor = StreamMonitor(converter, max_length=max_length, check_repetition=check_repetition)

    # Track previous lengths for incremental display
    previous_thoughts_len = 0
    previous_text_len = 0

    for chunk in response:
        chunks.append(chunk)
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content

            # Apply filter if present
            if content_filter:
                content_filter.feed(content)

                # Get incremental thoughts (analysis channel)
                current_thoughts = content_filter.thoughts
                if len(current_thoughts) > previous_thoughts_len:
                    # Show thinking header on first thought
                    if not thoughts_shown:
                        if file:
                            print(converter.feed("🤔 **Thinking...**\n"), file=file)
                        thoughts_shown = True

                    # Output new thoughts
                    new_thoughts = current_thoughts[previous_thoughts_len:]
                    if file:
                        print(converter.feed(new_thoughts), end='', flush=True, file=file)
                    previous_thoughts_len = len(current_thoughts)

                # Get incremental text (final channel)
                current_text = content_filter.text
                if len(current_text) > previous_text_len:
                    # Show answer header when switching from thoughts to answer
                    if thoughts_shown and not answer_shown:
                        if file:
                            # Add newline if thoughts don't end with one
                            if content_filter.thoughts and not content_filter.thoughts.endswith('\n'):
                                print(file=file)
                            print(converter.feed("\n💡 **Answer:**\n"), file=file)
                        answer_shown = True

                    # Output new text
                    new_text = current_text[previous_text_len:]
                    if file:
                        print(converter.feed(new_text), end='', flush=True, file=file)
                    previous_text_len = len(current_text)

                # Update stored values
                thoughts = current_thoughts
                collected_content = current_text
            else:
                # No filter: direct passthrough
                collected_content += content
                if file:
                    print(converter.feed(content), end='', flush=True, file=file)

            # Check for repetition and max length
            if not monitor.check(collected_content, file):
                response.close()  # Close stream connection
                break

    # Flush filter if present
    if content_filter:
        content_filter.flush()

        # Output any remaining thoughts
        if len(content_filter.thoughts) > previous_thoughts_len:
            if not thoughts_shown:
                if file:
                    print(converter.feed("🤔 **Thinking...**\n"), file=file)
            new_thoughts = content_filter.thoughts[previous_thoughts_len:]
            if file:
                print(converter.feed(new_thoughts), end='', flush=True, file=file)

        # Output any remaining text
        if len(content_filter.text) > previous_text_len:
            if thoughts_shown and not answer_shown:
                if file:
                    # Add newline if thoughts don't end with one
                    if content_filter.thoughts and not content_filter.thoughts.endswith('\n'):
                        print(file=file)
                    print(converter.feed("\n💡 **Answer:**\n"), file=file)
            new_text = content_filter.text[previous_text_len:]
            if file:
                print(converter.feed(new_text), end='', flush=True, file=file)

        # Update final values
        thoughts = content_filter.thoughts
        collected_content = content_filter.text

    # Flush any remaining markdown formatting
    remaining = converter.flush()
    if remaining and file:
        print(remaining, end='', flush=True, file=file)

    # Ensure output ends with newline
    if file and not collected_content.endswith("\n"):
        print(flush=True, file=file)

    # Create Response object for OpenAI
    return Response(
        model=model,
        config=kwargs,
        contents=messages,
        response=response,
        chunks=chunks,
        thoughts=thoughts,
        text=collected_content,
        repetition=monitor.repetition_detected,
        max_length=monitor.max_length_exceeded,
    )
