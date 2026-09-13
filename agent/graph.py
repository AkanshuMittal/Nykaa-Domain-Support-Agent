import re
import sys
import os
import uuid
from typing import TypedDict

from langgraph.graph import StateGraph, END

sys.path.insert(0, os.path.dirname(__file__))
from tools import check_order_status  # noqa: E402
from guardrails import mask_pii, detect_prompt_injection, groundedness_check  # noqa: E402
from schema import validate_response  # noqa: E402
from memory import append_turn, get_history  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag"))
from retrieve import generate_answer, THRESHOLD  # noqa: E402
from indexer import build_indexes  # noqa: E402

_ORDER_ID_PATTERN = re.compile(r"ORD-\d{4}", re.IGNORECASE)


class AgentState(TypedDict, total=False):
    thread_id: str
    trace_id: str
    raw_query: str
    masked_query: str
    pii_found: list
    injection_blocked: bool
    intent: str
    answer: str
    source: str
    top1_similarity: float
    is_fallback: bool
    escalation_score: float | None
    retrieved_doc_ids: list
    final_response: dict


# --- Nodes -----------------------------------------------------------------


def input_guardrail_node(state: AgentState) -> AgentState:
    print(f"[NODE] input_guardrail executing (trace_id={state.get('trace_id')})")
    masked_text, pii_found = mask_pii(state["raw_query"])
    injection = detect_prompt_injection(state["raw_query"])
    state["masked_query"] = masked_text
    state["pii_found"] = pii_found
    state["injection_blocked"] = injection
    return state


def router_node(state: AgentState) -> AgentState:
    print(f"[NODE] router executing (trace_id={state.get('trace_id')})")
    query = state["raw_query"]
    if _ORDER_ID_PATTERN.search(query) or (
        "order" in query.lower() and any(w in query.lower() for w in ["status", "where", "track"])
    ):
        state["intent"] = "order_lookup"
    else:
        state["intent"] = "rag"
    return state


def route_after_router(state: AgentState) -> str:
    """The genuine conditional edge: picks the next node by intent."""
    if state.get("injection_blocked"):
        return "blocked"
    return state["intent"]  # "order_lookup" or "rag"


def rag_node(state: AgentState, collection) -> AgentState:
    result = generate_answer(state["masked_query"], collection)
    state["answer"] = result["answer"]
    state["source"] = "rag"
    state["top1_similarity"] = result["top1_similarity"]
    state["is_fallback"] = result["is_fallback"]
    state["escalation_score"] = None
    state["retrieved_doc_ids"] = list({c["doc_id"] for c in result["retrieved"]})
    return state


def order_lookup_node(state: AgentState) -> AgentState:
    print(f"[NODE] order_lookup_node executing (trace_id={state.get('trace_id')})")
    match = _ORDER_ID_PATTERN.search(state["raw_query"])
    record_id = match.group(0).upper() if match else "UNKNOWN"
    result = check_order_status(record_id)

    if result.get("found"):
        state["answer"] = (
            f"Order {record_id}: status={result['status']}, "
            f"value=₹{result['order_value_inr']}, "
            f"escalation_score={result['escalation_score']}"
        )
        state["escalation_score"] = result["escalation_score"]
        state["is_fallback"] = False
    else:
        state["answer"] = result["error"]
        state["escalation_score"] = None
        state["is_fallback"] = True

    state["source"] = "order_lookup"
    state["top1_similarity"] = 1.0  # not applicable to this path
    state["retrieved_doc_ids"] = []
    return state


def blocked_node(state: AgentState) -> AgentState:
    state["answer"] = "This request was blocked by our input guardrail (potential prompt injection)."
    state["source"] = "guardrail_blocked"
    state["is_fallback"] = True
    state["escalation_score"] = None
    state["retrieved_doc_ids"] = []
    state["top1_similarity"] = 0.0
    return state


def output_guardrail_node(state: AgentState) -> AgentState:
    print(f"[NODE] output_guardrail executing (trace_id={state.get('trace_id')})")
    if state["source"] == "rag" and not state["is_fallback"]:
        grounded = groundedness_check(state["top1_similarity"], THRESHOLD)
        if not grounded:
            state["answer"] = "I don't know — I couldn't find this in our policy documents."
            state["is_fallback"] = True
    return state


def memory_write_node(state: AgentState) -> AgentState:
    print(f"[NODE] memory_write executing (trace_id={state.get('trace_id')})")
    append_turn(state["thread_id"], "user", state["raw_query"])
    append_turn(state["thread_id"], "assistant", state["answer"])

    response = {
        "query": state["raw_query"],
        "source": state["source"],
        "answer": state["answer"],
        "is_fallback": state["is_fallback"],
        "escalation_score": state.get("escalation_score"),
        "retrieved_doc_ids": state.get("retrieved_doc_ids", []),
        "trace_id": state["trace_id"],
    }
    is_valid, error = validate_response(response)
    if not is_valid:
        raise ValueError(f"Agent response failed schema validation: {error}")

    state["final_response"] = response
    return state


def build_graph(collection, checkpointer=None, interrupt_before=None):
    graph = StateGraph(AgentState)

    graph.add_node("input_guardrail", input_guardrail_node)
    graph.add_node("router", router_node)
    graph.add_node("rag_node", lambda s: rag_node(s, collection))
    graph.add_node("order_lookup_node", order_lookup_node)
    graph.add_node("blocked_node", blocked_node)
    graph.add_node("output_guardrail", output_guardrail_node)
    graph.add_node("memory_write", memory_write_node)

    graph.set_entry_point("input_guardrail")
    graph.add_edge("input_guardrail", "router")
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {"rag": "rag_node", "order_lookup": "order_lookup_node", "blocked": "blocked_node"},
    )
    graph.add_edge("rag_node", "output_guardrail")
    graph.add_edge("order_lookup_node", "output_guardrail")
    graph.add_edge("blocked_node", "memory_write")
    graph.add_edge("output_guardrail", "memory_write")
    graph.add_edge("memory_write", END)

    compile_kwargs = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    if interrupt_before is not None:
        compile_kwargs["interrupt_before"] = interrupt_before

    return graph.compile(**compile_kwargs)


def run_query(app, thread_id: str, query: str) -> dict:
    initial_state: AgentState = {
        "thread_id": thread_id,
        "trace_id": str(uuid.uuid4()),
        "raw_query": query,
    }
    final_state = app.invoke(initial_state)
    return final_state["final_response"]


if __name__ == "__main__":
    from memory import MEMORY_FILE

    # Clean slate every run — otherwise re-running this demo keeps appending
    # to the same thread_id and the "multi-turn" printout balloons with every
    # past run's turns (this was a real bug: the file wasn't being reset here
    # even though memory.py's own demo does reset it).
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)

    fixed_col, _ = build_indexes()
    app = build_graph(fixed_col)

    print("=== Route 1: policy question -> rag_node ===")
    print(run_query(app, "demo-thread-1", "What's the return window for Footwear?"))

    print("\n=== Route 2: order question -> order_lookup_node ===")
    print(run_query(app, "demo-thread-1", "What's the status of order ORD-0001?"))

    print("\n=== Multi-turn memory check on same thread ===")
    print(get_history("demo-thread-1"))

    print("\n=== Fresh thread (should have no prior history) ===")
    print(get_history("demo-thread-fresh"))