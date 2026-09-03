# Responses API for OpenAI Reasoning Summaries

This document explains why `openai.py` grew a second transport (the Responses API, alongside Chat Completions), how the routing rule was arrived at, and what was deliberately left out.

## Background

Chat Completions never exposes a reasoning/thinking process for standard OpenAI reasoning models (o1/o3/o4/gpt-5 family). This is unlike OpenAI-compatible providers reached through the same `openai.py` module — OpenRouter, for instance, streams thinking via a `delta.reasoning` field on the chat completion chunk (see [20260607-openrouter-reasoning.md](20260607-openrouter-reasoning.md)) — but real OpenAI has no equivalent field on that endpoint. The Responses API does expose it, as `response.reasoning_summary_text.delta` events, so getting a reasoning summary out of `openai:` models meant adding a second `StreamGenerator` that speaks that API and routing some calls to it.

The `codex-oauth/codex_oauth.py` reference script (a separate project's raw Responses API client using OpenAI's WHAM backend) supplied the shape to imitate: `client.responses.create(reasoning={"effort": ..., "summary": "auto"}, stream=True)`, with `response.reasoning_summary_text.delta`/`.done` for the summary and `response.output_text.delta` for the answer.

## Evolution of the Routing Rule

### Attempt 1: switch every `openai:` call, unconditionally

The most direct idea — route all `openai:` calls through the Responses API — was rejected immediately. `openai.py`'s `generate_content()` is shared by every OpenAI-*compatible* endpoint too (llama.cpp, LocalAI, OpenRouter, Groq, ...) via the `base_url` parameter, and none of those servers implement the Responses API. A blanket switch would have broken all of them.

### Attempt 2: whitelist reasoning-capable models

The next design gated the new transport on two conditions: `base_url is None` (real OpenAI) *and* the model name matching a reasoning-family pattern (`^(o\d|gpt-5)`, later trimmed to drop a redundant `codex` alternative — `gpt-5.1-codex-mini` already matches `gpt-5`). This kept the blast radius small: only reasoning models switched transport, so every existing Chat-Completions-based test kept working untouched.

This is also where `reasoning_effort` was first considered as an addition to the existing `include_thoughts` boolean, and rejected in that form: `include_thoughts` is a cross-provider on/off toggle (Gemini, Ollama, OpenRouter all understand it as a bool), so overloading it with an effort string would have been meaningful only for OpenAI. The existing precedent — `thinking_budget`, a Gemini-only parameter that rides alongside `include_thoughts` rather than replacing it — pointed at adding `reasoning_effort` as its own parameter instead.

### Attempt 3: destination decides transport, not the model

The whitelist was ultimately replaced with a simpler rule: **the transport is decided by destination alone**. Whenever `base_url` is unset (real OpenAI), every call goes through the Responses API, regardless of which model it names — a `gpt-4.1-mini` call gets the same transport as an `o3-mini` one. Calls with `base_url` set keep using Chat Completions unconditionally, since compatible servers don't implement Responses at all.

The model name still matters, but only for the `reasoning` request param, which the Responses API rejects outright on legacy (non-reasoning) models. This became `NON_REASONING_MODEL_RE`, a *blacklist* (`^gpt-[34]`) rather than the earlier whitelist — deliberately inverted so a new model family (a hypothetical `gpt-6`, more `o`-series entries) is treated as reasoning-capable by default, without a code change, instead of silently falling back to no summary until the pattern is updated.

```python
# llm7shi/openai.py
if not USE_COMPLETION and base_url is None:
    ...
    if include_thoughts and not NON_REASONING_MODEL_RE.match(model):
        responses_kwargs["reasoning"] = {"effort": reasoning_effort or "medium", "summary": "auto"}
```

`USE_COMPLETION` (default `False`) is the module-level escape hatch this design still needed: a single flag to fall back to Chat Completions everywhere against real OpenAI, for if the Responses API path misbehaves in practice. `examples/args.py` exposes it as `--completion` for the example scripts.

## Message and Schema Translation

The Responses API's request shape differs enough from Chat Completions that `openai.py` carries small translation helpers rather than building it inline:

- `_messages_to_responses_input()` splits the flat `role`/`content` message list into `instructions` (the system message) and `input` items, wrapping user/assistant content in `input_text`/`output_text` parts as the API requires.
- `_response_format_to_text_format()` reshapes the Chat Completions `response_format` (`json_schema` under `response_format.json_schema`) into the Responses API's `text.format`.

Both are pure, small, and localized enough to live as code comments rather than here — see `llm7shi/openai.py` for the current shape.

## Scope and Caveats

**Multi-turn reasoning continuity is not implemented.** The Responses API supports carrying a reasoning model's prior-turn reasoning into the next turn (`reasoning.context: "all_turns"`, with `encrypted_content` on stored `reasoning` output items, since this library always calls with `store=False`). `Client`'s conversation history is flattened back into plain `role`/`content` messages on every turn, discarding any `reasoning` output items instead of carrying them forward. This was an explicit scope cut in the design discussion, not an oversight: implementing it would require `Client`/`Response` to carry raw output items across turns, which is a larger architectural change than this pass covered.

**Reasoning summaries are not always populated even for the right model.** OpenAI's own docs note that reasoning summaries may require [organization verification](https://help.openai.com/en/articles/10910291-api-organization-verification), and reasoning models reason *adaptively* — trivial prompts can produce `reasoning_tokens: 0` in `usage.output_tokens_details`, with no summary to show, even at `effort: "medium"`. An empty `Response.thoughts` for a reasoning model is expected in both cases, not a bug.

See [openai.md](../llm7shi/openai.md) for the module-level rationale, [compat.md](../llm7shi/compat.md) for how `include_thoughts`/`reasoning_effort` reach the `openai:` vendor prefix, and the `[Unreleased]` section of [CHANGELOG.md](../CHANGELOG.md) for the user-facing summary.
