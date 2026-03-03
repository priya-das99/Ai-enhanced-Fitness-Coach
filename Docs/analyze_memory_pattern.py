"""
Memory Pattern Analysis for Conversation History
Shows the exact data structure and memory management strategy
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_assistant.unified_state import WorkflowState, _user_states, get_workflow_state

print("="*80)
print("MEMORY PATTERN ANALYSIS: CONVERSATION HISTORY")
print("="*80)

print("\n1. PATTERN NAME: SLIDING WINDOW BUFFER (Circular Buffer)")
print("-" * 80)
print("Also known as: Ring Buffer, Bounded Queue")
print("")
print("Description:")
print("  - Fixed-size buffer that keeps only the N most recent items")
print("  - When buffer is full, oldest items are discarded (FIFO)")
print("  - Prevents unbounded memory growth")
print("  - Maintains recent context without storing entire history")

print("\n2. DATA STRUCTURE")
print("-" * 80)
print("Type: Python List (Dynamic Array)")
print("Location: WorkflowState.conversation_history")
print("")
print("Structure:")
print("  conversation_history: List[Dict[str, str]] = [")
print("    {'role': 'user', 'content': 'message 1'},")
print("    {'role': 'assistant', 'content': 'response 1'},")
print("    {'role': 'user', 'content': 'message 2'},")
print("    ...")
print("  ]")

print("\n3. MEMORY LIMITS")
print("-" * 80)
print("Max messages per user: 20 messages (10 exchanges)")
print("Retention after workflow: 10 messages (5 exchanges)")
print("")
print("Why these limits?")
print("  - 20 messages = ~2-3 KB per user (assuming 100 chars/message)")
print("  - Enough context for multi-turn conversations")
print("  - Prevents memory bloat in long sessions")
print("  - LLM context window efficiency (fewer tokens)")

print("\n4. STORAGE SCOPE")
print("-" * 80)
print("Scope: Per-User, In-Memory")
print("Lifetime: Application runtime (not persisted)")
print("")
print("Storage location:")
print("  _user_states: Dict[int, WorkflowState] = {}")
print("    ↓")
print("  _user_states[user_id] = WorkflowState(user_id)")
print("    ↓")
print("  WorkflowState.conversation_history = [...]")

print("\n5. MEMORY MANAGEMENT STRATEGY")
print("-" * 80)

# Demonstrate the sliding window
state = WorkflowState(99999)

print("Initial state:")
print(f"  Length: {len(state.conversation_history)}")
print(f"  Memory: ~{len(str(state.conversation_history))} bytes")

# Add messages to demonstrate sliding window
print("\nAdding 25 messages (exceeds limit of 20)...")
for i in range(25):
    role = 'user' if i % 2 == 0 else 'assistant'
    state.add_message(role, f'Message {i+1}')

print(f"\nAfter adding 25 messages:")
print(f"  Length: {len(state.conversation_history)} (should be 20)")
print(f"  First message: {state.conversation_history[0]}")
print(f"  Last message: {state.conversation_history[-1]}")
print("")
print("Notice: Only last 20 messages kept (messages 6-25)")
print("        Messages 1-5 were automatically discarded")

print("\n6. IMPLEMENTATION CODE")
print("-" * 80)
print("From unified_state.py:")
print("")
print("def add_message(self, role: str, content: str):")
print("    self.conversation_history.append({")
print("        'role': role,")
print("        'content': content")
print("    })")
print("    # Sliding window: Keep only last 20 messages")
print("    if len(self.conversation_history) > 20:")
print("        self.conversation_history = self.conversation_history[-20:]")
print("")
print("def complete_workflow(self):")
print("    # Further trim to 10 messages when workflow completes")
print("    self.conversation_history = self.conversation_history[-10:]")

print("\n7. MEMORY CHARACTERISTICS")
print("-" * 80)

# Calculate memory usage
import sys as pysys

single_message = {'role': 'user', 'content': 'A' * 100}  # 100 char message
message_size = pysys.getsizeof(single_message)
history_20_size = message_size * 20
history_overhead = pysys.getsizeof([single_message] * 20)

print(f"Single message size: ~{message_size} bytes")
print(f"20 messages (data): ~{history_20_size} bytes")
print(f"List overhead: ~{history_overhead - history_20_size} bytes")
print(f"Total per user: ~{history_overhead} bytes (~{history_overhead/1024:.2f} KB)")
print("")
print("For 1000 concurrent users:")
print(f"  Total memory: ~{history_overhead * 1000 / 1024:.2f} KB")
print(f"              = ~{history_overhead * 1000 / (1024*1024):.2f} MB")

print("\n8. COMPARISON WITH OTHER PATTERNS")
print("-" * 80)

patterns = [
    ("Unbounded List", "Unlimited", "Grows forever", "Memory leak risk", "❌"),
    ("Sliding Window (Current)", "20 messages", "O(1) per add", "Bounded memory", "✅"),
    ("Database Storage", "Unlimited", "O(1) per add", "Persistent, slower", "⚖️"),
    ("LRU Cache", "N items", "O(1) per access", "Complex, overkill", "⚖️"),
    ("Session Storage", "Per session", "Cleared on logout", "Lost on disconnect", "⚖️"),
]

print(f"{'Pattern':<25} {'Capacity':<15} {'Performance':<15} {'Trade-off':<20} {'Fit'}")
print("-" * 80)
for pattern, capacity, perf, tradeoff, fit in patterns:
    print(f"{pattern:<25} {capacity:<15} {perf:<15} {tradeoff:<20} {fit}")

print("\n9. ADVANTAGES OF SLIDING WINDOW")
print("-" * 80)
print("✓ Bounded memory: Never exceeds 20 messages per user")
print("✓ O(1) append: Fast message addition")
print("✓ O(1) trim: Fast when limit exceeded (slice operation)")
print("✓ Simple: Easy to understand and maintain")
print("✓ No external dependencies: Pure Python, no database")
print("✓ Fast retrieval: In-memory access")
print("✓ Automatic cleanup: Old messages auto-discarded")

print("\n10. DISADVANTAGES & TRADE-OFFS")
print("-" * 80)
print("✗ Not persistent: Lost on server restart")
print("✗ Limited history: Only last 20 messages")
print("✗ Per-instance: Not shared across server instances")
print("✗ No long-term memory: Can't reference old conversations")
print("")
print("When to upgrade:")
print("  - Need conversation history across sessions → Add database storage")
print("  - Need longer context → Increase limit (but watch memory)")
print("  - Multiple servers → Use Redis/shared cache")
print("  - Analytics needed → Log to database separately")

print("\n11. REAL-WORLD MEMORY USAGE")
print("-" * 80)

# Simulate realistic usage
from chat_assistant.unified_state import _user_states

# Clear any existing states
_user_states.clear()

# Simulate 5 users with conversations
for user_id in range(1, 6):
    state = get_workflow_state(user_id)
    for i in range(10):  # 10 messages each
        role = 'user' if i % 2 == 0 else 'assistant'
        state.add_message(role, f'User {user_id} message {i+1}')

print(f"Active users: {len(_user_states)}")
print(f"Total messages stored: {sum(len(s.conversation_history) for s in _user_states.values())}")

total_size = 0
for user_id, state in _user_states.items():
    state_size = pysys.getsizeof(state.conversation_history)
    total_size += state_size
    print(f"  User {user_id}: {len(state.conversation_history)} messages, ~{state_size} bytes")

print(f"\nTotal memory: ~{total_size} bytes (~{total_size/1024:.2f} KB)")

print("\n" + "="*80)
print("SUMMARY: SLIDING WINDOW BUFFER PATTERN")
print("="*80)
print("")
print("Pattern: Bounded FIFO queue with automatic eviction")
print("Storage: In-memory Python list per user")
print("Capacity: 20 messages max, trimmed to 10 on workflow completion")
print("Memory: ~2-3 KB per user, ~2-3 MB for 1000 users")
print("Performance: O(1) append, O(1) trim, O(1) retrieval")
print("Lifetime: Application runtime (not persisted)")
print("")
print("Perfect for: Short-term conversational context in stateless APIs")
print("Not for: Long-term memory, cross-session history, multi-server setups")
print("")
print("="*80)
