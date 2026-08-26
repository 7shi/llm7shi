"""
Minimal proof of vendor neutrality: same call runs unmodified against cloud
(Gemini, OpenAI) and local (Ollama) backends, showing the compat layer removes
per-provider API differences. See also: compat1.py, compat2.py.
"""

from llm7shi.compat import generate_with_schema

generate_with_schema(["Hello, World!"], model="ollama:")
