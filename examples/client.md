# Client Usage Example

## Why This Implementation Exists

To demonstrate how the stateful `Client` simplifies conversational logic compared to stateless messaging wrappers.

### Duplicated State Management in Stateless Calls
**Problem**: Traditional stateless multi-turn examples require manual creation, updating, and passing of message lists, which becomes error-prone and hard to maintain as conversations grow.

**Solution**: Provided a clean example showing how the `Client` dynamically manages and appends conversation history internally, allowing users to execute turns using simple function calls.

