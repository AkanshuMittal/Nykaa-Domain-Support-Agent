import os
import sys

import chromadb
from sentence_transformers import SentenceTransformer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "knowledge_base"))
from docs import DOCUMENTS  # noqa: E402
from chunking import build_all_chunks  # noqa: E402

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_store")

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=CHROMA_PATH)


def build_indexes(reset: bool = True) -> tuple[chromadb.Collection, chromadb.Collection]:
    fixed_all, sentence_all = build_all_chunks(DOCUMENTS)
    model = get_model()
    client = get_client()

    if reset:
        for name in ["fixed_chunks_collection", "sentence_chunks_collection"]:
            try:
                client.delete_collection(name)
            except Exception:
                pass

    fixed_col = client.get_or_create_collection(
        "fixed_chunks_collection", metadata={"hnsw:space": "cosine"}
    )
    sentence_col = client.get_or_create_collection(
        "sentence_chunks_collection", metadata={"hnsw:space": "cosine"}
    )

    for name, chunks, col in [
        ("fixed", fixed_all, fixed_col),
        ("sentence", sentence_all, sentence_col),
    ]:
        texts = [c["text"] for c in chunks]
        embeddings = model.encode(texts).tolist()
        col.add(
            ids=[c["chunk_id"] for c in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[{"doc_id": c["doc_id"]} for c in chunks],
        )
        print(f"Indexed {len(chunks)} {name} chunks into '{col.name}'")

    return fixed_col, sentence_col


if __name__ == "__main__":
    fixed_col, sentence_col = build_indexes()

    query = "How long do I have to return a beauty product?"
    model = get_model()
    q_emb = model.encode([query]).tolist()

    print(f"\nSample query: {query!r}")
    for name, col in [("fixed_chunks_collection", fixed_col), ("sentence_chunks_collection", sentence_col)]:
        res = col.query(query_embeddings=q_emb, n_results=3)
        print(f"\nTop-3 from {name}:")
        for doc, dist, meta in zip(res["documents"][0], res["distances"][0], res["metadatas"][0]):
            similarity = 1 - dist
            print(f"  sim={similarity:.3f}  doc_id={meta['doc_id']}  text={doc[:80]!r}")