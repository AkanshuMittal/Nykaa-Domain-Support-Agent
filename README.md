# Nykaa Domain Support Agent

**Track completed: Nykaa (E-commerce & Retail)**

This repository implements a LangGraph-orchestrated support agent for Nykaa,
covering RAG-based policy Q&A, order-status lookup with a designed escalation
score, persisted memory, guardrails, a FastAPI deployment with structured
logging and RAG-triad evaluation, an MCP-exposed tool, SQLite checkpointing,
and timeout/retry resilience — all runnable under `MOCK_LLM` with **zero API
keys and zero network access at inference time** (only the one-time
SentenceTransformers model download needs internet).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Project Structure

```text
Nykaa-Support-Agent/
│
├── agent/
│   ├── graph.py
│   ├── guardrails.py
│   ├── memory.py
│   ├── schema.py
│   └── tools.py
│
├── api/
│   ├── main.py
│   └── logging_utils.py
│
├── eval/
│   ├── rag_triad_eval.py
│   └── test_queries.py
│
├── knowledge_base/
│   └── docs.py
│
├── mcp/
│   ├── server.py
│   └── client.py
│
├── rag/
│   ├── chunking.py
│   ├── eval_retrieval.py
│   ├── indexer.py
│   └── retrieve.py
│
├── resilience/
│   ├── checkpointed_graph.py
│   └── timeouts_retries.py
│
├── transcripts/
│   ├── part1_transcripts.txt
│   ├── part2_transcripts.txt
│   ├── part3_transcripts.txt
│   └── part4_transcripts.txt
│
├── dataset.py
├── requirements.txt
├── README.md
│
├── chroma_store/              # generated local vector database
├── checkpoints.sqlite         # generated SQLite checkpoint database
├── conversation_memory.json   # generated conversation memory
└── requests.jsonl             # generated API request logs

## Part 1 — Dataset & RAG Core

### Task 1 — Dataset design choices

- **Seed:** `42`
- **Record count:** 60 (above the required minimum of 40)
- **Category weighting:** every category (`Apparel`, `Electronics`, `Home`,
  `Footwear`, `Beauty`) is guaranteed >= 3 records via round-robin seeding,
  remaining slots filled uniformly at random.
- **Status weighting:** `{Placed: 0.15, Shipped: 0.25, Delivered: 0.35,
  Returned: 0.15, Refunded: 0.10}` — modeling a realistic funnel where most
  orders have progressed past "Placed".
- **`order_value_inr` range:** ₹150–₹12,000. Reasoning: Nykaa sells
  everything from a ₹150 lipstick to premium electronics/home appliances in
  the ₹10k+ range, so a wide range models real order-value spread.
- **`delayed_shipment` probability:** `0.18` (Bernoulli draw), verified by
  direct count to land inside the required 10-30% band.
- **Verified output (run `python3 dataset.py` to reproduce):**
  ```
  Category counts: Apparel=16, Electronics=13, Home=11, Footwear=9, Beauty=11  (all >= 3)
  Status counts:   Placed=9, Shipped=14, Delivered=19, Returned=10, Refunded=8 (all >= 1)
  delayed_shipment=True: 13/60 = 21.7%  (within the required 10-30% band)
  ```

### Task 4 — Threshold calibration

Run `python3 rag/retrieve.py` to reproduce. Measured top-1 cosine
similarities on `fixed_chunks_collection`:

| Query | Type | top-1 similarity |
|---|---|---|
| "How long do I have to return a beauty product?" | in-scope | 0.629 |
| "When will I get my refund for a COD order?" | in-scope | 0.741 |
| "How many days does standard delivery usually take?" | in-scope | 0.619 |
| "What is the capital of France?" | out-of-scope | 0.091 |
| "How do I train a neural network from scratch?" | out-of-scope | 0.036 |

min(in-scope) = 0.619, max(out-of-scope) = 0.091 — the two clusters separate
cleanly with a wide gap.

**Chosen threshold: `0.355`** (midpoint of 0.619 and 0.091). `THRESHOLD` in
`rag/retrieve.py` is set to `0.35`, which is consistent with this measured
value (both correctly classify all 6 calibration/demo queries below).

Demonstrated on 5 in-scope + 1 out-of-scope query — all 5 in-scope queries
returned a grounded answer (similarity 0.523–0.741, all above threshold);
the out-of-scope query ("What is the capital of France?", similarity 0.091)
correctly triggered the "I don't know" fallback.

### Task 5 — Precision@3 / Recall@3 (both collections)

| Query | Relevant doc | `fixed_chunks` top-3 | `sentence_chunks` top-3 | P@3 (both) | R@3 (both) |
|---|---|---|---|---|---|
| How long do I have to return a beauty product? | return_window | return_window, warranty_terms | warranty_terms, return_window | 0.333 | 1.000 |
| When will I get my refund for a COD order? | cod_refund | cod_refund | cod_refund, order_cancellation | 0.333 | 1.000 |
| How many days does standard delivery usually take? | delivery_sla | delivery_sla, size_exchange | delivery_sla, damaged_item | 0.333 | 1.000 |
| Can I exchange my shoes for a different size? | size_exchange | size_exchange, return_window | size_exchange, reverse_pickup | 0.333 | 1.000 |
| What happens if my payment fails during checkout? | payment_failure | payment_failure | payment_failure, order_cancellation | 0.333 | 1.000 |

**`fixed_chunks_collection` averages:** avg P@3 = 0.333, avg R@3 = 1.000
**`sentence_chunks_collection` averages:** avg P@3 = 0.333, avg R@3 = 1.000

**Recommendation:** the two strategies tie exactly on this 5-query set (avg
P@3=0.333, avg R@3=1.000 for both) — every query's relevant document was
retrieved in the top-3 for both chunking strategies, so retrieval quality
is indistinguishable at this KB size. Given the tie, **I'd deploy
sentence-based chunking**: it never splits a sentence mid-thought, unlike
fixed-size chunking, which (before a word-boundary-snapping fix applied
during development) was observed producing chunks starting mid-word — e.g.
an early transcript showed a chunk beginning "nd Footwear..." from a split
"and Footwear". Sentence-based chunking keeps retrieved context more
coherent for generation at no retrieval-quality cost here, and doesn't
depend on a boundary-snapping fix to avoid that class of bug at all.

## Part 2 — Agent

### Task 6 — Escalation score formula

```
escalation_score = 0.6 * delayed_component + 0.4 * recency_component
  delayed_component = 1.0 if delayed_shipment else 0.0
  recency_component = min(days_since_created, 30) / 30
