import os
import sys
import uuid

from langgraph.checkpoint.sqlite import SqliteSaver

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
from graph import build_graph  # noqa: E402

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "checkpoints.sqlite")


def main() -> None:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # clean slate for the demo

    thread_id = f"checkpoint-demo-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        # Interrupt right before output_guardrail, so only
        # input_guardrail -> router -> order_lookup_node run initially.
        app = build_graph(
            collection=None,  # order-lookup path never touches the RAG collection
            checkpointer=checkpointer,
            interrupt_before=["output_guardrail"],
        )

        initial_state = {
            "thread_id": thread_id,
            "trace_id": str(uuid.uuid4()),
            "raw_query": "What's the status of order ORD-0002?",
        }

        print("=" * 70)
        print("STEP (a)+(b): first run — should stop BEFORE output_guardrail")
        print("=" * 70)
        app.invoke(initial_state, config=config)

        state_after_interrupt = app.get_state(config)
        print(f"\nGraph paused. Next node(s) to run: {state_after_interrupt.next}")
        print("(only input_guardrail, router, order_lookup_node printed above — correct)")

        print("\n" + "=" * 70)
        print("STEP (c): resuming the SAME thread_id with input=None")
        print("=" * 70)
        # Passing None resumes from the last checkpoint instead of restarting.
        final_state = app.invoke(None, config=config)

        print("\nOnly output_guardrail and memory_write should have printed just now —")
        print("input_guardrail / router / order_lookup_node did NOT re-run, proving")
        print("their results were loaded from the SQLite checkpoint.")

        print("\nFinal response after resume:")
        print(final_state["final_response"])


if __name__ == "__main__":
    main()