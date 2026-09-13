import os
import sys
import time
import uuid

from fastapi import FastAPI
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "knowledge_base"))

from graph import build_graph, run_query  # noqa: E402
from indexer import build_indexes  # noqa: E402
from chunking import fixed_size_chunks, sentence_chunks  # noqa: E402
from indexer import get_model  # noqa: E402
from api.logging_utils import log_request  # noqa: E402

app = FastAPI(title="Nykaa Support Agent API")

# Build indexes and the compiled graph once at startup.
_fixed_col, _sentence_col = build_indexes(reset=True)
_agent_app = build_graph(_fixed_col)


class AskRequest(BaseModel):
    query: str = Field(..., description="The customer's question")
    thread_id: str = Field(default="default-thread", description="Conversation thread identifier")


class AskResponse(BaseModel):
    query: str
    source: str
    answer: str
    is_fallback: bool
    escalation_score: float | None
    retrieved_doc_ids: list[str]
    trace_id: str


class AddDocumentRequest(BaseModel):
    doc_id: str = Field(..., description="Unique document identifier")
    title: str
    text: str = Field(..., description="Full document text, 2-5 sentences recommended")


class AddDocumentResponse(BaseModel):
    success: bool
    doc_id: str
    fixed_chunks_added: int
    sentence_chunks_added: int


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    start = time.time()
    response = run_query(_agent_app, request.thread_id, request.query)
    duration_ms = (time.time() - start) * 1000

    log_request(response["trace_id"], request.query, response, duration_ms)

    return AskResponse(**response)


@app.post("/add-document", response_model=AddDocumentResponse)
def add_document(request: AddDocumentRequest) -> AddDocumentResponse:
    model = get_model()

    new_fixed = fixed_size_chunks(request.doc_id, request.text)
    new_sentence = sentence_chunks(request.doc_id, request.text)

    for chunks, col in [(new_fixed, _fixed_col), (new_sentence, _sentence_col)]:
        texts = [c["text"] for c in chunks]
        embeddings = model.encode(texts).tolist()
        col.add(
            ids=[c["chunk_id"] for c in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[{"doc_id": c["doc_id"]} for c in chunks],
        )

    return AddDocumentResponse(
        success=True,
        doc_id=request.doc_id,
        fixed_chunks_added=len(new_fixed),
        sentence_chunks_added=len(new_sentence),
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)