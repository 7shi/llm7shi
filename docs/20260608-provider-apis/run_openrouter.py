import os
import argparse
from openai import OpenAI

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", required=True)
parser.add_argument("--no-think", action="store_true")
args = parser.parse_args()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

stream = client.chat.completions.create(
    model=args.model,
    messages=[{"role": "user", "content": "Hello, World!"}],
    stream=True,
    extra_body={"reasoning": {"enabled": not args.no_think}},
)

section = None
for chunk in stream:
    delta = chunk.choices[0].delta
    reasoning = getattr(delta, "reasoning", None)
    for label, text in [("thinking", reasoning), ("answer", delta.content)]:
        if not text:
            continue
        if section != label:
            section = label
            print(f"\n[{label}]")
        print(text, end="", flush=True)
print()
