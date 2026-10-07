# Making `include_thoughts=False` Stop the Thinking

`include_thoughts=False` is meant to stop a model's reasoning entirely, not just hide it ([20260608-provider-apis.md](20260608-provider-apis.md)). Measuring reasoning tokens showed that on the two first-party APIs, OpenAI and Gemini, it only hid the reasoning: the model kept thinking at its default effort. This document records the measurements and the fixes.

## How It Was Found

A downstream judge that should answer with a single word and no reasoning was being designed on top of `generate_with_schema(include_thoughts=False)`. Reading `openai.py` to confirm that this disables reasoning showed that it does not send a `reasoning` param at all, leaving the effort to the model's default. The Gemini path turned out to do the same: with no `thinking_budget`, `include_thoughts=False` sends no `thinking_config`.

Earlier documents had not caught this because they judged by output, not by tokens:

- [20260903-responses-api.md](20260903-responses-api.md) designed `include_thoughts=False` as "skip requesting a summary" and did not check `reasoning_tokens`.
- [20260608-provider-apis.md](20260608-provider-apis.md) concluded that `gemini-2.5-flash` "honors `--no-think` cleanly" because no thought parts came back. But Gemini's `ThinkingConfig.include_thoughts` only decides whether thought summaries are returned; whether the model thinks is decided by `thinking_budget` (or `thinking_level`).
- [20260915-token-usage.md](20260915-token-usage.md) had in fact already recorded `gemini-3.8-flash` spending 56 thinking tokens with no config, and no thought text, but read it as a usage-reporting detail rather than a sign that thinking was never off.

