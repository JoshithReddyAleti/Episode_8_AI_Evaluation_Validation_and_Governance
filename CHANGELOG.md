# Changelog
## [1.0.0] — 2026
### Added
- LLM evaluation (4 paradigms): reference-based, reference-free, LLM-as-judge, pairwise
- RAG evaluation (6 metrics): faithfulness, relevance, context precision/recall, correctness, groundedness
- Agent evaluation (6 dimensions): tool selection, task completion, step efficiency, error recovery, trajectory analysis, multi-agent
- Validation pipeline (6 layers): input, schema, Pydantic, coercion, retry, guardrail
- Hallucination detection: 5 types + claim extraction/verification + source attribution
- Bias & safety: fairness metrics, toxicity, stereotypes, safety classifier
- Red teaming: prompt injection, jailbreak, data leakage, adversarial, edge cases
- Metrics library: classification, generation (BLEU/ROUGE/METEOR/BERTScore), embedding, retrieval (MRR/NDCG)
- Testing strategies: deterministic, property-based, snapshot, regression, integration, smoke, contract
- Production monitoring: online eval, drift detection, feedback loops, A/B testing, shadow eval
- Governance: model cards, data documentation, compliance (GDPR/EU AI Act), audit trails, access control
- Framework tool comparison: RAGAS, DeepEval, LangSmith, Phoenix, Promptfoo, Giskard, TruLens
- 11 documentation deep-dives + 12 subsection READMEs
