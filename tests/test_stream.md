# Stream Generator Testing

## Why This Implementation Exists

Testing the unified retry loop and stream consumption logic presented unique challenges because real-world API rate limits and network errors are stochastic and depend on external services. This test suite validates that retry budgets, backoff countdowns, stream termination, and exception propagation function reliably.
