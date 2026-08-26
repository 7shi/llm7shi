from llm7shi import Client

# Initialize client with a model (using Ollama as default, matching multiturn.py)
client = Client(model="ollama:", include_thoughts=False)

# set via dedicated method, not the constructor, so model config and system role stay independently settable
system_prompt = "You are a helpful assistant that answers questions concisely."
client.set_system_prompt(system_prompt)

print("--- First turn: call with a system prompt ---")
# no print(response1) here: the client already echoes generation to the console
response1 = client(
    prompt="What is the capital of France?"
)

print("\n--- Second turn: history is managed automatically by the client ---")
response2 = client(
    prompt="What is its population?"
)

# The history can also be serialized to a flat XML string
print("\n--- XML History Log ---")
print(client.to_xml())
