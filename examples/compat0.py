"""
Minimal proof of vendor neutrality: same call runs unmodified against cloud
(Gemini, OpenAI) and local (Ollama) backends, showing the compat layer removes
per-provider API differences. See also: compat1.py, compat2.py.
"""

import argparse
from llm7shi.compat import generate_with_schema
from args import parse_model_args

args = parse_model_args(argparse.ArgumentParser(description=__doc__))
generate_with_schema(["Hello, World!"], model=args.model)
