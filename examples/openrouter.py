from llm7shi.compat import generate_with_schema

MODEL = "openrouter:moonshotai/kimi-k2.6:free"

print("=== include_thoughts=True ===")
generate_with_schema(["Hello, World!"], model=MODEL, include_thoughts=True)

print("\n=== include_thoughts=False ===")
generate_with_schema(["Hello, World!"], model=MODEL, include_thoughts=False)
