# 🎯 LLM Evaluation — Complete Enterprise Deep Dive

> *"How do you know your LLM output is good?" This is the single hardest question in AI engineering. This document is the answer.*

---

## The Problem with LLM Evaluation

Traditional software has clear right/wrong outputs. LLM outputs are:
- **Open-ended:** Many valid answers exist
- **Non-deterministic:** Same input, different outputs
- **Context-dependent:** "Good" depends on the use case
- **Multi-dimensional:** Correct, but was it also concise? Well-formatted? Appropriately toned?

You cannot evaluate LLMs with `assertEqual`. You need statistical, multi-metric, task-appropriate evaluation frameworks.

---

## The 4 Evaluation Paradigms

Every LLM evaluation falls into one of these categories:

### 1. Reference-Based Evaluation (`reference_based_eval.py`)
Compare LLM output against a known "correct" answer.

**When it works:**
- Translation (source text has a known good translation)
- Structured extraction (known entities to extract)
- Classification (known correct label)
- Fact-based Q&A (single correct answer)

**When it fails:**
- Creative writing (many valid outputs)
- Summarisation (many valid summaries)
- Open-ended generation

**Metrics used:**
- Exact match (very brittle)
- BLEU, ROUGE, METEOR (n-gram overlap — see metrics/)
- BERTScore (semantic similarity)
- Semantic similarity (embedding cosine)

### 2. Reference-Free Evaluation (`reference_free_eval.py`)
Score the output on its own merits without comparing to a "correct" answer.

**When to use:**
- Creative writing
- Open-ended generation
- When no ground truth exists

**Metrics used:**
- Fluency (does it read naturally?)
- Coherence (is it internally consistent?)
- Relevance (does it address the query?)
- Style adherence (matches requested tone?)

Usually scored via LLM-as-judge.

### 3. LLM-as-Judge Evaluation (`llm_as_judge.py`)
Use a strong LLM (GPT-4o, Claude Opus) to grade outputs from a target model.

**Why it works:** LLMs are trained on human preferences. Strong LLMs correlate 80-90% with human judgment on quality assessments. Cheaper and faster than human evaluation.

**Why it's dangerous:**
- Judge bias (LLM prefers verbose, confident-sounding answers)
- Judge blind spots (misses errors the judge itself would make)
- Position bias in pairwise (prefers first or second option)
- Format bias (prefers well-formatted outputs even if wrong)

**Mitigation:**
- Use a different (stronger) model as judge than as generator
- Randomize position in pairwise comparisons
- Use multiple judges and take consensus
- Validate judge quality against human labels on a subset

**Prompt template (production-grade):**
```
You are an impartial evaluator. Score the assistant's response on a scale of 1-10 for [specific criterion].

Instructions:
- Score based ONLY on the specified criterion, not overall quality
- 1 = completely fails, 10 = perfect
- Provide a brief justification (max 20 words)
- Return JSON: {"score": <int>, "reasoning": "<string>"}

Query: {query}
Response: {response}
Criterion: {criterion}
```

### 4. Pairwise Comparison (`pairwise_comparison.py`)
Instead of scoring individual outputs, present two outputs and ask which is better.

**Why it's often better than scoring:**
- Humans (and LLMs) are more reliable at comparison than absolute scoring
- Eliminates score inflation ("everything gets 8/10")
- Directly maps to production decisions ("switch from model A to B?")

**When to use:**
- Model comparison (GPT-4o vs Claude vs Llama fine-tune)
- Version comparison (old prompt vs new prompt)
- A/B test analysis

**The Elo rating approach:**
Run pairwise comparisons at scale, compute Elo ratings for each model/version. This is how LMSYS Chatbot Arena ranks LLMs.

---

## The Enterprise Evaluation Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVALUATION PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. DATASET PREPARATION                                           │
│     • Curated golden examples (100-1000 hand-labeled)            │
│     • Synthetic examples (LLM-generated, human-verified)         │
│     • Production samples (real user queries, anonymized)         │
│     • Adversarial examples (edge cases, red team results)        │
│                                                                   │
│  2. RUN EVALUATION                                                │
│     • Batch run: system processes all eval queries                │
│     • Log: inputs, outputs, retrieved context, tool calls        │
│     • Store: full trace per query (for debugging)                 │
│                                                                   │
│  3. SCORE OUTPUTS                                                 │
│     • Automated metrics (BLEU, BERTScore, embedding similarity)  │
│     • LLM-as-judge for open-ended dimensions                     │
│     • Rule-based checks (does JSON parse? does format match?)    │
│     • Human eval on a subset (calibration + validation)          │
│                                                                   │
│  4. AGGREGATE + ANALYZE                                           │
│     • Overall scores per metric                                   │
│     • Per-category scores (which query types fail most?)         │
│     • Regression analysis (did quality drop from last version?)  │
│     • Distribution analysis (any queries scoring < 0.5?)         │
│                                                                   │
│  5. GATE DECISION                                                 │
│     • Pass: quality meets thresholds, ship it                     │
│     • Fail: quality regression, block deploy, investigate         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Building Evaluation Datasets (`eval_dataset_builder.py`)

