import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from indexer import build_indexes  # noqa: E402
from retrieve import retrieve, DEMO_QUERIES, TOP_K  # noqa: E402


def precision_recall_at_k(retrieved_chunks: list[dict], relevant_doc_ids: list[str], k: int) -> tuple[float, float, list[str]]:
    # Map chunks -> parent doc_ids, dedup, preserve order, cap at k.
    seen = []
    for chunk in retrieved_chunks:
        if chunk["doc_id"] not in seen:
            seen.append(chunk["doc_id"])
    top_k_docs = seen[:k]

    hits = [d for d in top_k_docs if d in relevant_doc_ids]
    precision = len(hits) / k
    recall = len(hits) / len(relevant_doc_ids)
    return precision, recall, top_k_docs


def evaluate_collection(collection_name: str, collection) -> dict:
    print(f"\n=== {collection_name} ===")
    precisions, recalls = [], []
    for item in DEMO_QUERIES:
        query, relevant = item["query"], item["relevant_doc_ids"]
        retrieved = retrieve(query, collection, k=TOP_K)
        precision, recall, top_k_docs = precision_recall_at_k(retrieved, relevant, TOP_K)
        precisions.append(precision)
        recalls.append(recall)

        hits = [d for d in top_k_docs if d in relevant]
        print(f"\nQuery: {query!r}")
        print(f"  relevant_doc_ids   = {relevant}")
        print(f"  top-{TOP_K} unique docs = {top_k_docs}")
        print(f"  hits = {hits}")
        print(f"  Precision@{TOP_K} = {len(hits)}/{TOP_K} = {precision:.3f}")
        print(f"  Recall@{TOP_K}    = {len(hits)}/{len(relevant)} = {recall:.3f}")

    avg_precision = sum(precisions) / len(precisions)
    avg_recall = sum(recalls) / len(recalls)
    print(f"\n{collection_name} AVERAGES over {len(DEMO_QUERIES)} queries:")
    print(f"  avg Precision@{TOP_K} = {avg_precision:.3f}")
    print(f"  avg Recall@{TOP_K}    = {avg_recall:.3f}")

    return {"avg_precision": avg_precision, "avg_recall": avg_recall}


if __name__ == "__main__":
    fixed_col, sentence_col = build_indexes()

    fixed_results = evaluate_collection("fixed_chunks_collection", fixed_col)
    sentence_results = evaluate_collection("sentence_chunks_collection", sentence_col)

    print("\n\n=== RECOMMENDATION ===")
    print(f"fixed_chunks_collection:    avg P@3={fixed_results['avg_precision']:.3f}, avg R@3={fixed_results['avg_recall']:.3f}")
    print(f"sentence_chunks_collection: avg P@3={sentence_results['avg_precision']:.3f}, avg R@3={sentence_results['avg_recall']:.3f}")
    print(
        "\n[Fill this in after running with real embeddings:] "
        "State which collection scored higher and recommend deploying that "
        "chunking strategy, citing the two avg P@3 / R@3 numbers above. If "
        "they tie, prefer sentence-based chunking since it never splits a "
        "sentence mid-thought, which tends to keep retrieved context more "
        "coherent for the MOCK_LLM's template-based generation."
    )