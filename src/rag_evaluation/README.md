# 🔍 RAG Evaluation — Complete Enterprise Deep Dive

> *A RAG system has two failure modes: bad retrieval or bad generation. This document teaches you to measure both, separately.*

---

## Why RAG Needs Its Own Evaluation

Basic LLM evaluation measures one thing: is the output good?

RAG evaluation must measure THREE things independently:
1. Was the RIGHT context retrieved?
2. Did the LLM USE the retrieved context correctly?
3. Is the FINAL answer good?

Failing at any of these three produces bad output — but each requires a different fix. Conflating them means you'll optimize the wrong thing.

---

## The RAG Evaluation Diamond

```
                    ┌─────────────────────┐
                    │  ANSWER CORRECTNESS  │
                    │  (final quality)      │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                  │
       ┌──────▼──────┐                   ┌──────▼──────┐
       │ ANSWER      │                   │ FAITHFULNESS│
       │ RELEVANCE   │                   │ (grounding) │
       │ (addresses  │                   │             │
       │  query?)    │                   │             │
       └──────┬──────┘                   └──────┬──────┘
              │                                  │
              └────────────────┬─────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                  │
       ┌──────▼──────┐                   ┌──────▼──────┐
       │ CONTEXT     │                   │ CONTEXT     │
       │ PRECISION   │                   │ RECALL      │
       │ (retrieved  │                   │ (retrieved  │
       │  chunks     │                   │  all needed │
       │  relevant?) │                   │  chunks?)   │
       └──────┬──────┘                   └──────┬──────┘
              │                                  │
              └────────────────┬─────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ RETRIEVAL QUALITY    │
                    │ (embedding similarity│
                    │  ranking, etc.)      │
                    └─────────────────────┘
```

Each level measures a different failure mode.

---

## The 6 Core RAG Metrics

### 1. Faithfulness (`faithfulness.py`)

**Definition:** Percentage of claims in the answer that are supported by the retrieved context.

**How it's calculated:**
```
1. Extract atomic claims from the answer
   Answer: "The Transformer was introduced in 2017 by Vaswani at Google Brain."
   Claims: ["Transformer was introduced in 2017", "Introduced by Vaswani", "At Google Brain"]

2. For each claim, check if it's supported by any retrieved chunk
   Claim 1 → context mentions "2017" → SUPPORTED
   Claim 2 → context mentions "Vaswani et al." → SUPPORTED
   Claim 3 → context doesn't mention Google Brain → NOT SUPPORTED

3. Faithfulness = supported_claims / total_claims = 2/3 = 0.67
```

**What it catches:** Hallucination from parametric knowledge — model adding details not in the context.

**What it misses:** Whether the answer is actually correct. A faithful answer can be based on wrong context.

**Production threshold:** > 0.85 for shipping. Below 0.7 = investigate.

### 2. Answer Relevance (`answer_relevance.py`)

**Definition:** How well does the answer address the actual question asked?

**How it's calculated:**
```
1. Given the answer, generate 3-5 questions it would answer
   Answer: "The Transformer uses self-attention."
   Reverse questions: ["What does the Transformer use?", "What is self-attention?", "How does Transformer work?"]

2. Compare reverse-generated questions to the original question
   Original: "How does attention work in Transformers?"
   Similarity to reverse questions: 0.85 (high — the answer addresses this)

3. Answer relevance = mean cosine similarity
```

**What it catches:** Off-topic answers, non-sequiturs, answers to different questions than asked.

### 3. Context Precision (`context_precision.py`)

**Definition:** Of the retrieved chunks, what fraction are actually relevant to the query?

**How it's calculated:**
```
Retrieved: [chunk_1, chunk_2, chunk_3, chunk_4, chunk_5]
For each chunk, LLM judge: is this relevant to the query?
Relevant: [YES, YES, NO, YES, NO]
Context Precision = 3/5 = 0.6

Ranked variant (weight top chunks more):
  Precision@k = sum(relevance_i / rank_i) / total_relevant
```

**What it catches:** Retrieval that pulls too much noise. Wasted context window.

**Production threshold:** > 0.75. Below 0.6 = retrieval needs improvement.

### 4. Context Recall (`context_recall.py`)

**Definition:** Did the retrieval find ALL the information needed to answer the question?

**How it's calculated (requires ground truth):**
```
Ground truth answer: "The Transformer was introduced in 2017 by Vaswani. It uses self-attention and enables parallel processing."

Required facts to answer: [
  "Transformer introduced in 2017",
  "Introduced by Vaswani",
  "Uses self-attention",
  "Enables parallel processing"
]

For each required fact, check if it's in the retrieved context:
[YES, YES, YES, NO]

Context Recall = 3/4 = 0.75
```

**What it catches:** Retrieval that misses critical information. The LLM can't use what it wasn't given.

**Production threshold:** > 0.8. Below 0.7 = retrieval strategy needs revision (better chunking, hybrid search, re-ranking).

### 5. Answer Correctness (`answer_correctness.py`)

**Definition:** Is the answer actually correct? (Requires ground truth.)

**How it's calculated:**
```
Method 1 (Factual): Semantic similarity between generated answer and ground truth
Method 2 (Claim-based): 
  - Extract claims from ground truth (TP set)
  - Extract claims from generated answer
  - Compute: True Positives (in both), False Positives (in answer only), False Negatives (in truth only)
  - F1 score of claims
```