```

**Escalation threshold: `0.6133`** — the 80th percentile of
`escalation_score` computed across all 60 records in the generated dataset
(seed=42). Orders scoring above this are recommended for escalation (the
top ~20% most concerning orders).

### Tasks 7-10 — Graph, memory, schema, guardrails

Run `python3 agent/graph.py` to reproduce transcripts for:
- both routing paths (RAG vs order-lookup) firing on different queries
- multi-turn memory on one thread + a separate fresh-thread transcript
  showing no carried-over state
- the guardrail-blocked path firing on a prompt-injection test query

Run `python3 agent/guardrails.py` for isolated PII-masking and
injection-detection demonstrations.

Paste full terminal output into `transcripts/part2_transcripts.txt`.

## Part 3 — FastAPI, Logging, Evaluation

### Task 11-12 — API + logging

```bash
uvicorn api.main:app --reload --port 8000
```

Endpoints: `POST /ask`, `POST /add-document`, `GET /health`. Every `/ask`
call writes one JSON-Lines entry to `requests.jsonl` with a `trace_id`,
timing, and the **masked** query text — verified in `api/logging_utils.py`'s
own test that raw phone/card digits never reach disk.

query             : What's the return window for footwear?
source            : rag
answer            : Based on our policy: nd Footwear can be returned within 15 days as long as tags are attached and the item is unworn. Electronics and Home 
                    appliances carry a shorter 10-day return window because these items are checked
is_fallback       : False
escalation_score  : 
retrieved_doc_ids : {return_window, size_exchange}
trace_id          : 15244a03-b8f2-4c91-8e47-f5863baf3559

### Task 13 — RAG-triad evaluation

Run `python3 eval/rag_triad_eval.py` to reproduce.

| # | Type | Topic | context_relevance | groundedness | answer_relevance | Query |
|---|---|---|---|---|---|---|
| 1 | in_scope | return_window | 0.629 | 0.903 | 0.633 | How long do I have to return a beauty product? |
| 2 | in_scope | cod_refund | 0.769 | 0.867 | 0.783 | When will my COD refund reach my bank account? |
| 3 | in_scope | delivery_sla | 0.786 | 0.867 | 0.766 | How many days does standard delivery take? |
| 4 | in_scope | reverse_pickup | 0.815 | 0.900 | 0.792 | Is reverse pickup available for my pin code? |
| 5 | in_scope | warranty_terms | 0.600 | 0.900 | 0.609 | Does my hair straightener come with a warranty? |
| 6 | in_scope | order_cancellation | 0.759 | 0.875 | 0.754 | Can I cancel my order after it has shipped? |
| 7 | in_scope | loyalty_points | 0.767 | 0.879 | 0.747 | How do I redeem my Nykaa Prive loyalty points? |
| 8 | in_scope | payment_failure | 0.727 | 0.871 | 0.713 | What happens if my payment fails during checkout? |
| 9 | in_scope | size_exchange | 0.523 | 0.903 | 0.508 | Can I exchange my shoes for a different size? |
| 10 | in_scope | damaged_item | 0.656 | 0.909 | 0.639 | My product arrived damaged, how do I report it? |
| 11 | in_scope | international_shipping | 0.496 | 0.893 | 0.478 | Can I place an international order from the US? |
| 12 | in_scope | escalation_matrix | 0.505 | 0.857 | 0.527 | When does my complaint get escalated to a manager? |
| 13 | out_of_scope | — | 0.091 | 0.000 | 0.078 | What is the capital of France? |
| 14 | out_of_scope | — | 0.036 | 0.091 | -0.093 | How do I train a neural network from scratch? |
| 15 | edge_case | return_window | 0.542 | 0.900 | 0.531 | returns? |

**Averages over 15 queries:** avg context_relevance = **0.580**, avg
groundedness = **0.774**, avg answer_relevance = **0.564**.

The two out-of-scope queries correctly pull down all three averages (near-zero
scores) since the agent's fallback response is, correctly, not grounded in or
relevant to a nonsense query — this is the expected behavior, not a defect.

**MOCK_LLM judge formulas used** (documented in `eval/rag_triad_eval.py`):
- `context_relevance` = retriever's top-1 cosine similarity
- `groundedness` = fraction of the answer's distinct words also present in
  the retrieved context
- `answer_relevance` = cosine similarity between the query's and the
  answer's embeddings


## Part 4 — MCP, Checkpointing, Resilience

### Task 14 — MCP

```bash
# terminal 1
python3 mcp/server.py
# terminal 2
python3 mcp/client.py
```

Confirmed: standalone MCP client round-trips `check_order_status` for
`ORD-0001`, `ORD-0002`, and a not-found case (`ORD-9999`), all returning a
standardized `CallToolResult`.

### Task 15 — SQLite checkpointing

```bash
python3 resilience/checkpointed_graph.py
```

Confirmed via `[NODE] ... executing` print statements: the first invocation
stops before `output_guardrail` (after `input_guardrail`, `router`,
`order_lookup_node` have run); resuming the same `thread_id` with `None`
input runs only `output_guardrail` and `memory_write` — the first three
nodes do **not** re-execute, proving their results were loaded from
`checkpoints.sqlite`.

### Task 16 — Timeouts and retries

```bash
python3 resilience/timeouts_retries.py
```

Confirmed:
- (a) retry policy recovers a simulated `ConnectionError` within
  `max_attempts=4` (succeeds on attempt 3)
- (b) a per-node timeout (1s) cleanly cancels a simulated 5s call —
  elapsed ~1s, not ~5s
- (c) a global timeout (1.5s) cleanly cancels a simulated ~3s multi-step run
  — elapsed ~1.5s, not ~3s

