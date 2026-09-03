"""
Plain List[str] prompts can't represent multi-turn history. OpenAI-style
role-based messages (system/user/assistant) are accepted instead and mapped
uniformly onto each provider's native format (e.g. assistant -> Gemini's
"model" role), so conversational apps don't need provider-specific code.
"""

import argparse
from llm7shi.compat import generate_with_schema
from args import parse_model_args

args = parse_model_args(argparse.ArgumentParser(description=__doc__))

# Multi-turn conversation using OpenAI-compatible message format
messages = [
    # system prompt embedded as a message, not a separate parameter, so conversation structure is self-contained
    {"role": "system", "content": "You are a helpful assistant that answers questions concisely."},
    {"role": "user", "content": "What is the capital of France?"},
    # "assistant" is mapped to Gemini's "model" role internally, so the same message works across providers
    {"role": "assistant", "content": "The capital of France is Paris."},
    {"role": "user", "content": "What is its population?"}
]

generate_with_schema(messages, model=args.model)
