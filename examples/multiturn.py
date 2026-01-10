from llm7shi.compat import generate_with_schema, VENDOR_PREFIXES

# Multi-turn conversation using OpenAI-compatible message format
messages = [
    {"role": "system", "content": "You are a helpful assistant that answers questions concisely."},
    {"role": "user", "content": "What is the capital of France?"},
    {"role": "assistant", "content": "The capital of France is Paris."},
    {"role": "user", "content": "What is its population?"}
]

for i, model in enumerate(VENDOR_PREFIXES):
    if i:
        print("", "=" * 60, "", sep="\n")
    generate_with_schema(messages, model=model)
