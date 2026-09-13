import re

def fixed_size_chunks(doc_id: str, text: str, size: int = 200, overlap: int = 50) -> list[dict]:
    """Fixed-size window with overlap. Snaps each window's end to the nearest
    preceding whitespace (when one exists within a small lookback) so chunks
    don't cut a word in half — the window size stays approximately fixed,
    it just doesn't guarantee an exact character count like a naive slice
    would. This does NOT turn it into sentence-based chunking: it still
    ignores sentence boundaries entirely, which sentence_chunks() respects."""
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # snap to the last whitespace within the final 20 chars of the window
            lookback_start = max(start, end - 20)
            snap = text.rfind(" ", lookback_start, end)
            if snap != -1:
                end = snap
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(
                {"chunk_id": f"{doc_id}::fixed::{idx}", "doc_id": doc_id, "text": chunk_text}
            )
            idx += 1
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)  # step forward, re-covering the overlap window
    return chunks


def sentence_chunks(doc_id: str, text: str, sentences_per_chunk: int = 2) -> list[dict]:
    # Simple sentence splitter: split on '.', '!', '?' followed by whitespace.
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    idx = 0
    for i in range(0, len(sentences), sentences_per_chunk):
        group = sentences[i : i + sentences_per_chunk]
        chunk_text = " ".join(group)
        chunks.append(
            {"chunk_id": f"{doc_id}::sent::{idx}", "doc_id": doc_id, "text": chunk_text}
        )
        idx += 1
    return chunks


def build_all_chunks(documents: list[dict]) -> tuple[list[dict], list[dict]]:
    """Returns (fixed_chunks_all_docs, sentence_chunks_all_docs)."""
    fixed_all, sentence_all = [], []
    for doc in documents:
        fixed_all.extend(fixed_size_chunks(doc["doc_id"], doc["text"]))
        sentence_all.extend(sentence_chunks(doc["doc_id"], doc["text"]))
    return fixed_all, sentence_all


if __name__ == "__main__":
    import sys
    import os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "knowledge_base"))
    from docs import DOCUMENTS

    fixed_all, sentence_all = build_all_chunks(DOCUMENTS)
    print(f"Fixed-size chunks:    {len(fixed_all)}")
    print(f"Sentence-based chunks: {len(sentence_all)}")
    print("\nSample fixed chunk:", fixed_all[0])
    print("\nSample sentence chunk:", sentence_all[0])