**What it catches:** Everything that other metrics miss. This is the ultimate quality measure.

### 6. Groundedness (`groundedness.py`)

**Definition:** Are answer statements traceable to specific retrieved sources? (Enterprise-critical for auditability.)

**Difference from faithfulness:** Faithfulness = "supported by context." Groundedness = "you can cite the specific source chunk for every claim."

**Implementation:**
```python
for claim in extract_claims(answer):
    supporting_chunks = find_supporting_chunks(claim, retrieved_context)
    if not supporting_chunks:
        return "UNGROUNDED"
    citation = {"claim": claim, "sources": [c.chunk_id for c in supporting_chunks]}
```

**Production requirement:** Regulated industries (medical, legal, financial) require groundedness scores of 1.0 — every claim must be citable.

---

## Retrieval-Only Metrics (`retrieval_quality.py`)

These metrics measure the retrieval step in isolation, before generation.

### Precision@k
Of the top-k retrieved chunks, how many are relevant?

### Recall@k
Of all relevant chunks in the corpus, how many appear in the top-k?

### Mean Reciprocal Rank (MRR)
For each query, what's the rank of the first relevant chunk? Averaged across queries.
- MRR = 1.0 → first result is always relevant
- MRR = 0.5 → first relevant result is on average at position 2
- MRR = 0.1 → first relevant is on average at position 10 (bad)

### Normalized Discounted Cumulative Gain (NDCG)
Rewards ranking relevant results HIGHER, not just including them. The industry standard for search ranking quality.

```
NDCG@k = DCG@k / IDCG@k
DCG@k = sum(relevance_i / log2(i+1))  for i in 1..k
IDCG@k = same, but with ideal ranking
```

### Hit Rate
Simplest metric: does at least one relevant chunk appear in top-k? Binary yes/no per query, averaged.

---

## The End-to-End RAG Eval Pipeline (`end_to_end_rag_eval.py`)

Enterprise RAG evaluation runs all metrics in a single pipeline:

```
For each (query, ground_truth) in eval_dataset:
    1. Run RAG pipeline → get (answer, retrieved_chunks)
    
    2. Retrieval metrics:
       - Precision@k
       - Recall@k
       - MRR
       - NDCG
    
    3. Context metrics:
       - Context Precision (LLM judges each chunk)
       - Context Recall (against ground truth facts)
    
    4. Answer metrics:
       - Faithfulness (claims supported by context?)
       - Answer Relevance (addresses the query?)
       - Answer Correctness (matches ground truth?)
       - Groundedness (traceable to sources?)
    
    5. Cost/latency:
       - Retrieval latency
       - Generation latency
       - Token cost
    
    6. Log full trace for debugging

Aggregate:
    - Per-metric averages
    - Per-category breakdowns
    - Failure analysis (which queries scored < threshold?)
    - Comparison to previous version (regression check)
```

---

## Interpreting Metric Combinations

The value comes from analyzing metrics TOGETHER, not in isolation:

| Faithfulness | Relevance | Context Precision | Diagnosis |
|---|---|---|---|
| High | High | High | ✅ System working well |
| Low | High | High | Model ignoring context, hallucinating |
| High | Low | High | Retrieval getting wrong chunks (relevant but not to THIS query) |
| High | High | Low | Retrieval noisy but LLM extracting the right parts |
| Low | Low | Low | 🔥 Full pipeline broken, investigate everything |
| High | Low | Low | Rare — retrieval bad + answer somehow addresses off-topic |

---

## Threshold-Based Release Gates (Production Pattern)

Production RAG systems block deploys when metrics drop:

```python
# In your CI/CD pipeline
eval_results = run_rag_eval(new_version)

RELEASE_THRESHOLDS = {
    "faithfulness": 0.85,
    "answer_relevance": 0.80,
    "context_precision": 0.75,
    "context_recall": 0.80,
    "answer_correctness": 0.80,
}

REGRESSION_TOLERANCE = 0.02  # allow 2% quality drop

for metric, threshold in RELEASE_THRESHOLDS.items():
    if eval_results[metric] < threshold:
        raise ReleaseBlock(f"{metric} below threshold: {eval_results[metric]:.2f}")
    if eval_results[metric] < prev_version[metric] - REGRESSION_TOLERANCE:
        raise ReleaseBlock(f"{metric} regression from {prev_version[metric]:.2f} to {eval_results[metric]:.2f}")
```

---

## Files in This Directory

| File | Metric / Component |
|---|---|
| `faithfulness.py` | Are claims supported by context? |
| `answer_relevance.py` | Does the answer address the query? |
| `context_precision.py` | Are retrieved chunks relevant? |
| `context_recall.py` | Are all needed chunks retrieved? |
| `answer_correctness.py` | Is the answer factually correct? |
| `groundedness.py` | Traceable citations per claim |
| `retrieval_quality.py` | MRR, NDCG, Precision@k, Recall@k, Hit Rate |
| `end_to_end_rag_eval.py` | Full evaluation pipeline |

---

*Previous: [← LLM Evaluation](../llm_evaluation/README.md) · Next: [Agent Evaluation →](../agent_evaluation/README.md)*

*Back to [main README](../../README.md)*
