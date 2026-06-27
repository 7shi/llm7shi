# Client Usage Example

## Why This Implementation Exists

To demonstrate how the stateful `Client` simplifies conversational logic compared to stateless messaging wrappers.

### Duplicated State Management in Stateless Calls
**Problem**: Traditional stateless multi-turn examples require manual creation, updating, and passing of message lists, which becomes error-prone and hard to maintain as conversations grow.

**Solution**: Provided a clean example showing how the `Client` dynamically manages and appends conversation history internally, allowing users to execute turns using simple function calls.

### Separated System Role Configuration
**Problem**: The LLM engine settings (model configuration) are often defined globally, while system instructions (such as agent roles or tasks) are defined by the execution flow. Setting the system prompt in the constructor couples these roles unnecessarily.

**Solution**: Demonstrated configuration of the system prompt via the dedicated `client.set_system_prompt()` method, showing how system instructions are integrated directly into the managed history.

### Display Noise with Auto-Echo Output
**Problem**: The client's underlying stream engine automatically echoes LLM generation to the console, so adding explicit `print` statements in the caller code results in duplicated text and cluttered console logs.

**Solution**: Adjusted the example to call the client directly without manual output prints, ensuring a clean, single-pass generation display.
