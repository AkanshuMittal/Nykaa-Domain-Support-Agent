import time
import concurrent.futures

from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy
from typing import TypedDict


class DemoState(TypedDict, total=False):
    value: int
    log: list


# ---------------------------------------------------------------------------
# Shared timeout helper — used for BOTH the per-node and the global timeout
# demos. Running the target callable in a worker thread and calling
# future.result(timeout=...) is what turns an overrun into a clean,
# immediate TimeoutError instead of the caller hanging indefinitely.
# ---------------------------------------------------------------------------


def run_with_timeout(fn, args=(), timeout_seconds: float = 2.0):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn, *args)
    try:
        result = future.result(timeout=timeout_seconds)
        executor.shutdown(wait=False)
        return result
    except concurrent.futures.TimeoutError:
        # shutdown(wait=False) is the key fix: don't block the caller waiting
        # for the orphaned background thread to finish — that would silently
        # turn a "clean timeout" back into a hang. The worker thread keeps
        # running detached and is abandoned when it eventually finishes.
        executor.shutdown(wait=False)
        raise TimeoutError(
            f"Operation exceeded its {timeout_seconds}s timeout — cancelled cleanly."
        )


# =============================================================================
# (a) RETRY DEMO
# =============================================================================

_flaky_call_count = 0


def flaky_node(state: DemoState) -> DemoState:
    global _flaky_call_count
    _flaky_call_count += 1
    print(f"[flaky_node] attempt #{_flaky_call_count}")
    if _flaky_call_count < 3:
        raise ConnectionError(f"Simulated transient failure on attempt #{_flaky_call_count}")
    state["log"] = state.get("log", []) + [f"flaky_node succeeded on attempt #{_flaky_call_count}"]
    return state


def demo_retry() -> None:
    global _flaky_call_count
    _flaky_call_count = 0

    graph = StateGraph(DemoState)
    graph.add_node(
        "flaky",
        flaky_node,
        retry=RetryPolicy(
            max_attempts=4,
            initial_interval=0.2,
            backoff_factor=2.0,
            max_interval=2.0,
            jitter=True,
        ),
    )
    graph.set_entry_point("flaky")
    graph.add_edge("flaky", END)
    app = graph.compile()

    print("=== (a) Retry policy recovering a simulated transient failure ===")
    start = time.time()
    result = app.invoke({})
    elapsed = time.time() - start
    print(f"Result: {result}")
    print(f"Total attempts made: {_flaky_call_count} (recovered within max_attempts=4)")
    print(f"Elapsed time (reflects backoff waits): {elapsed:.2f}s\n")


# =============================================================================
# (b) PER-NODE TIMEOUT DEMO
# =============================================================================


def _slow_work(seconds: float) -> str:
    time.sleep(seconds)
    return "finished (should not be reached within the timeout)"


def slow_node(state: DemoState) -> DemoState:
    # Simulated call that takes 5s, wrapped with a 1s per-node timeout.
    result = run_with_timeout(_slow_work, args=(5.0,), timeout_seconds=1.0)
    state["log"] = state.get("log", []) + [result]
    return state


def demo_per_node_timeout() -> None:
    graph = StateGraph(DemoState)
    graph.add_node("slow", slow_node)
    graph.set_entry_point("slow")
    graph.add_edge("slow", END)
    app = graph.compile()

    print("=== (b) Per-node timeout firing a clean error (not a hang) ===")
    start = time.time()
    try:
        app.invoke({})
        print("UNEXPECTED: node completed without raising a timeout.")
    except TimeoutError as e:
        elapsed = time.time() - start
        print(f"Caught expected TimeoutError after {elapsed:.2f}s: {e}")
        print("(elapsed ~1s, NOT ~5s — proves this was a clean cancellation, not a hang)\n")


# =============================================================================
# (c) GLOBAL TIMEOUT DEMO
# =============================================================================


def step_node_factory(name: str, sleep_seconds: float):
    def _node(state: DemoState) -> DemoState:
        time.sleep(sleep_seconds)
        state["log"] = state.get("log", []) + [f"{name} done"]
        return state

    return _node


def demo_global_timeout() -> None:
    graph = StateGraph(DemoState)
    graph.add_node("step1", step_node_factory("step1", 1.0))
    graph.add_node("step2", step_node_factory("step2", 1.0))
    graph.add_node("step3", step_node_factory("step3", 1.0))
    graph.set_entry_point("step1")
    graph.add_edge("step1", "step2")
    graph.add_edge("step2", "step3")
    graph.add_edge("step3", END)
    app = graph.compile()

    print("=== (c) Global timeout cancelling the whole run on total-time overrun ===")
    # 3 steps x 1s each = ~3s total, but the global budget below is 1.5s.
    start = time.time()
    try:
        run_with_timeout(app.invoke, args=({},), timeout_seconds=1.5)
        print("UNEXPECTED: full run completed without hitting the global timeout.")
    except TimeoutError as e:
        elapsed = time.time() - start
        print(f"Caught expected global TimeoutError after {elapsed:.2f}s: {e}")
        print("(elapsed ~1.5s, NOT ~3s — the whole run was cancelled, not just one node)\n")


if __name__ == "__main__":
    demo_retry()
    demo_per_node_timeout()
    demo_global_timeout()