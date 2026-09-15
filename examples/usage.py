"""
Shows Response.usage: a Usage object with normalized fields (input_tokens,
output_tokens, reasoning_tokens, cached_tokens, total_tokens - None where a
provider doesn't report that dimension) plus the provider's untouched data in
.raw. Field names and shape vary per vendor - see docs/20260915-token-usage.md.
"""

import argparse
from llm7shi.compat import generate_with_schema
from args import parse_model_args

args = parse_model_args(argparse.ArgumentParser(description=__doc__))
response = generate_with_schema(["What is the capital of France?"], model=args.model)

# repr() shows the normalized fields only; .raw is the provider's untouched data
print("\nusage:", response.usage)

if response.usage:
    # the one aggregate that generalizes cleanly across all providers
    # (summed for Ollama, which reports no total)
    print("usage.total_tokens:", response.usage.total_tokens)
    print("usage.input_tokens:", response.usage.input_tokens)
    print("usage.output_tokens:", response.usage.output_tokens)
    print("usage.reasoning_tokens:", response.usage.reasoning_tokens)
    print("usage.cached_tokens:", response.usage.cached_tokens)

    # the provider's dict, untouched
    print("usage.raw:", response.usage.raw)
