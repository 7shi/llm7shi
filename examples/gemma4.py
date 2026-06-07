from llm7shi.compat import generate_with_schema

MODELS = [
    "google:gemma-4-31b-it",
    "openrouter:google/gemma-4-31b-it:free",
    "ollama:gemma4:31b-it-qat",
]

for model in MODELS:
    for include_thoughts in [True, False]:
        print(f"=== {model} (include_thoughts={include_thoughts}) ===")
        generate_with_schema(["Hello, World!"], model=model, include_thoughts=include_thoughts)
        print()
