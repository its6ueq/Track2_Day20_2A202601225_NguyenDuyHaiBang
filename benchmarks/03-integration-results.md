# 03 - Integrate: RAG pipeline run

Host `Linux-x86_64` · llama.cpp `b10488` ·
retrieval backend: **keyword overlap** · 3 queries

| Query | Contexts retrieved | embed (ms) | retrieve (ms) | llm (ms) | total (ms) |
|:--|--:|--:|--:|--:|--:|
| Why is goodput more useful than raw throughp... | goodput, paged, radix | 0.0 | 0.0 | 20372.0 | 20372.1 |
| What problem does PagedAttention actually so... | paged, radix, disagg | 0.0 | 0.0 | 15255.6 | 15255.6 |
| When does splitting prefill and decode help?... | disagg, radix, batching | 0.0 | 0.0 | 15622.8 | 15622.9 |

Mean per stage (ms): embed **0.0** · retrieve **0.0** ·
llm **17083.5** · total **17083.5**
Dominant stage: **llm** (100% of total)

## Answers returned

**Why is goodput more useful than raw throughput?**

> Goodput@SLO counts only the requests per second that met the TTFT and TPOT targets. Throughput at saturation ignores SLOs.

**What problem does PagedAttention actually solve?**

> PagedAttention stores the KV cache in non-contiguous pages, removing the internal fragmentation that wasted most GPU memory.

**When does splitting prefill and decode help?**

> Splitting prefill and decode helps because prefill is compute-bound and decode is memory-bandwidth-bound.


### Component Declaration & Pipeline Latency Analysis

- **Module Status Declaration**:
  - **N16 (Document Ingestion & Chunking)**: **Stub** — the 6 documents come from the hard-coded `TOY_DOCS` list in `pipeline.py`; no ingestion or chunking code of my own runs.
  - **N17 (Embedding Generation)**: **Stub** (0.0 ms; no `--embed-url` server, so it falls back to keyword matching instead of a dense vector model).
  - **N18 (Vector Store / Retrieval Index)**: **Stub** (0.0 ms; keyword overlap scoring over the in-memory list).
  - **N19 (Vector + features / Prompt Construction)**: **Real code** (`build_prompt()` assembles system prompt + retrieved context per query) but it is fed by the stubbed N16/N18 above, so the retrieval quality is toy.
  - **N20 (Serving)**: **Real** (17,083.5 ms; HTTP calls to `llama-server` b10488 `/v1/chat/completions`).
- **Dominant Stage**: **LLM Generation** accounts for **100% of total pipeline latency** (17,083.5 ms out of 17,083.5 ms). This completely aligns with expectations for local CPU-based LLM inference.
- **Latency Reduction Strategy**: To halve this pipeline's end-to-end latency, the target MUST be the LLM stage. The most effective optimization is **Prompt Caching (Prefix Caching)**: since RAG context documents are frequently reused across queries, caching the prefill KV state avoids redundant matrix operations on system and context tokens, reducing TTFT by 80-90%.

