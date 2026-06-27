# LLM Client Tests

## Why This Implementation Exists

To verify that the stateful, callable chat execution client handles history tracking, configuration settings, parameter propagation, system prompt mutation, and XML persistence reliably and symmetrically.

### Intertwined History and Retry State
**Problem**: The client mutates history state based on retry results, creating complex execution sequences (such as partial failures before a successful output) and parameter variations.

**Solution**: Mocked LLM responses to simulate multi-turn chats and simulated quality errors to confirm that history is only appended with the final successful response. Added verification that Client instance properties (such as model, temperature, and thinking settings) are correctly propagated down to the underlying `generate_with_schema` call.

### System Prompt Modification
**Problem**: The system prompt needs to be set or replaced dynamically at the head of the conversation history, which could corrupt message order if not handled symmetrically.

**Solution**: Added tests verifying `set_system_prompt` correctly inserts a system role message at index 0 of an empty history, replaces it in-place when a system prompt already exists, and preserves subsequent user/assistant turns in the list.
