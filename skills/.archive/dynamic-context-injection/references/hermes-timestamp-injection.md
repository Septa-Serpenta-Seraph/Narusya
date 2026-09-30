# Hermes Timestamp Injection Status

**Last Updated**: 2026-06-24

## Current State

The timestamp injection feature in Hermes has a **config flag but no implementation** in the currently deployed version.

## Evidence

- Config key `gateway.message_timestamps.enabled` exists and can be set to `true`
- The actual injection code commits exist in the repository:
  - `36ae95847` - "feat(gateway): gate message timestamps behind opt-in (default off)"
  - `bd7fc8fdc` - "feat(gateway): inject stable human-readable message timestamps"
- These commits are on a different branch and haven't been merged to the currently deployed version

## Impact on Dynamic Context Injection

This feature is **highly relevant** to dynamic context injection for several reasons:

### 1. Timing of Context Injection
- Timestamp-aware context loading needs to know WHEN a message was sent
- Without injection timestamps, you can't reliably determine temporal relationships between messages
- Makes it harder to implement "activate context for messages within last X minutes/hours"

### 2. Debugging and Logging
- When debugging context activation, you want to see exactly when each message arrived
- Without timestamps in the conversation context, you have to manually query the system time
- Makes it harder to correlate activation decisions with message timing

### 3. Workarounds

#### Use Terminal `date` Command
```bash
date "+%Y-%m-%d %H:%M:%S %Z"
```
- Shows current time in one command
- Can be called before processing each message
- Adds a small delay but provides accurate timing

#### Use `datetime` in Python
```python
from datetime import datetime
datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
```
- Same as above but in Python context
- Useful for scripts and automation

#### Check Message Metadata
- If using QDRANT for context storage, you can store timestamps with each message
- Query message timestamps separately from conversation context
- More complex but provides full temporal history

## Recommended Approach for Now

### For Prototype/Development
1. Use terminal `date` command before processing messages
2. Store timestamps in QDRANT message metadata
3. Build activation logic with explicit timestamp checks

### For Production (When Feature Lands)
1. Enable `gateway.message_timestamps.enabled: true`
2. Test that timestamps inject correctly
3. Update activation logic to use injected timestamps
4. Remove manual timestamp queries (cleaner code)

## Future Monitoring

Watch for:
- Hermes releases that merge the timestamp injection commits
- `gateway.message_timestamps.enabled` config to actually do something
- Documentation updates mentioning timestamp injection
- Release notes for version including commits `36ae95847` and `bd7fc8fdc`

When the feature lands, update this document and adjust dynamic context injection implementation to use the native timestamps instead of manual queries.

## Related Systems

- **Dynamic Context Injection**: `memory-systems/dynamic-context-injection` - Uses temporal awareness for activation
- **QDRANT Message Storage**: `memory-systems/qdrant-memory-diagnostics` - Can store timestamps with messages
- **Hermes Agent Configuration**: `autonomous-ai-agents/hermes-agent` - Config management for gateway features
