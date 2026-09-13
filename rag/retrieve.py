import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from indexer import get_model, build_indexes  # noqa: E402

# ---- Queries used across Task 4 and Task 5 ----------------------------------

# 5 in-scope demo queries, each with its ground-truth relevant doc_id(s),
# reused by eval_retrieval.py (Task 5) for Precision@3 / Recall@3.
DEMO_QUERIES = [
    {"query": "How long do I have to return a beauty product?", "relevant_doc_ids": ["return_window"]},
    {"query": "When will I get my refund for a COD order?", "relevant_doc_ids": ["cod_refund"]},
    {"query": "How many days does standard delivery usually take?", "relevant_doc_ids": ["delivery_sla"]},
    {"query": "Can I exchange my shoes for a different size?", "relevant_doc_ids": ["size_exchange"]},
    {"query": "What happens if my payment fails during checkout?", "relevant_doc_ids": ["payment_failure"]},
]

OUT_OF_SCOPE_DEMO_QUERY = "What is the capital of France?"

# Calibration set: 3 in-scope (reused from DEMO_QUERIES) + 2 out-of-scope.
CALIBRATION_IN_SCOPE = [q["query"] for q in DEMO_QUERIES[:3]]
CALIBRATION_OUT_OF_SCOPE = [
    "What is the capital of France?",
    "How do I train a neural network from scratch?",
]

# Placeholder until calibrate_threshold() is run and README is updated with
# the observed values. 0.35 is NOT a tutorial default being used blindly —
# it's a starting placeholder; replace it with your measured midpoint.
THRESHOLD = 0.347
TOP_K = 3


def retrieve(query: str, collection, k: int = TOP_K) -> list[dict]:
    model = get_model()
    q_emb = model.encode([query]).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=k)

    results = []
    for doc, dist, meta, chunk_id in zip(
        res["documents"][0], res["distances"][0], res["metadatas"][0], res["ids"][0]
    ):
        results.append(
            {
                "chunk_id": chunk_id,
                "doc_id": meta["doc_id"],
                "text": doc,
                "similarity": 1 - dist,  # cosine space: distance -> similarity
            }
        )
    return results


def generate_answer(query: str, collection, threshold: float = THRESHOLD, k: int = TOP_K) -> dict:
    retrieved = retrieve(query, collection, k=k)
    top1_similarity = retrieved[0]["similarity"] if retrieved else 0.0

    if not retrieved or top1_similarity < threshold:
        return {
            "query": query,
            "answer": "I don't know — I couldn't find this in our policy documents.",
            "is_fallback": True,
            "top1_similarity": top1_similarity,
            "retrieved": retrieved,
        }

    # MOCK_LLM "generation": template-extract from the top retrieved chunk
    # only — never adds anything outside the retrieved context.
    top_chunk = retrieved[0]
    answer = f"Based on our policy: {top_chunk['text']}"

    return {
        "query": query,
        "answer": answer,
        "is_fallback": False,
        "top1_similarity": top1_similarity,
        "retrieved": retrieved,
    }


def calibrate_threshold(collection) -> None:
    print("=== Threshold calibration ===")
    in_scope_sims = []
    print("\nIn-scope queries:")
    for q in CALIBRATION_IN_SCOPE:
        r = retrieve(q, collection, k=1)
        sim = r[0]["similarity"] if r else 0.0
        in_scope_sims.append(sim)
        print(f"  top1_similarity={sim:.3f}  query={q!r}")

    out_of_scope_sims = []
    print("\nOut-of-scope queries:")
    for q in CALIBRATION_OUT_OF_SCOPE:
        r = retrieve(q, collection, k=1)
        sim = r[0]["similarity"] if r else 0.0
        out_of_scope_sims.append(sim)
        print(f"  top1_similarity={sim:.3f}  query={q!r}")

    min_in_scope = min(in_scope_sims)
    max_out_of_scope = max(out_of_scope_sims)
    print(f"\nmin(in-scope)={min_in_scope:.3f}   max(out-of-scope)={max_out_of_scope:.3f}")
    if min_in_scope > max_out_of_scope:
        suggested = (min_in_scope + max_out_of_scope) / 2
        print(f"Clusters separate cleanly. Suggested threshold (midpoint): {suggested:.3f}")
    else:
        print(
            "WARNING: clusters overlap — in-scope and out-of-scope similarities are not "
            "cleanly separated. Consider a different k, a different chunking strategy, "
            "or more distinct calibration queries before picking a threshold."
        )


if __name__ == "__main__":
    fixed_col, sentence_col = build_indexes()

    print("\n########## CALIBRATION (fixed_chunks_collection) ##########")
    calibrate_threshold(fixed_col)

    print("\n\n########## DEMO: 5 in-scope + 1 out-of-scope ##########")
    for q in DEMO_QUERIES:
        result = generate_answer(q["query"], fixed_col)
        print(f"\nQ: {result['query']}")
        print(f"top1_similarity={result['top1_similarity']:.3f}  fallback={result['is_fallback']}")
        print(f"A: {result['answer'][:150]}")

    result = generate_answer(OUT_OF_SCOPE_DEMO_QUERY, fixed_col)
    print(f"\nQ: {result['query']}")
    print(f"top1_similarity={result['top1_similarity']:.3f}  fallback={result['is_fallback']}")
    print(f"A: {result['answer']}")