**The 80% of eval work nobody talks about.** You can have the best metrics in the world — if your eval dataset doesn't cover real production queries, you're evaluating the wrong thing.

### Dataset Composition (production-grade)

A good eval dataset has 100-1000 examples across these categories:

| Category | % of Dataset | What It Tests |
|---|---|---|
| **Happy path** | 40% | Common, well-formed queries |
| **Edge cases** | 20% | Unusual but valid inputs |
| **Adversarial** | 15% | Prompt injection, jailbreak attempts |
| **Ambiguous** | 10% | Queries with multiple valid interpretations |
| **Out-of-scope** | 10% | Queries the system should refuse |
| **Regression** | 5% | Historical failures that must not recur |

### Dataset Sources

1. **Hand-crafted golden set (start here):** 50-100 carefully labeled examples covering critical use cases. Every prompt engineer should be able to write these.

2. **Synthetic generation:** Use a strong LLM to generate variations of your golden set. Then human-verify. Alpaca-style bootstrapping.

3. **Production sampling:** Sample real user queries (privacy-preserving). Label a subset. This is your ground-truth for "does it actually work in the wild?"

4. **Adversarial mining:** Failed production queries. Red team results. Bug reports.

### Dataset Format

Standard JSONL format:
```json
{
  "id": "eval_001",
  "category": "happy_path",
  "query": "What is RAG?",
  "expected_answer": "RAG stands for Retrieval-Augmented Generation...",
  "expected_facts": ["retrieval", "augmentation", "generation", "external knowledge"],
  "must_not_contain": ["hallucination_marker_1", "banned_phrase_2"],
  "metadata": {
    "difficulty": "easy",
    "domain": "AI",
    "created_by": "human",
    "created_at": "2026-01-15"
  }
}
```

---

## Human Evaluation Pipeline (`human_eval_pipeline.py`)

For high-stakes systems, human evaluation is non-negotiable. LLM-as-judge is a proxy; humans are the ground truth.

### The Human Eval Workflow

1. **Annotation guidelines:** Precise rubrics for what constitutes each score. Ambiguity destroys inter-annotator agreement.

2. **Multiple annotators per example:** 3 minimum for critical evaluations. Compute inter-annotator agreement (Cohen's kappa, Fleiss' kappa).

3. **Golden set validation:** Every annotator scores the same 20 examples. Check for consistency before trusting their scores on new examples.

4. **Blind evaluation:** Annotators don't know which model produced which output (prevents brand bias).

5. **Continuous quality checks:** Insert known-quality examples throughout the eval to catch annotator drift.

### Cost Reality
- Human eval: $2-10 per example (annotator time, review, quality control)
- LLM-as-judge: $0.01 per example
- **Use both:** LLM-as-judge for scale, human eval for calibration and high-stakes decisions.

---

## Common Failure Modes in LLM Evaluation

### 1. Evaluation-Data Leakage
Test queries end up in training data. The model has "seen" the answers. Scores are inflated.

**Prevention:** Keep eval sets private. Never publish golden examples online. Rotate eval sets periodically.

### 2. Overfitting to the Eval Set
Team optimizes prompts/model until eval scores are perfect. Production quality doesn't improve.

**Prevention:** Hold out a "diagnostic" set that's used sparingly. Test on fresh production samples periodically.

### 3. Metric Gaming
"Faithfulness score is high" → team thinks quality is high → deploys → users complain.

**Root cause:** Faithfulness alone doesn't measure usefulness. A vague answer can be perfectly faithful and totally useless.

**Prevention:** Multiple metrics, human eval on subset, production monitoring.

### 4. Score Inflation with Strong Judges
Using GPT-4o as judge: everything scores 8-10. No signal in the scores.

**Prevention:** Anchor the judge with examples of each score (1, 3, 5, 7, 9). Force distribution.

### 5. Ignoring Distribution Shift
Eval dataset from 2024. Production queries in 2026 look different. Eval scores no longer predict production quality.

**Prevention:** Continuously refresh eval datasets from production samples.

---

## Files in This Directory

| File | What It Does |
|---|---|
| `llm_as_judge.py` | LLM-as-judge evaluation framework with anchoring |
| `pairwise_comparison.py` | Pairwise scoring + Elo rating computation |
| `reference_based_eval.py` | BLEU, ROUGE, BERTScore, semantic similarity |
| `reference_free_eval.py` | Fluency, coherence, relevance scoring |
| `human_eval_pipeline.py` | Annotator workflow with quality controls |
| `eval_dataset_builder.py` | Build golden, synthetic, and production-sampled datasets |

---

*Next: [RAG Evaluation →](../rag_evaluation/README.md)*

*Back to [main README](../../README.md)*