What made the problem measurable was that same token-usage work. `Response.usage` exposes reasoning tokens per call across providers (`Usage.reasoning_tokens`, with the provider's own fields kept in `Usage.raw`), and since 0.22.1 Gemini's thinking tokens are counted in `output_tokens` like the other providers'. Before that, the only evidence available was whether thinking text appeared, which is exactly what misled the earlier checks.

## Measurements

The scripts are in [20261007-disable-thinking/](20261007-disable-thinking/). Each asks "What is 17 * 23? Answer with the number only." and reads the reasoning-token count from the usage (`output_tokens_details.reasoning_tokens` for OpenAI, `thoughts_token_count` for Gemini). The llm7shi rows below were taken with the code before the fixes.

### OpenAI (`gpt-6-luna`, 3 calls each)

| Call | Reasoning tokens |
|---|---|
| llm7shi `include_thoughts=True` (`effort: medium`, summary) | 13, 14, 14 |
| llm7shi `include_thoughts=False` (no `reasoning` param) | 19, 17, 17 |
| raw: no `reasoning` param | 12, 17, 15 |
| raw: `effort: none` | 0, 0, 0 |
| raw: `effort: minimal` | 400: not supported (`none`/`low`/`medium`/`high`/`xhigh`/`max` only) |
| raw: `effort: low` | 0, 0, 0 (the prompt is trivial; not an off switch) |

`include_thoughts=False` thought as much as `True`. `effort: none` stops reasoning every time.

### Gemini (`gemini-2.5-flash`, 1 call each)

| Call | Thoughts tokens |
|---|---|
| llm7shi `include_thoughts=True` | 164 |
| llm7shi `include_thoughts=False` (no `thinking_config`) | 290 |
| raw: no config | 295 |
| raw: `ThinkingConfig(include_thoughts=False)` | 70 |
| raw: `thinking_budget=0` | none |
| raw: `thinking_level` (any) | 400: not supported for this model |

`include_thoughts=False`, whether llm7shi's (no config) or the raw `ThinkingConfig` used in [20260608-provider-apis.md](20260608-provider-apis.md), leaves the model thinking. `thinking_budget=0` stops it.

### Gemini (`gemini-3.8-flash`)

Two runs of the same variants:

| Call | Run 1 | Run 2 |
|---|---|---|
| llm7shi `include_thoughts=True` | 154 | 157 |
| llm7shi `include_thoughts=False` | 178 | 161 |
| raw: no config | 76 | 117 |
| raw: `ThinkingConfig(include_thoughts=False)` | 146 | 74 |
| raw: `thinking_budget=0` | 74 | none |
| raw: `thinking_level=MINIMAL` | — | 400: not supported for this model |
| raw: `thinking_level=LOW` | — | 73 |

Since `thinking_budget=0` gave different results, it was repeated 5 times against no config:

| Call | Thoughts tokens (5 calls) |
|---|---|
| no config | 150, 170, 155, 164, 74 |
| `thinking_budget=0` | none, 48, 48, none, 74 |

On Gemini 3, `thinking_budget=0` stopped thinking in 2 of 5 calls and cut it to roughly a quarter on average, but does not reliably turn it off. `MINIMAL`, the lowest documented level, is rejected by this model, so there is no reliable off switch for it.

## Fixes

### OpenAI (`openai.py`, Responses API path)

For reasoning models, `include_thoughts=False` now sends `reasoning={"effort": "none"}` without a summary instead of omitting `reasoning`. An explicit `reasoning_effort` replaces the `"none"` default, for models that do not accept `"none"` (e.g. `"minimal"` for gpt-5); such models now fail with `include_thoughts=False` alone, where they previously ran (and thought). Legacy gpt-3/gpt-4 models still get no `reasoning` param.

### Gemini (`gemini.py`)

`include_thoughts=False` now also sends `thinking_budget=0` unless a budget was given. `NO_ZERO_BUDGET_MODEL_RE` (`^gemma|-pro\b`) skips this for models that reject a zero budget: Gemma on the Gemini API (`400 INVALID_ARGUMENT: Thinking budget is not supported for this model`, see [20260608-provider-apis.md](20260608-provider-apis.md)) and Pro models, whose thinking cannot be turned off. Those keep thinking at their default, as before. The Pro exclusion follows Google's documentation and was not measured here.

After the fix, the same script ([check_gemini_thinking.py](20261007-disable-thinking/check_gemini_thinking.py)) gave:

| Call | `gemini-2.5-flash` | `gemini-3.8-flash` |
|---|---|---|
| llm7shi `include_thoughts=True` | 123 | 157 |
| llm7shi `include_thoughts=False` (now `thinking_budget=0`) | none | none |
| raw: `thinking_budget=0` | none | 73 |

On `gemini-3.8-flash` both calls sent the same zero budget, yet one thought and one did not, matching the 5-call repetition above.

On Gemini 3 the fix reduces thinking rather than stopping it, as measured above. `include_thoughts=False` therefore means "ask the provider to skip thinking as far as it allows," not a guarantee of zero reasoning tokens; checking `Usage.reasoning_tokens` is the only way to confirm.

## Other Providers

### OpenRouter (`inclusionai/ling-3.0-flash-sante:free`, 3 calls each)

OpenRouter already sent an explicit off switch (`reasoning.enabled=False`, [20260607-openrouter-reasoning.md](20260607-openrouter-reasoning.md)), but as a remote service it could hide reasoning the way OpenAI and Gemini did, so it was measured with [check_openrouter_thinking.py](20261007-disable-thinking/check_openrouter_thinking.py). Each cell is `completion_tokens_details.reasoning_tokens` / length of the returned reasoning text:

| Call | Results |
|---|---|
| llm7shi `include_thoughts=True` (`enabled: true`) | 11/43, 11/43, 28/109 |
| llm7shi `include_thoughts=False` (`enabled: false`) | 0/0, 0/0, 0/0 |
| raw: no `reasoning` | 11/43, 11/43, 24/92 |
| raw: `enabled: false` | 0/0, 0/0, 0/0 |
| raw: `enabled: true` | 11/43, 11/43, 11/43 |
| raw: `exclude: true` | 6/0, 17/0, 4/0 |
| raw: `effort: none` | 0/0, 0/0, 0/0 |
| raw: `max_tokens: 0` | 19/73, 11/43, 11/43 |

`include_thoughts=False` stops reasoning on OpenRouter; no fix was needed. The counts also confirm the earlier findings by numbers: `exclude: true` reasons without returning the text (it only hides), and `max_tokens: 0` does not turn reasoning off.

### Local Servers

Ollama (`think=False`) and the Chat Completions path for llama.cpp/vLLM (`chat_template_kwargs.enable_thinking=False`, [20260918-llama-cpp.md](20260918-llama-cpp.md)) also send an explicit off switch and were not re-measured here. On a local server the reasoning is ordinary generated text that the server only splits off, so it cannot be hidden server-side: an empty thinking text means no reasoning. Ollama reports no separate reasoning-token count ([20260915-token-usage.md](20260915-token-usage.md)), but its `eval_count` includes the reasoning, so comparing it between `think=True` and `False` would show the difference.
