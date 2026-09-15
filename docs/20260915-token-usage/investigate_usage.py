"""Investigation script (temporary): dump dir() and repr() of the final
streaming chunk for each provider, to find where token usage info lives.

Usage:
    uv run investigate_usage.py -m ollama:qwen3.5:4b
    uv run investigate_usage.py -m google:gemma-4-31b-it
    uv run investigate_usage.py -m openai:gpt-5.6-luna
    uv run investigate_usage.py -m openai:gpt-5.6-luna --completion
    uv run investigate_usage.py -m openrouter:liquid/lfm-2.5-2.6b:free
"""
import argparse
import os
import re

from llm7shi.compat import OPENAI_COMPATIBLE_VENDORS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", required=True,
                         help="Model name with vendor prefix, e.g. google:gemini-2.5-flash")
    parser.add_argument("--completion", action="store_true",
                         help="For vendor=openai, use Chat Completions instead of the Responses API")
    args = parser.parse_args()

    match = re.match(r"([^:]+):(.*)", args.model)
    vendor, model = (match.group(1), match.group(2)) if match else ("google", args.model)

    chunks = []

    if vendor == "google":
        from google import genai
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        stream = client.models.generate_content_stream(model=model, contents=["hi"])
        for chunk in stream:
            chunks.append(chunk)

    elif vendor == "openai" and not args.completion:
        # Real OpenAI now goes through the Responses API (see llm7shi/openai.py),
        # not Chat Completions, so investigate that instead.
        from openai import OpenAI
        client = OpenAI()
        stream = client.responses.create(
            model=model,
            input=[{"role": "user", "content": [{"type": "input_text", "text": "hi"}]}],
            store=False,
            stream=True,
        )
        for chunk in stream:
            chunks.append(chunk)

    elif vendor == "openai" and args.completion:
        from openai import OpenAI
        client = OpenAI()
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            stream=True,
            stream_options={"include_usage": True},
        )
        for chunk in stream:
            chunks.append(chunk)

    elif vendor == "ollama":
        import ollama
        client = ollama.Client()
        stream = client.chat(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            stream=True,
        )
        for chunk in stream:
            chunks.append(chunk)

    elif vendor in OPENAI_COMPATIBLE_VENDORS:
        # OpenAI-compatible endpoints (OpenRouter etc.) use Chat Completions,
        # not the Responses API, and need stream_options to get usage at all.
        from openai import OpenAI
        vendor_config = OPENAI_COMPATIBLE_VENDORS[vendor]
        client = OpenAI(
            base_url=vendor_config["base_url"],
            api_key=os.environ.get(vendor_config["api_key_env"], ""),
        )
        stream = client.chat.completions.create(
            model=model or vendor_config["default_model"],
            messages=[{"role": "user", "content": "hi"}],
            stream=True,
            stream_options={"include_usage": True},
        )
        for chunk in stream:
            chunks.append(chunk)

    else:
        raise ValueError(f"Unsupported vendor: {vendor}")

    print(f"total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks[-2:], start=len(chunks) - len(chunks[-2:])):
        print(f"\n=== chunk[{i}] type: {type(chunk)} ===")
        print(dir(chunk))
        print(f"\n--- repr chunk[{i}] ---")
        print(chunk)


if __name__ == "__main__":
    main()
