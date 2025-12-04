# Ollama Streaming Cleanup and Connection Management

Investigation and resolution of persistent server-side sessions when interrupting Ollama streaming responses.

## Problem

When using the `ollama-python` library to receive streaming responses from Ollama, interrupting the client-side loop processing (e.g., upon detecting character repetition) leaves computing sessions active on the Ollama server side. This causes unintended resource consumption.

## Root Cause Analysis

### 1. HTTP Client Connection Management

The `ollama-python` library uses `httpx` internally for HTTP communication. For efficiency, `httpx` maintains a connection pool and reuses established TCP connections. Simply breaking out of the streaming loop with `break` does not immediately close the connection, leaving the server thinking the client is still connected.

### 2. Ollama API Limitations

As of December 2023, Ollama's official REST API does not provide endpoints to explicitly cancel or abort generation tasks (`/api/generate` or `/api/chat`) on the server side. While related feature requests exist in GitHub issues, they remain unimplemented.

Therefore, the only practical approach is to physically close the connection from the client side.

## Solution

The solution is to explicitly close the `httpx` client object maintained internally by `ollama-python` immediately after interrupting streaming. This forces TCP connection termination, signaling session end to the server.

Using `try...finally` ensures cleanup happens whether the loop completes normally or is interrupted early.

### Synchronous Client Implementation

```python
import ollama

client = ollama.Client()
try:
    stream = client.chat(
        model='llama3',
        messages=[{'role': 'user', 'content': 'Tell me a long story.'}],
        stream=True,
    )

    for chunk in stream:
        # Process response and check for abort conditions
        # (e.g., detecting repetitive content)
        if should_abort_condition:
            print("\n[INFO] Aborting stream.")
            break

finally:
    # Directly close the internal httpx client
    client._client.close()
    print("\n[INFO] Client connection closed.")
```

### Asynchronous Client Implementation

```python
import asyncio
import ollama

async def main():
    client = ollama.AsyncClient()
    try:
        stream = await client.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': 'Tell me a long story.'}],
            stream=True,
        )

        async for chunk in stream:
            # Process response and check for abort conditions
            if should_abort_condition:
                print("\n[INFO] Aborting stream.")
                break

    finally:
        # Directly close the internal httpx client
        await client._client.aclose()
        print("\n[INFO] Async client connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
```

## Convenience Functions Warning

The library allows calling `ollama.chat()` and similar functions directly without creating a client instance. In this case, a temporary client is created internally for each call.

**This convenient approach has critical limitations when interrupting streams:**

- **Problem persists:** Using `ollama.chat(..., stream=True)` and breaking out of the loop leaves server-side sessions active
- **No solution available:** There is no way to obtain a reference to the internally created temporary client, making it impossible to call `client._client.close()` for forced cleanup

**Conclusion: When implementing streaming with potential interruption, always use `ollama.Client` or `ollama.AsyncClient` explicitly and guarantee connection cleanup with `try...finally`.**

## Implementation in llm7shi

The changes in `llm7shi/ollama.py` implement this solution:

1. Changed from `from ollama import chat, show` to `import ollama` and create explicit `client = ollama.Client()` instance
2. Updated all API calls to use the client instance (`client.chat()`, `client.show()`)
3. Added `client._client.close()` when breaking due to repetition detection or max length limits (llm7shi/ollama.py:85)

This ensures that when the streaming monitor detects issues and interrupts generation, the server-side session is properly terminated.

## Caveats

- **Internal API Access:** This solution accesses the undocumented internal `_client` property. Future `ollama-python` versions may change this implementation, breaking the code.
- **Client Reuse:** Once `close()` or `aclose()` is called, the client object cannot be reused. For subsequent Ollama requests in the same script, create new client instances or consider alternative connection management strategies.
