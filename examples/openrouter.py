"""
include_thoughts controls reasoning visibility via OpenRouter regardless of a
model's default behavior: kimi reasons unless told not to, gemma stays silent
unless asked. The nested loop over both models and both settings confirms the
toggle overrides each model's default consistently.
"""

from llm7shi.compat import generate_with_schema

# paired because they differ in default reasoning behavior: kimi reasons unless told not to, gemma stays silent unless asked
MODELS = [
    "openrouter:moonshotai/kimi-k2.6:free",
    "openrouter:google/gemma-4-31b-it:free",
]

for model in MODELS:
    for include_thoughts in [True, False]:  # confirms the toggle overrides each model's default behavior consistently
        print(f"=== {model} (include_thoughts={include_thoughts}) ===")
        generate_with_schema(["Hello, World!"], model=model, include_thoughts=include_thoughts)
        print()
