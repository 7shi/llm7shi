import os
import argparse
from google import genai
from google.genai import types

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", required=True)
parser.add_argument("--no-think", action="store_true")
args = parser.parse_args()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(include_thoughts=not args.no_think),
)

stream = client.models.generate_content_stream(
    model=args.model,
    contents="Hello, World!",
    config=config,
)

section = None
for chunk in stream:
    for part in chunk.candidates[0].content.parts:
        if not part.text:
            continue
        label = "thinking" if part.thought else "answer"
        if section != label:
            section = label
            print(f"\n[{label}]")
        print(part.text, end="", flush=True)
print()
