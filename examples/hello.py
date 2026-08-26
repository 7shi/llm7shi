"""
Simplicity-by-default demo: one function call, no config, yet streaming,
thinking-process display, and retry/error handling all come for free.
"""

from llm7shi import generate_content_retry

generate_content_retry(["Hello, World!"])
