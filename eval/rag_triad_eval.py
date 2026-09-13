import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag"))
from retrieve import generate_answer, THRESHOLD  # noqa: E402
from indexer import build_indexes, get_model  # noqa: E402
from test_queries import TEST_QUERIES  # noqa: E402

_WORD_RE = re.compile(r"[a-zA-Z]+")


def _words(text: str) -> set:
    return set(w.lower() for w in _WORD_RE.findall(text))


def groundedness_score(answer: str, retrieved_chunks: list[dict]) -> float:
    answer_words = _words(answer)
    if not answer_words:
        return 0.0
    context_words = set()
    for c in retrieved_chunks:
        context_words |= _words(c["text"])
    if not context_words:
        return 0.0
    return len(answer_words & context_words) / len(answer_words)


def cosine_similarity(vec_a, vec_b) -> float:
    a, b = np.array(vec_a), np.array(vec_b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def answer_relevance_score(query: str, answer: str) -> float:
    model = get_model()
    q_emb, a_emb = model.encode([query, answer])
    return cosine_similarity(q_emb, a_emb)


def evaluate_all(collection) -> list[dict]:
    results = []
    for item in TEST_QUERIES:
        query = item["query"]
        result = generate_answer(query, collection)

        context_relevance = result["top1_similarity"]
        groundedness = groundedness_score(result["answer"], result["retrieved"])
        answer_relevance = answer_relevance_score(query, result["answer"])

        results.append(
            {
                "query": query,
                "type": item["type"],
                "topic": item["topic"],
                "is_fallback": result["is_fallback"],
                "context_relevance": round(context_relevance, 3),
                "groundedness": round(groundedness, 3),
                "answer_relevance": round(answer_relevance, 3),
            }
        )
    return results


def print_report(results: list[dict]) -> None:
    print(f"{'#':<3} {'type':<12} {'topic':<22} {'ctx_rel':<8} {'ground':<8} {'ans_rel':<8} query")
    print("-" * 100)
    for i, r in enumerate(results, 1):
        topic = r["topic"] or "-"
        print(
            f"{i:<3} {r['type']:<12} {topic:<22} {r['context_relevance']:<8} "
            f"{r['groundedness']:<8} {r['answer_relevance']:<8} {r['query'][:40]}"
        )

    n = len(results)
    avg_ctx = sum(r["context_relevance"] for r in results) / n
    avg_ground = sum(r["groundedness"] for r in results) / n
    avg_rel = sum(r["answer_relevance"] for r in results) / n

    print("-" * 100)
    print(f"AVERAGES over {n} queries:")
    print(f"  avg context_relevance = {avg_ctx:.3f}")
    print(f"  avg groundedness      = {avg_ground:.3f}")
    print(f"  avg answer_relevance  = {avg_rel:.3f}")


if __name__ == "__main__":
    fixed_col, _ = build_indexes()
    results = evaluate_all(fixed_col)
    print_report(results)