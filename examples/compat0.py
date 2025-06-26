from llm7shi.compat import generate_with_schema

generate_with_schema(["Hello, World!"], model="gemini-2.5-flash")
print("=" * 40)
generate_with_schema(["Hello, World!"], model="gpt-4.1-mini")
