# Token Usage Fields Across Providers

Investigation into where each provider puts token-usage information in its streaming response. This survey informed the design of `Response.usage` (the `Usage` class in `llm7shi/usage.py`; see `llm7shi/usage.md` for the design rationale) - the raw findings below are kept as the reference for why that design looks the way it does.

Script: [investigate_usage.py](20260915-token-usage/investigate_usage.py). It sends `"hi"` through the raw provider client (not the llm7shi wrapper) for a given `-m vendor:model`, collects every streamed chunk, and dumps `dir()` and `repr()` of the last two. `--completion` forces real OpenAI onto Chat Completions instead of the Responses API, mirroring the `USE_COMPLETION` escape hatch in `llm7shi/openai.py`.

## Ollama

```
$ uv run docs/20260915-token-usage/investigate_usage.py -m ollama:qwen3.5:4b
```

Usage sits directly on the final chunk (`done=True`), alongside timing fields — no separate nested object:

```
done=True done_reason='stop' total_duration=19974540800 load_duration=5480967800
prompt_eval_count=11 prompt_eval_duration=67347000 eval_count=701 eval_duration=14422607000
```

- Input: `prompt_eval_count`
- Output: `eval_count`
- Also present: `*_duration` fields (nanoseconds) and `load_duration`
- No separate usage sub-object: `llm7shi/ollama.py`'s `extract_usage()` dumps the whole chunk (`model_dump()`) and excludes the known non-usage keys (`model`, `created_at`, `done`, `done_reason`, `message`, `logprobs`), so a usage field Ollama adds later still ends up in `raw` without a code change

Intermediate chunks (`done=False`) carry these fields too, but they are always `None`.

Unlike Gemini, there is no separate reasoning-token count even with thinking enabled (`think=True`): a check against `qwen3.5:4b` showed `eval_count` bundling thinking and answer tokens into one number, with no field to split them back out. `Usage.reasoning_tokens` is therefore always `None` for Ollama - not a gap in the wrapper, a gap in what the API reports.

## Google (Gemini API)

```
$ uv run docs/20260915-token-usage/investigate_usage.py -m google:gemma-4-31b-it
```

Every chunk — not just the last — carries a `usage_metadata`, and it is already a running total rather than a per-chunk delta:

```
usage_metadata=GenerateContentResponseUsageMetadata(
  candidates_token_count=9,
  prompt_token_count=2,
  prompt_tokens_details=[ModalityTokenCount(modality=<MediaModality.TEXT: 'TEXT'>, token_count=2)],
  thoughts_token_count=50,
  total_token_count=61
)
```

- Input: `usage_metadata.prompt_token_count`
- Output: `usage_metadata.candidates_token_count`
- Also present: `thoughts_token_count` (reasoning), `total_token_count`, and a per-modality breakdown in `prompt_tokens_details`

## OpenAI — Responses API (the real-OpenAI default; see [20260903-responses-api.md](20260903-responses-api.md))

```
$ uv run docs/20260915-token-usage/investigate_usage.py -m openai:gpt-5.6-luna
```

Usage lives one level down, inside the final `ResponseCompletedEvent.response.usage`:

```
usage=ResponseUsage(
  input_tokens=7,
  input_tokens_details=InputTokensDetails(cache_write_tokens=0, cached_tokens=0),
  output_tokens=13,
  output_tokens_details=OutputTokensDetails(reasoning_tokens=0),
  total_tokens=20
)
```

- Input: `usage.input_tokens`
- Output: `usage.output_tokens`
- Also present: `input_tokens_details.cached_tokens`/`cache_write_tokens`, `output_tokens_details.reasoning_tokens`, `total_tokens`

## OpenAI — Chat Completions (`--completion`) and OpenAI-compatible vendors (OpenRouter, etc.)

```
$ uv run docs/20260915-token-usage/investigate_usage.py -m openai:gpt-5.6-luna --completion
$ uv run docs/20260915-token-usage/investigate_usage.py -m openrouter:liquid/lfm-2.5-2.6b:free
```

Both go through `chat.completions.create(..., stream_options={"include_usage": True})` — without that option, `usage` stays `None` on every chunk. Usage arrives as an *extra* chunk after the one with `finish_reason`, identifiable by `choices == []`:

```
ChatCompletionChunk(choices=[], usage=CompletionUsage(
  completion_tokens=53, prompt_tokens=11, total_tokens=64,
  completion_tokens_details=CompletionTokensDetails(reasoning_tokens=42, ...),
  prompt_tokens_details=PromptTokensDetails(cached_tokens=0, cache_write_tokens=0, ...)
))
```

- Input: `usage.prompt_tokens`
- Output: `usage.completion_tokens`
- Also present: `completion_tokens_details.reasoning_tokens`, `prompt_tokens_details.cached_tokens`/`cache_write_tokens`, `total_tokens`
- OpenRouter adds its own `usage.cost` / `usage.cost_details` (billed amount), absent from real OpenAI

This shape is identical for real OpenAI (Chat Completions) and OpenAI-compatible vendors, since both go through the same `openai` SDK response type.

## Summary

| Provider / API | Requires opt-in? | Where | Input field | Output field |
|---|---|---|---|---|
| Ollama | no | final chunk, top level | `prompt_eval_count` | `eval_count` |
| Gemini | no | every chunk, `usage_metadata` | `prompt_token_count` | `candidates_token_count` |
| OpenAI Responses | no | final event, `response.usage` | `input_tokens` | `output_tokens` |
| OpenAI/OpenRouter Chat Completions | yes — `stream_options={"include_usage": True}` | extra chunk with `choices=[]`, `usage` | `prompt_tokens` | `completion_tokens` |

Three different field-naming schemes (`prompt_eval_count`/`eval_count`, `prompt_token_count`/`candidates_token_count`, `input_tokens`/`output_tokens`, `prompt_tokens`/`completion_tokens`) and three different delivery shapes (flat on the final chunk, repeated on every chunk, or as a distinguishable extra chunk). Each `StreamGenerator` subclass's `extract_usage()` (in `llm7shi/stream.py` and the per-provider modules) implements the adapter for its own delivery shape — Ollama and the Responses API both keep whatever came in the last chunk/event, Gemini reads `usage_metadata` off any chunk since it is already cumulative, and the Chat Completions shape scans for the chunk with `choices == []`.

## What llm7shi Implements

`Response.usage` wraps whatever `extract_usage()` returns in a `Usage` object (`llm7shi/usage.py`): `raw` keeps the provider's dict as shown above, untouched, while `input_tokens`/`output_tokens`/`reasoning_tokens`/`cached_tokens`/`total_tokens` are best-effort normalizations that return `None` for a dimension a provider doesn't report, rather than forcing every provider into one shape. See `llm7shi/usage.md` for the full rationale. `examples/usage.py` demonstrates it:

```
$ uv run examples/usage.py -m openrouter:liquid/lfm-2.5-2.6b:free
...
usage: Usage({'input_tokens': 17, 'output_tokens': 147, 'reasoning_tokens': 137, 'cached_tokens': 0, 'total_tokens': 164})
usage.raw: {'completion_tokens': 147, 'prompt_tokens': 17, ...}
usage.total_tokens: 164
```

Related: [20260608-provider-apis.md](20260608-provider-apis.md) (same side-by-side approach for thinking/answer fields), [20260903-responses-api.md](20260903-responses-api.md) (why real OpenAI defaults to the Responses API), [20260607-openrouter-reasoning.md](20260607-openrouter-reasoning.md) (OpenRouter-specific extensions in the same Chat Completions layer).
