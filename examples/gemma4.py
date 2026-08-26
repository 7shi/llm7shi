"""
Same open model (gemma-4-31b-it) hosted via Google, OpenRouter, and Ollama:
confirms the unified interface, including include_thoughts, behaves
identically regardless of hosting. For the raw per-provider API calls this
replaces, see ../docs/20260608-provider-apis.md.
"""

from llm7shi.compat import generate_with_schema

# same open model under 3 vendor prefixes, to show provider choice needs no code change
MODELS = [
    # google: can't actually suppress Gemma's reasoning; llm7shi discards the thought parts but the model still runs them server-side
    "google:gemma-4-31b-it",
    "openrouter:google/gemma-4-31b-it:free",
    "ollama:gemma4:31b-it-qat",
]

for model in MODELS:
    for include_thoughts in [True, False]:  # confirms the toggle behaves identically across all three backends
        print(f"=== {model} (include_thoughts={include_thoughts}) ===")
        generate_with_schema(["Hello, World!"], model=model, include_thoughts=include_thoughts)
        print()
