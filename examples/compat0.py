from llm7shi.compat import generate_with_schema

generate_with_schema(["Hello, World!"], model="google:gemini-2.5-flash")
print("", "=" * 60, "", sep="\n")
generate_with_schema(["Hello, World!"], model="openai:gpt-4o-mini")
