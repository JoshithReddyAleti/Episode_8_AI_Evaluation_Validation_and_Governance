# Interview Prep — Episode 8

## "How do you evaluate a non-deterministic system?"
> "You can't use assertEqual. Instead: build eval datasets with 100-1000 labeled examples, run the system, score outputs on multiple dimensions (faithfulness, relevance, accuracy, safety), set quality thresholds per metric, and block deploys when scores drop. For open-ended outputs, use LLM-as-judge for scale plus human eval for calibration. Track everything in CI/CD like unit tests."

## "How do you know your RAG system is working?"
> "Six metrics measured together: faithfulness (claims supported by context), answer relevance (addresses the query), context precision (retrieved chunks are relevant), context recall (all needed info retrieved), answer correctness (matches ground truth), and groundedness (claims are citable). Individual metrics can be gamed. Together they give real signal. Threshold: shipping requires faithfulness > 0.85 and no regression from prior version."

## "How do you detect hallucinations?"
> "Three approaches. First, faithfulness scoring — extract atomic claims from the answer, verify each against retrieved context. Second, claim verification — check factual claims against structured knowledge bases or web search. Third, groundedness — require every claim to be citable to a specific source. In production, monitor these continuously; alert when hallucination rate exceeds thresholds."

## "How do you handle bias in an LLM system?"
> "Systematic testing across protected attributes with swap tests (change 'he' to 'she', measure output difference), fairness metrics (demographic parity, equal opportunity), stereotype benchmarks (StereoSet, BBQ), and continuous production monitoring. Document what remains in model cards. This isn't solved — it's managed."

## "How do you deploy a new version safely?"
> "Multi-layer: offline eval must beat baseline (regression check), shadow deploy compares new version to production on real traffic without user impact, A/B test on 10% of traffic with statistical significance testing, gradual rollout with automated rollback on quality degradation. Every step has clear thresholds and gates."

## Resume Bullet
> Engineered enterprise-grade AI evaluation, validation, and governance infrastructure — 11 evaluation dimensions (LLM quality, RAG metrics, agent trajectories, hallucination detection, bias, red teaming), production monitoring with drift detection and A/B testing, compliance documentation (GDPR, EU AI Act), and incident response procedures.
