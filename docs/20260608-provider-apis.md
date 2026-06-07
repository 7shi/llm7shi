# Raw Provider APIs Behind the Wrapper

This document shows the raw API code that llm7shi wraps. The same model — Gemma 4 31B-it — is available from three providers (Google's Gemini API, OpenRouter, and Ollama), yet each exposes a completely different API. Seeing the three side by side makes concrete what the wrapper actually hides.

In every script the prompt is `"Hello, World!"`, thinking is enabled by default (pass `--no-think` to disable it), and the thinking and answer sections are separated with `[thinking]` / `[answer]` labels. The model is given with `-m`/`--model`. Each provider below links to its runnable script rather than reproducing the code inline, and shows the command used and the actual output instead.

## Google (Gemini API)

Script: [run_google.py](20260608-provider-apis/run_google.py)

- **Client**: `genai.Client`, from the dedicated `google-genai` SDK.
- **Enabling thinking**: nest `ThinkingConfig(include_thoughts=True)` inside `GenerateContentConfig`.
- **Distinguishing thinking from answer**: each chunk carries `chunk.candidates[0].content.parts`; a part is thinking when `part.thought` is `True`, otherwise it is the answer. The text is in `part.text`.

```
$ uv run docs/20260608-provider-apis/run_google.py -m gemma-4-31b-it

[thinking]
The user said "Hello, World!".
This is the classic first program output in almost every programming language. It's a friendly greeting and a common way to start an interaction or test a system.

    *   Acknowledge the greeting.
    *   Match the friendly, slightly "techy" tone.
    *   Offer assistance.
    *   (Optional) Add a playful nod to the coding tradition.

    *   *Simple:* "Hello! How can I help you today?"
    *   *Playful/Techy:* "Hello, World! 🌍 It looks like we've successfully initialized. How can I assist you today?"
    *   *Detailed:* "Hello! That's the classic first line of code. Are you learning to program, or just saying hi?"
[answer]
Hello, World! 🌍

It looks like we've successfully initialized. How can I help you today?
```

## OpenRouter

Script: [run_openrouter.py](20260608-provider-apis/run_openrouter.py)

- **Client**: the OpenAI SDK reused with a `base_url` (an OpenAI-compatible API).
- **Enabling thinking**: although the call uses the OpenAI library, reasoning is *not* part of the OpenAI API — it is an OpenRouter-specific extension. There is no standard OpenAI parameter for it, which is why it must be smuggled in through `extra_body` as `{"reasoning": {"enabled": True}}` rather than passed as a normal keyword argument.
- **Distinguishing thinking from answer**: each chunk carries `chunk.choices[0].delta`; thinking is in `delta.reasoning`, which is likewise an OpenRouter addition absent from the standard OpenAI response (hence the defensive `getattr(delta, "reasoning", None)`), while the answer is in the standard `delta.content`.

```
$ uv run docs/20260608-provider-apis/run_openrouter.py -m google/gemma-4-31b-it:free

[thinking]
The user said "Hello, World!".
This is the classic first program written in almost every programming language. It's a greeting and a test of functionality.

    *   Acknowledge the greeting.
    *   Respond in a friendly, helpful manner.
    *   Possibly play along with the "coding" theme or keep it simple.

    *   *Option 1 (Simple):* "Hello! How can I help you today?"
    *   *Option 2 (Playful/Coding):* "Hello, World! 🌍 It looks like we're successfully initialized. How can I assist you?"
    *   *Option 3 (Detailed):* "Hello! That's the classic first line of code. Are you learning to program, or just saying hi?"
[answer]
Hello, World! 🌍 How can I help you today?
```

## Ollama

Script: [run_ollama.py](20260608-provider-apis/run_ollama.py)

- **Client**: the local `ollama.Client`; no API key required.
- **Enabling thinking**: the `think=True` argument to `chat()`.
- **Distinguishing thinking from answer**: each chunk carries `chunk.message`; thinking is in `chunk.message.thinking`, the answer is in `chunk.message.content`.

```
$ uv run docs/20260608-provider-apis/run_ollama.py -m gemma4:31b-it-qat

[thinking]
The user said "Hello, World!".
This is a classic greeting and often the first output in programming tutorials.

    *   Friendly acknowledgement.
    *   Reciprocation of the greeting.
    *   Optional: Acknowledging the programming reference (the "Hello, World!" tradition).
[answer]
Hello! How can I help you today?
```

## Summary of the Differences

Calling the same Gemma 4 model, the three providers diverge on every axis:

| | Google | OpenRouter | Ollama |
|---|---|---|---|
| Client creation | `genai.Client(api_key=...)` | `OpenAI(base_url=..., api_key=...)` | `ollama.Client()` |
| Enabling thinking | `ThinkingConfig(include_thoughts=True)` | `extra_body={"reasoning": {"enabled": True}}` | `think=True` |
| Thinking field | check `part.thought` → `part.text` | `delta.reasoning` | `chunk.message.thinking` |
| Answer field | `part.text` | `delta.content` | `chunk.message.content` |

Switching providers means rewriting all of these by hand.

## What llm7shi Replaces

llm7shi hides these differences behind a single call. The provider is selected with a vendor prefix on the model name:

```python
from llm7shi.compat import generate_with_schema

MODELS = [
    "google:gemma-4-31b-it",
    "openrouter:google/gemma-4-31b-it:free",
    "ollama:gemma4:31b-it-qat",
]

for model in MODELS:
    for include_thoughts in [True, False]:
        print(f"=== {model} (include_thoughts={include_thoughts}) ===")
        generate_with_schema(["Hello, World!"], model=model, include_thoughts=include_thoughts)
        print()
```

The client creation, thinking-enablement, and thinking/answer extraction shown above are dispatched internally to per-provider implementations (`llm7shi/gemini.py`, `llm7shi/openai.py`, `llm7shi/ollama.py`). The display work the raw snippets did by hand — labeling sections and streaming to stdout — is handled automatically, with `🤔 Thinking...` / `💡 Answer:` headers in place of the `[thinking]` / `[answer]` labels.

## Caveat: Disabling Reasoning Is Not Uniform

`include_thoughts=False` is meant to stop reasoning entirely, not just hide it, but the providers honor this differently.

A genuine Gemini model such as `gemini-2.5-flash` honors `--no-think` cleanly. With reasoning disabled, no thought parts come back and only the answer is produced:

```
$ uv run docs/20260608-provider-apis/run_google.py -m gemini-2.5-flash --no-think

[answer]
Hello, World to you too! 👋

How can I help you today?
```

Gemma, reached through the same Gemini API, ignores the flag. Passing `--no-think` sets `ThinkingConfig(include_thoughts=False)`, yet the model still returns thought parts (`part.thought=True`):

```
$ uv run docs/20260608-provider-apis/run_google.py -m gemma-4-31b-it --no-think

[thinking]
The user said "Hello, World!".
This is the classic first program in almost every programming language. It's a greeting.
Respond politely, warmly, and perhaps acknowledge the "coding" nature of the phrase.

    *   Option 1: "Hello! How can I help you today?" (Simple, professional)
    *   Option 2: "Hello, World! It's great to meet you. What's on your mind?" (Friendly, mirror)
    *   Option 3: "print('Hello, World!') - Hello! How can I assist you?" (Playful, coding-themed)
[answer]
Hello, World! 🌍 How can I help you today?
```

The thinking section is still there despite `--no-think`. llm7shi discards these parts client-side so they do not leak into the answer, but the model keeps reasoning server-side (with its cost and latency), which the client cannot prevent. The `thinking_budget` parameter does not help either — `thinking_budget=0` is rejected with `400 INVALID_ARGUMENT: Thinking budget is not supported for this model.`

OpenRouter and Ollama also suppress reasoning correctly. The inability to disable reasoning is therefore specific to using Gemma through the Gemini API.

Related: [20260607-openrouter-reasoning.md](20260607-openrouter-reasoning.md) (OpenRouter reasoning control), [examples/gemma4.md](../examples/gemma4.md) (the English example walkthrough).
