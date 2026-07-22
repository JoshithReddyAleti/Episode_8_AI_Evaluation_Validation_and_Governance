# Offline vs Online Evaluation

## Offline Evaluation
- **Where:** Before deployment
- **Data:** Curated eval datasets
- **Ground truth:** Available (you labeled it)
- **Metrics:** Full metric suite (faithfulness, relevance, correctness, ...)
- **Purpose:** Release gate — should we ship this version?
- **Frequency:** Every commit / PR / release
- **Sample size:** 100-10,000 examples

## Online Evaluation
- **Where:** In production
- **Data:** Real user queries
- **Ground truth:** Rarely available
- **Metrics:** Proxy metrics (user feedback, quality classifiers, distribution stats)
- **Purpose:** Continuous monitoring — is quality maintained?
- **Frequency:** Continuous (streaming)
- **Sample size:** Sampled % of production traffic

## The Feedback Loop
```
Offline eval → Deploy → Online monitoring → 
  Failed queries → New eval dataset → Better offline eval
```

## Enterprise Requirement
You need BOTH. Offline alone: fails on real-world distribution. Online alone: no release gate, ships bad versions.
