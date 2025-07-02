from llm7shi.compat import generate_with_schema

models = [
    "google:gemini-2.5-flash",
    "openai:gpt-4o-mini",
    "ollama:qwen3:4b"
]

for i, model in enumerate(models):
    if i:
        print("", "=" * 60, "", sep="\n")
    generate_with_schema(["Hello, World!"], model=model)
