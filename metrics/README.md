# 📏 Metrics — The Complete Enterprise Reference

> *Every metric defined precisely. When to use each. What each catches and misses.*

---

## The Metric Taxonomy

```
CLASSIFICATION METRICS       (for tasks with discrete labels)
├── Accuracy, Precision, Recall, F1
├── ROC-AUC, PR-AUC
└── Confusion matrix analysis

GENERATION METRICS           (for text outputs)
├── N-gram overlap: BLEU, ROUGE, METEOR, CHRF
├── Semantic: BERTScore, MoverScore, embedding similarity
├── Task-specific: SacreBLEU (translation), CIDEr (captioning)
└── LLM-as-judge scores

EMBEDDING METRICS            (for vector representations)
├── Cosine similarity
├── Euclidean distance
├── Dot product
└── Retrieval metrics: MRR, NDCG, Precision@k, Recall@k, Hit Rate

OPERATIONAL METRICS          (for production monitoring)
├── Latency (p50, p95, p99)
├── Throughput (queries/second)
├── Cost per query
├── Token usage per request
└── Error rates
```

---

## Classification Metrics (`classification_metrics.py`)

For tasks like sentiment classification, intent detection, toxicity detection.

- **Accuracy:** correct / total. Only reliable when classes are balanced.
- **Precision:** TP / (TP + FP). "Of the ones I said were positive, how many actually were?"
- **Recall:** TP / (TP + FN). "Of the actually positive ones, how many did I catch?"
- **F1:** Harmonic mean of precision and recall. Balanced metric.
- **F-beta:** Weighted version — F2 weights recall more, F0.5 weights precision more.

**Threshold-independent:**
- **ROC-AUC:** Area under the receiver operating characteristic curve
- **PR-AUC:** Area under the precision-recall curve (better for imbalanced datasets)

---

## Generation Metrics (`generation_metrics.py`)

### BLEU, ROUGE, METEOR (`bleu_rouge_meteor.py`)

**BLEU** (Bilingual Evaluation Understudy)
- Measures n-gram overlap between generated and reference text
- BLEU-1 (unigrams), BLEU-2, BLEU-3, BLEU-4 (4-grams)
- Weighted by brevity penalty (penalizes short outputs)
- Standard for machine translation
- **Weakness:** doesn't capture meaning, just surface overlap

**ROUGE** (Recall-Oriented Understudy for Gisting Evaluation)
- ROUGE-N: n-gram recall
- ROUGE-L: longest common subsequence
- Standard for summarization
- **Weakness:** same as BLEU — surface-level

**METEOR**
- Adds synonym matching, stemming, word order
- Better correlation with human judgment than BLEU
- Slower to compute

**When to use:** Translation, summarization, when reference outputs exist. **Never use alone** — always combine with semantic metrics.

### BERTScore (`bertscore.py`)

Uses BERT embeddings to measure semantic similarity between generated and reference text.

**How it works:**
1. Encode both texts with BERT
2. For each token in generated, find best-matching token in reference (cosine similarity)
3. Aggregate: BERTScore-Precision, BERTScore-Recall, BERTScore-F1

**Advantages over BLEU/ROUGE:**
- Captures paraphrasing ("car" and "automobile" score high)
- Better correlation with human judgment
- Language-agnostic

**Cost:** Requires a BERT model. Slower than BLEU.

### Semantic Similarity (`semantic_similarity.py`)

Simpler than BERTScore — just cosine similarity of full-text embeddings.
- Fast
- Good for quick eval
- Loses granularity (whole-text similarity, not token-level)

---

## Embedding Metrics (`embedding_metrics.py`)

For retrieval evaluation and vector store analysis:

**Cosine similarity:** `dot(a, b) / (|a| * |b|)`. Range: -1 to 1. Standard for text embeddings.

**Euclidean distance:** L2 distance. Used with L2-normalized embeddings.

**Dot product:** Direct dot(a, b). Used with normalized embeddings for efficiency (FAISS default).

**Retrieval-specific:** MRR, NDCG, Precision@k — covered in `rag_evaluation/retrieval_quality.py`.

---

## Latency and Cost (`latency_and_cost.py`)

Production metrics that MUST be tracked:

**Latency percentiles:**
- **p50 (median):** Half of requests are faster than this
- **p95:** 95% of requests are faster than this
- **p99:** 99% of requests are faster than this — the "tail latency"

**Why p99 matters:** Averages hide problems. If 1% of your users experience 30-second latency, they'll churn.

**Cost metrics:**
- Cost per query (input tokens × input price + output tokens × output price)
- Cost per user per month
- Cost per successful task (accounts for retries and failures)

**Enterprise SLA targets:**
- p50 latency: < 1s for chat, < 5s for complex agents
- p99 latency: < 5s for chat, < 30s for agents
- Cost per query: track and alert on 20%+ increases

---

## Custom Metrics (`custom_metrics.py`)

**When existing metrics don't fit your use case, build custom.**

Framework for custom metrics:
```python
class CustomMetric:
    def __init__(self, name, description):
        self.name = name
        self.description = description
    
    def score(self, prediction, reference=None, context=None) -> float:
        """Return score in 0-1 range."""
        raise NotImplementedError
    
    def batch_score(self, predictions, references=None) -> list[float]:
        return [self.score(p, r) for p, r in zip(predictions, references or [None]*len(predictions))]

# Example: Domain-specific metric
class MedicalTerminologyAccuracy(CustomMetric):
    def score(self, prediction, reference=None, context=None):
        # Extract medical terms from prediction and reference
        # Check if terminology matches accepted medical vocabulary
        # Return precision of medical terms
        ...
```

**When custom metrics are worth building:**
- Domain-specific quality (medical terminology, legal citations)
- Business-critical dimensions (brand voice, product accuracy)
- Composite metrics (weighted combinations of standard metrics)

---

*Previous: [← Red Teaming](../red_teaming/README.md) · Next: [Testing Strategies →](../testing_strategies/README.md)*

*Back to [main README](../../README.md)*
