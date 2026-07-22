# Core Concepts — Episode 8

## 1. AI Testing Is Fundamentally Different
Traditional testing assumes determinism. AI systems are stochastic. Evaluation is testing for non-deterministic systems.

## 2. Multi-Metric or No Metric
Any single metric can be gamed. Faithfulness alone → vague safe answers. Relevance alone → confident hallucinations. Only multiple metrics together give real signal.

## 3. Ground Truth Is Expensive But Necessary
LLM-as-judge scales. Human eval is the ground truth. Enterprise needs both — LLM-as-judge for coverage, human eval for calibration.

## 4. Production Eval Is Different From Development Eval
Development: curated datasets, all metrics. Production: real traffic, proxy metrics, drift detection. Different problems, different solutions.

## 5. Governance Is Engineering
Model cards, audit trails, access control — these are code and process, not just documents. Treat them as infrastructure.

## 6. Evaluation-Driven Development
Evals define what "working" means. Write them before the system. Track them in CI/CD. Block deploys on regressions.
