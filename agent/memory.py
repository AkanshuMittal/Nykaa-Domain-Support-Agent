import json
import os

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "conversation_memory.json")


def _load_all() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def _save_all(data: dict) -> None:
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_history(thread_id: str) -> list[dict]:
    """Returns the message history for a thread_id, or [] if the thread is new."""
    all_data = _load_all()
    return all_data.get(thread_id, [])


def append_turn(thread_id: str, role: str, content: str) -> None:
    all_data = _load_all()
    thread_history = all_data.get(thread_id, [])
    thread_history.append({"role": role, "content": content})
    all_data[thread_id] = thread_history
    _save_all(all_data)


if __name__ == "__main__":
    # Clean slate for the demo
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)

    thread_a = "thread-demo-a"
    print(f"--- Multi-turn demo on {thread_a} ---")
    append_turn(thread_a, "user", "What's the status of order ORD-0001?")
    append_turn(thread_a, "assistant", "ORD-0001 is Returned.")
    append_turn(thread_a, "user", "And is that one delayed?")
    print("History after 3 turns:", get_history(thread_a))

    thread_b = "thread-demo-b-fresh"
    print(f"\n--- Fresh thread {thread_b} (should be empty) ---")
    print("History:", get_history(thread_b))