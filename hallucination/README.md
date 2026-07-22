# 🌀 Hallucination Detection — Enterprise Deep Dive

> *Hallucination is not a bug — it's a fundamental property of how LLMs work. Detection isn't about elimination; it's about measurement and mitigation.*

---

## The Types of Hallucination (`hallucination_types.py`)

Not all hallucinations are the same. Enterprise systems must categorize them:

### 1. Factual Hallucination
Model states false facts. "The Eiffel Tower is in London."

### 2. Attribution Hallucination
Correct fact, wrong source. "According to Einstein: E=mc²... published in 1955." (Einstein published it in 1905.)

### 3. Contextual Hallucination
Adding information not in the provided context.
Context: "The API returns JSON."
Answer: "The API returns JSON in a specific schema with 5 fields." (fields weren't in context)

### 4. Reasoning Hallucination
Correct facts, incorrect reasoning connecting them.
"All humans are mortal. Socrates is mortal. Therefore, Socrates is human." (invalid syllogism)

### 5. Instruction Hallucination
Model claims to have done something it didn't.
User: "Search for X and summarize."
Model: "I searched and found..." (but no search happened)

---

## Detection Approaches

### 1. Factual Consistency Check (`factual_consistency_check.py`)
For RAG systems — is the output supported by retrieved context?

```
Extract claims from output → for each claim, check if any chunk supports it → score
```

### 2. Claim Extraction + Verification (`claim_extraction.py`, `claim_verification.py`)
Two-stage process:
1. **Extract:** LLM extracts atomic claims from the answer
2. **Verify:** For each claim, verify against:
   - Retrieved context (for RAG)
   - Knowledge base (for structured facts)
   - Web search (for current events)

### 3. Source Attribution (`source_attribution.py`)
For every claim, produce a citation:
```json
{
  "claim": "The Transformer was introduced in 2017",
  "source": "chunk_42",
  "source_text": "In 2017, Vaswani et al. introduced...",
  "confidence": 0.95
}
```

Enterprise-critical: regulated industries require every claim to be citable.

### 4. Hallucination Scorer (`hallucination_scorer.py`)
Composite score combining all approaches:
```
hallucination_score = weighted_avg(
    unfaithful_claims_ratio,
    unverified_facts_ratio,
    reasoning_errors_ratio,
    instruction_mismatches
)
```

---

## Production Mitigation Patterns

1. **CRAG (Corrective RAG)** — Verify retrieved chunks before generation (Episode 5)
2. **Self-consistency** — Generate multiple answers, check for agreement (Episode 6)
3. **Retrieval grounding requirement** — Refuse to answer if retrieval confidence is low
4. **Constrained generation** — Force outputs to cite specific chunks
5. **Human-in-the-loop** — Route uncertain outputs to human review

---

*Previous: [← Validation](../validation/README.md) · Next: [Bias & Safety →](../bias_and_safety/README.md)*

*Back to [main README](../../README.md)*
