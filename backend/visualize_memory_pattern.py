"""
Visual Demonstration of Sliding Window Memory Pattern
Shows exactly how messages are stored and evicted
"""

print("""
================================================================================
                    SLIDING WINDOW BUFFER - VISUAL DEMO
================================================================================

PATTERN: Sliding Window (Circular Buffer / Bounded Queue)

CONCEPT: Keep only the N most recent items, automatically discard oldest

================================================================================
                              HOW IT WORKS
================================================================================

Step 1: Empty Buffer (Capacity: 5 for demo, actual: 20)
┌─────────────────────────────────────────────────────────┐
│ [  empty  ] [  empty  ] [  empty  ] [  empty  ] [  empty  ] │
└─────────────────────────────────────────────────────────┘
  Position 0    Position 1  Position 2  Position 3  Position 4

Step 2: Add 3 messages
┌─────────────────────────────────────────────────────────┐
│ [ msg 1 ] [ msg 2 ] [ msg 3 ] [  empty  ] [  empty  ] │
└─────────────────────────────────────────────────────────┘
  Length: 3 / 5

Step 3: Add 2 more messages (buffer full)
┌─────────────────────────────────────────────────────────┐
│ [ msg 1 ] [ msg 2 ] [ msg 3 ] [ msg 4 ] [ msg 5 ] │
└─────────────────────────────────────────────────────────┘
  Length: 5 / 5 (FULL)

Step 4: Add 1 more message (exceeds capacity)
┌─────────────────────────────────────────────────────────┐
│ [ msg 2 ] [ msg 3 ] [ msg 4 ] [ msg 5 ] [ msg 6 ] │
└─────────────────────────────────────────────────────────┘
  Length: 5 / 5
  ⚠️  msg 1 was AUTOMATICALLY DISCARDED (oldest)

Step 5: Add 2 more messages
┌─────────────────────────────────────────────────────────┐
│ [ msg 4 ] [ msg 5 ] [ msg 6 ] [ msg 7 ] [ msg 8 ] │
└─────────────────────────────────────────────────────────┘
  Length: 5 / 5
  ⚠️  msg 2 and msg 3 were DISCARDED

================================================================================
                        IMPLEMENTATION IN CODE
================================================================================

Python List Implementation:
""")

print("conversation_history = []  # Start empty")
print("")

# Simulate the pattern
conversation_history = []
MAX_SIZE = 5  # Demo size (actual is 20)

def add_message(role, content):
    global conversation_history
    conversation_history.append({'role': role, 'content': content})
    if len(conversation_history) > MAX_SIZE:
        conversation_history = conversation_history[-MAX_SIZE:]  # Keep last N
    return len(conversation_history)

# Add messages
for i in range(1, 9):
    role = 'user' if i % 2 == 1 else 'assistant'
    size = add_message(role, f'Message {i}')
    print(f"add_message('{role}', 'Message {i}')  → Length: {size}")
    
    if i == 5:
        print("  ⚠️  Buffer FULL (5/5)")
    elif i > 5:
        discarded = i - MAX_SIZE
        print(f"  ⚠️  Message {discarded} DISCARDED (oldest)")

print("")
print("Final state:")
for i, msg in enumerate(conversation_history):
    print(f"  [{i}] {msg}")

print("""

================================================================================
                        KEY IMPLEMENTATION DETAIL
================================================================================

The "magic" line that implements sliding window:

    if len(self.conversation_history) > 20:
        self.conversation_history = self.conversation_history[-20:]
                                                                 ^^^^^^
                                                                 Python slice
                                                                 "last 20 items"

What this does:
  1. Check if list exceeds 20 items
  2. If yes, create NEW list with only last 20 items
  3. Discard old list (garbage collected)
  4. Assign new list to conversation_history

Time Complexity: O(n) where n = 20 (constant, so effectively O(1))
Space Complexity: O(1) - creates temporary list of size 20

================================================================================
                        MEMORY LAYOUT IN RAM
================================================================================

Per-User Memory Structure:
""")

print("""
_user_states = {
    1001: WorkflowState {
        user_id: 1001,
        active_workflow: 'activity_logging',
        conversation_history: [
            {'role': 'user', 'content': 'log_water'},        ← ~184 bytes
            {'role': 'assistant', 'content': 'How many?'},   ← ~184 bytes
            {'role': 'user', 'content': "don't log"},        ← ~184 bytes
            ...  (up to 20 messages)
        ]  ← List overhead: ~216 bytes
    },  ← WorkflowState overhead: ~500 bytes
    
    1002: WorkflowState { ... },
    1003: WorkflowState { ... },
    ...
}  ← Dict overhead: ~240 bytes

Total per user: ~4-5 KB (with 20 messages)
Total for 1000 users: ~4-5 MB
""")

print("""
================================================================================
                        WHY THIS PATTERN?
================================================================================

Alternatives Considered:

1. ❌ Unbounded List
   conversation_history.append(msg)  # No limit
   Problem: Memory grows forever → Memory leak

2. ❌ Database for Every Message
   db.insert('chat_history', msg)
   Problem: Too slow, database overhead for temporary context

3. ⚖️  LRU Cache (Least Recently Used)
   from functools import lru_cache
   Problem: Overkill, we don't need access-based eviction

4. ✅ Sliding Window (CHOSEN)
   Keep last N items, discard oldest
   Benefits:
     - Bounded memory (never exceeds N)
     - Fast (O(1) operations)
     - Simple (easy to understand)
     - No external dependencies
     - Perfect for short-term context

================================================================================
                        WHEN TO USE EACH PATTERN
================================================================================

Sliding Window (Current):
  ✓ Short-term conversational context
  ✓ Single-server applications
  ✓ Stateless APIs with session state
  ✓ Memory-constrained environments

Database Storage:
  ✓ Long-term conversation history
  ✓ Cross-session persistence
  ✓ Analytics and reporting
  ✓ Multi-server deployments

Redis/Memcached:
  ✓ Shared state across servers
  ✓ High-traffic applications
  ✓ Need TTL (time-to-live) expiration
  ✓ Distributed systems

Hybrid (Current + Database):
  ✓ Recent context in memory (fast)
  ✓ Full history in database (persistent)
  ✓ Best of both worlds
  ✓ Recommended for production

================================================================================
                        PRODUCTION RECOMMENDATIONS
================================================================================

Current Implementation (Sliding Window):
  ✓ Good for: MVP, single-server, < 10k users
  ✓ Memory usage: ~5 MB for 1000 concurrent users
  ✓ Performance: Excellent (in-memory)
  ⚠️  Limitation: Lost on restart, not shared across servers

Upgrade Path:
  1. Add database logging (async, non-blocking)
  2. Keep sliding window for fast access
  3. Load from database on user reconnect
  4. Use Redis for multi-server deployments

Example Hybrid:
  - In-memory: Last 20 messages (fast LLM context)
  - Database: Full history (analytics, persistence)
  - Redis: Shared state (multi-server)

================================================================================
""")
