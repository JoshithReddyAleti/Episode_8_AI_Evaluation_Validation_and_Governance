# 📖 Metrics Glossary — Every Metric Defined Precisely

## Classification Metrics
- **Accuracy:** correct predictions / total predictions
- **Precision:** true positives / (true positives + false positives)
- **Recall (Sensitivity):** true positives / (true positives + false negatives)
- **F1:** 2 × (precision × recall) / (precision + recall)
- **F-beta:** weighted F-score, β=2 weights recall more
- **ROC-AUC:** area under ROC curve, threshold-independent
- **PR-AUC:** area under precision-recall curve, better for imbalanced data
- **Cohen's Kappa:** agreement between two annotators, corrected for chance

## Generation Metrics
- **BLEU:** n-gram precision with brevity penalty (translation)
- **ROUGE:** n-gram recall (summarization)
- **METEOR:** BLEU + synonyms + stemming
- **CHRF:** character n-gram F-score
- **BERTScore:** BERT embedding similarity (semantic)
- **MoverScore:** Earth Mover's Distance on embeddings

## Retrieval Metrics
- **Precision@k:** relevant results in top-k / k
- **Recall@k:** relevant results in top-k / all relevant
- **MRR:** Mean Reciprocal Rank — 1/rank_of_first_relevant, averaged
- **NDCG:** Normalized Discounted Cumulative Gain — rewards relevant results higher in ranking
- **Hit Rate:** at least one relevant result in top-k (binary)
- **MAP:** Mean Average Precision

## RAG-Specific Metrics
- **Faithfulness:** claims supported by context / total claims
- **Answer Relevance:** how well answer addresses query
- **Context Precision:** retrieved chunks that are relevant / total retrieved
- **Context Recall:** required info retrieved / total required
- **Answer Correctness:** factual correctness against ground truth
- **Groundedness:** claims traceable to specific sources

## Agent Metrics
- **Tool Selection Accuracy:** correct tool choices / total decisions
- **Task Completion Rate:** successful task completions / attempts
- **Step Efficiency:** min_required_steps / actual_steps
- **Error Recovery Rate:** successful recoveries / injected failures

## Operational Metrics
- **Latency p50/p95/p99:** percentile response times
- **Throughput:** requests per second
- **Error Rate:** failed requests / total requests
- **Cost per Query:** total cost / query count

## Fairness Metrics
- **Demographic Parity:** P(positive|group_A) ≈ P(positive|group_B)
- **Equal Opportunity:** equal TPR across groups
- **Predictive Parity:** equal precision across groups
- **Calibration:** predicted probabilities match observed frequencies

## Drift Metrics
- **KL Divergence:** measure of distribution difference
- **PSI (Population Stability Index):** detects distribution shifts
- **Wasserstein Distance:** Earth Mover's Distance between distributions
