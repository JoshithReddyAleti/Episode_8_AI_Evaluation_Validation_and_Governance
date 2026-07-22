# ⚖️ Bias, Fairness & Safety — Enterprise Deep Dive

> *"The model was trained on the internet." That's not a joke — it's the entire problem statement for bias detection.*

---

## The Bias Landscape

LLMs learn from training data. Training data reflects human biases. Therefore, LLMs reproduce human biases. Enterprise systems must:
1. **Detect** bias systematically
2. **Measure** it quantitatively
3. **Mitigate** where possible
4. **Document** what remains (in model cards)

---

## Bias Detection (`bias_detection.py`)

### Types of Bias to Test
- **Demographic bias:** Different treatment based on gender, race, age, nationality
- **Occupational bias:** Stereotyping professions ("nurse=woman, doctor=man")
- **Regional bias:** Different quality for different English dialects/languages
- **Political bias:** Systematic leaning in political questions
- **Historical bias:** Reproducing outdated views encoded in training data

### The Bias Test Pattern
```python
# Systematic swap testing
test_pairs = [
    ("The engineer solved the problem. He was...", "The engineer solved the problem. She was..."),
    ("A doctor from India explained...", "A doctor from Germany explained..."),
    # ...
]

for a, b in test_pairs:
    response_a = model(a)
    response_b = model(b)
    # Measure difference in sentiment, professionalism, capability attributions
```

---

## Toxicity Scoring (`toxicity_scoring.py`)

Use dedicated classifiers to score outputs for:
- Harmful content
- Slurs and hate speech
- Threatening language
- Sexual content
- Self-harm content

**Production tools:** Perspective API (Google), Detoxify, Anthropic's Constitutional AI classifiers.

**Production threshold:** Toxicity score < 0.05 for any user-facing output.

---

## Fairness Metrics (`fairness_metrics.py`)

Statistical measures of whether the model treats groups equitably:

### Demographic Parity (`demographic_parity.py`)
Does the model produce similar positive rates across groups?
```
P(positive_outcome | group_A) ≈ P(positive_outcome | group_B)
```

### Equal Opportunity
Among people who deserve a positive outcome, are groups treated equally?
```
P(model_says_yes | qualified, group_A) ≈ P(model_says_yes | qualified, group_B)
```

### Predictive Parity
When the model predicts positive, is precision equal across groups?

**No single metric is "the right" one.** Different fairness definitions can conflict. Enterprise systems document which definition they optimize for and why.

---

## Stereotype Detection (`stereotype_detection.py`)

Uses benchmark datasets like:
- **StereoSet:** Tests stereotypical associations
- **BBQ (Bias Benchmark for QA):** Tests biased assumptions in Q&A
- **BOLD:** Tests biased language generation

Run these against your model. Track scores over time.

---

## Safety Classifier (`safety_classifier.py`)

Real-time classifier for production safety:
- Blocks harmful outputs before reaching users
- Flags borderline outputs for review
- Logs all classifications for audit

**Architecture:**
```
LLM output → Safety Classifier → 
  ├── SAFE → return to user
  ├── FLAGGED → return with warning + log
  └── BLOCKED → return safe fallback + alert
```

---

*Previous: [← Hallucination](../hallucination/README.md) · Next: [Red Teaming →](../red_teaming/README.md)*

*Back to [main README](../../README.md)*
