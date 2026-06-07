import argparse
import ollama

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", required=True)
parser.add_argument("--no-think", action="store_true")
args = parser.parse_args()

client = ollama.Client()

stream = client.chat(
    model=args.model,
    messages=[{"role": "user", "content": "Hello, World!"}],
    stream=True,
    think=not args.no_think,
)

section = None
for chunk in stream:
    for label, text in [
        ("thinking", chunk.message.thinking),
        ("answer", chunk.message.content),
    ]:
        if not text:
            continue
        if section != label:
            section = label
            print(f"\n[{label}]")
        print(text, end="", flush=True)
print()
