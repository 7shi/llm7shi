"""
Simplicity-by-default demo: one function call, no config, yet streaming,
thinking-process display, and retry/error handling all come for free.
"""

from llm7shi import generate_content_retry

# No model specified: uses DEFAULT_MODEL from gemini.py
generate_content_retry(["Hello, World!"])
