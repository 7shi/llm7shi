# OpenRouter Reasoning Control

This document explains how llm7shi maps the `include_thoughts` parameter onto OpenRouter's reasoning controls, and why the implementation arrived at sending `reasoning.enabled` explicitly for both states.

## Background

OpenRouter is reached through the OpenAI-compatible layer (`_generate_with_openai`), so reasoning-capable models routed via OpenRouter expose their thinking process through `delta.reasoning` on the streaming response rather than through a provider-specific field. llm7shi extracts this into `Response.thoughts` and displays it under the same Thinking/Answer indicators used for Gemini and Ollama, giving a consistent experience regardless of provider.

The harder question was the inverse: how to honor `include_thoughts=False`, i.e. how to actually turn reasoning *off* for a model that would otherwise reason. OpenRouter exposes this through a `reasoning` object passed in `extra_body`, but the correct key was not obvious, and several approaches were tried before settling on the current one.

## The Evolution of the Disable Mechanism

### Attempt 1: `reasoning.exclude = True`

The first implementation suppressed reasoning with `{"reasoning": {"exclude": True}}`. This looked correct because the thinking process disappeared from the output, but it was misleading: `exclude` only hides the reasoning tokens from the response. The model still performs the full reasoning process server-side, so the user pays the latency and token cost without seeing any benefit. That is the opposite of what `include_thoughts=False` is meant to achieve — the goal is to *skip* reasoning, not merely to hide it.

### Attempt 2: `reasoning.max_tokens = 0`

To actually stop the model from reasoning, the next attempt used `{"reasoning": {"max_tokens": 0}}`, reasoning that a zero budget would leave no room for the thinking process. This was also incorrect; `max_tokens` is a budget hint, not a switch, and zero is not the intended way to disable reasoning entirely.

### Attempt 3: `reasoning.enabled = False`

The correct switch is `{"reasoning": {"enabled": False}}`. This tells OpenRouter to skip the reasoning process altogether rather than hide its output, which is exactly the semantics `include_thoughts=False` promises.

## Sending `enabled` Explicitly for Both States

A subtler problem remained even after the disable path was correct. Some models do not reason *by default*. For example, `google/gemma-4-31b-it:free` stays silent unless reasoning is explicitly requested. With the earlier logic — which only sent `extra_body` when `include_thoughts` was `False` — these models would never emit a thinking process, so `include_thoughts=True` had no effect on them.

The fix was to send `reasoning.enabled` explicitly in both directions:

```python
extra_body = None
if vendor_prefix == "openrouter":
    extra_body = {"reasoning": {"enabled": include_thoughts}}
```

By always passing the flag, `include_thoughts=True` reliably turns reasoning *on* (even for models that default to off), and `include_thoughts=False` reliably turns it off. This makes the parameter behave consistently across OpenRouter models regardless of each model's default reasoning behavior.

## Scope and Caveats

This control applies only to the `openrouter:` vendor prefix. Other OpenAI-compatible vendors (`groq`, `grok`, plain `openai`) do not receive the `reasoning` field, because it is an OpenRouter extension.

The behavior is not perfectly uniform across providers even for the *same* model. The Gemma model, for instance, can be reached through `google:`, `openrouter:`, and `ollama:`. OpenRouter and Ollama cleanly suppress reasoning when reasoning is disabled, but the direct `google:` path does not — with reasoning off, the Gemini API lets the model's deliberation leak into the answer body instead of separating it out. That is a server-side behavior outside llm7shi's control. See [examples/gemma4.md](../examples/gemma4.md) for a side-by-side demonstration, and [examples/openrouter.md](../examples/openrouter.md) for the OpenRouter-specific reasoning toggle example.
