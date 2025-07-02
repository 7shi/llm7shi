from llm7shi.compat import generate_with_schema, VENDOR_PREFIXES

for i, model in enumerate(VENDOR_PREFIXES):
    if i:
        print("", "=" * 60, "", sep="\n")
    generate_with_schema(["Hello, World!"], model=model)
