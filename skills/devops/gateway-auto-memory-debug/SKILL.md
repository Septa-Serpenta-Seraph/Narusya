---
name: gateway-auto-memory-debug
description: Diagnose and fix gateway memory tool auto-firing on startup due to session expiry watcher death spirals
---

# Debug Gateway Auto-Memory Flush

## Problem
Gateway shows memory/skill tool calls immediately on startup without user input, or enters an infinite loop of memory tool calls.

## Symptoms
- Tool calls appear: `┊ 🧠 memory +memory: "..." 0.0s [full]`
- Multiple retries with `[error]` or `[full]` status
- Agent cycles: "Memory is at capacity" → "Let me condense" → fails → repeats
- Max iterations (8) reached repeatedly
- Memory stays at 100% capacity during loops

## Root Causes

### 1. Session Expiry Watcher (Normal Behavior)
Gateway runs `_session_expiry_watcher` every 5 minutes (300s) to flush expired sessions. When sessions exceed their reset policy, it spawns a temporary agent with enabled_toolsets containing "memory" and "skills" to save context before clearing.

### 2. Memory Capacity Death Spiral (CRITICAL)
When MEMORY.md or USER.md exceeds ~90% of character limits, the flush agent:
1. Tries to add memories
2. Fails with "full" error
3. Attempts to condense existing entries
4. Fails condensing (no good matches)
5. Tries new approaches
6. Hits max iterations
7. Restarts from summary state
8. Cycles indefinitely

## Default Reset Policy
- Mode: `both` (idle OR daily)
- Idle: 1440 minutes (24 hours)  
- Daily: 4 AM local time
- Memory char limit: 4400 (~1600 tokens)
- User char limit: 2750 (~1000 tokens)

## Emergency Fix

**Clear memory files immediately:**

```bash
# Create archive directory and backup
mkdir -p ~/.hermes/memories/archive
cp ~/.hermes/memories/MEMORY.md ~/.hermes/memories/archive/MEMORY-$(date +%Y%m%d-%H%M).md
cp ~/.hermes/memories/USER.md ~/.hermes/memories/archive/USER-$(date +%Y%m%d-%H%M).md

# Clear active files (stops the spiral)
echo "Memory archived $(date)" > ~/.hermes/memories/MEMORY.md
echo "User archived $(date)" > ~/.hermes/memories/USER.md
```

## Permanent Fix: Capacity Guard

Add `_check_memory_capacity()` helper and guards to prevent flush when memory is >90% full.

### Step 1: Add capacity checker

In `gateway/run.py`, add to `GatewayRunner` class:

```python
def _check_memory_capacity(self) -> tuple[bool, str]:
    """Check if memory is near or at capacity.
    
    Returns (should_flush, status) where should_flush is False
    if memory is too full to safely run a flush agent.
    """
    try:
        from tools.memory_tool import MEMORY_DIR
        from pathlib import Path
        
        # Default limits
        memory_char_limit = 4400
        user_char_limit = 2750
        
        # Try loading from config
        try:
            import yaml
            config_path = Path.home() / ".hermes" / "config.yaml"
            if config_path.exists():
                with open(config_path) as f:
                    cfg = yaml.safe_load(f) or {}
                mem_cfg = cfg.get("memory", {})
                memory_char_limit = mem_cfg.get("memory_char_limit", 4400)
                user_char_limit = mem_cfg.get("user_char_limit", 2750)
        except Exception:
            pass
        
        # Check file sizes
        memory_path = MEMORY_DIR / "MEMORY.md"
        user_path = MEMORY_DIR / "USER.md"
        memory_chars = len(memory_path.read_text()) if memory_path.exists() else 0
        user_chars = len(user_path.read_text()) if user_path.exists() else 0
        
        memory_pct = memory_chars / memory_char_limit if memory_char_limit > 0 else 0
        user_pct = user_chars / user_char_limit if user_char_limit > 0 else 0
        
        status = f"MEMORY: {memory_chars}/{memory_char_limit} ({memory_pct:.0%}), USER: {user_chars}/{user_char_limit} ({user_pct:.0%})"
        
        # If either >90%, skip flush to prevent death spiral
        if memory_pct >= 0.90 or user_pct >= 0.90:
            logger.warning("[MEMORY GUARD] Memory near capacity: %s", status)
            return False, status
        
        logger.debug("[MEMORY GUARD] Memory OK: %s", status)
        return True, status
        
    except Exception as e:
        logger.debug("[MEMORY GUARD] Check failed: %s", e)
        return True, "unknown (check failed)"
```

### Step 2: Guard the flush function

In `_flush_memories_for_session()`, add at the start:

```python
def _flush_memories_for_session(self, old_session_id: str, ...):
    try:
        # GUARD: Check capacity before spawning flush agent
        should_flush, status = self._check_memory_capacity()
        if not should_flush:
            logger.info("[FLUSH SKIP] Session %s - memory full (%s)", old_session_id, status)
            return
        
        # ... existing flush logic ...
```

### Step 3: Guard the watcher

In `_session_expiry_watcher()`, add capacity check at loop start:

```python
async def _session_expiry_watcher(self, interval: int = 300):
    await asyncio.sleep(60)  # initial delay
    skipped_due_to_capacity = 0
    
    while self._running:
        try:
            # GUARD: Check capacity before processing
            should_flush, capacity_status = self._check_memory_capacity()
            if not should_flush:
                skipped_due_to_capacity += 1
                # Log first and every ~hour (12 checks)
                if skipped_due_to_capacity == 1 or skipped_due_to_capacity % 12 == 0:
                    logger.warning(
                        "[WATCHER GUARD] Memory near capacity. Skipping flushes. "
                        "Clear memory files or increase limits to resume."
                    )
                # Sleep but don't flush
                for _ in range(interval):
                    if not self._running:
                        break
                    await asyncio.sleep(1)
                continue
            
            # Reset counter when capacity restores
            if skipped_due_to_capacity > 0:
                logger.info("[WATCHER GUARD] Capacity restored. Resuming flushes.")
                skipped_due_to_capacity = 0
            
            # ... existing watcher logic ...
```

## Diagnosis

Check current memory usage:
```bash
wc -c ~/.hermes/memories/*.md
```

Check Qdrant status:
```bash
curl -s http://localhost:6333/collections | head -1
```

Watch for guard logs:
```bash
hermes gateway 2>&1 | grep -E "MEMORY GUARD|FLUSH SKIP|WATCHER GUARD"
```

## Prevention

### Increase Limits
If you frequently hit capacity, modify the memory section in your main config:
```yaml
memory:
  memory_char_limit: 8800
  user_char_limit: 5500
```

### Backup to Qdrant
Archive memories before clearing. Creates 3072-dim embeddings via API and stores in `naru_memory_backups` collection for semantic search.

### Disable Auto-Flush
Set memory_enabled to false to prevent all memory operations.

## Code Locations
- Watcher: `gateway/run.py` around line 1033
- Flush logic: `gateway/run.py` around line 514  
- Memory tool: `tools/memory_tool.py` around line 100

## Debugging

The patched code adds these log prefixes:
- `[MEMORY GUARD]` - Capacity check results
- `[FLUSH SKIP]` - Individual flush skipped due to capacity
- `[FLUSH START]` - Flush beginning with capacity OK
- `[WATCHER GUARD]` - Watcher skipping all flushes
- `[WATCHER]` - Normal watcher operations

Look for these in gateway logs to verify the fix is working.
