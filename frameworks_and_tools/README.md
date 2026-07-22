# 🛠️ Evaluation Frameworks & Tools — The Honest Comparison

## The Tools

### RAGAS (`ragas_guide.py`)
- **Best for:** RAG-specific evaluation
- **Metrics:** Faithfulness, answer relevance, context precision/recall, answer correctness
- **Strength:** Purpose-built for RAG, well-documented
- **Weakness:** RAG-only (not general LLM eval)
- **Cost:** Free, uses your LLM API

### DeepEval (`deepeval_guide.py`)
- **Best for:** General LLM evaluation, pytest integration
- **Metrics:** 14+ including hallucination, bias, toxicity, coherence, custom
- **Strength:** Broad metric coverage, testing framework feel
- **Weakness:** Younger project than RAGAS
- **Cost:** Free, uses your LLM API

### LangSmith (`langsmith_eval.py`)
- **Best for:** LangChain-heavy stacks, production tracing + eval
- **Metrics:** Custom evaluators, LLM-as-judge, standard NLP metrics
- **Strength:** Production observability + eval in one platform
- **Weakness:** Best for LangChain users, subscription for production
- **Cost:** Free tier, paid for production usage

### Phoenix / Arize (`phoenix_arize_eval.py`)
- **Best for:** RAG debugging, embedding visualization
- **Metrics:** Retrieval metrics, drift detection, embedding analysis
- **Strength:** Best-in-class RAG debugging UI
- **Weakness:** More focused on retrieval than generation
- **Cost:** Free (Phoenix open source), paid for Arize platform

### Promptfoo (`promptfoo_guide.py`)
- **Best for:** Prompt engineering testing, model comparison
- **Metrics:** Configurable via YAML
- **Strength:** Great CLI, great for prompt A/B tests
- **Weakness:** Less integrated than LangSmith
- **Cost:** Free

### Giskard (`giskard_guide.py`)
- **Best for:** Bias, fairness, robustness testing
- **Metrics:** Bias detection, adversarial testing, LLM red teaming
- **Strength:** Regulatory compliance features, bias detection
- **Weakness:** Requires more setup
- **Cost:** Free open source, paid Enterprise

### TruLens (`trulens_guide.py`)
- **Best for:** Feedback function-based evaluation
- **Metrics:** Groundedness, relevance, custom feedback functions
- **Strength:** Novel approach to eval, good for research
- **Weakness:** Smaller community than RAGAS
- **Cost:** Free

## Decision Matrix (`comparison_matrix.md`)

| Need | Best Tool |
|---|---|
| RAG evaluation | RAGAS |
| General LLM eval + testing | DeepEval |
| LangChain stack | LangSmith |
| RAG debugging | Phoenix |
| Prompt A/B testing | Promptfoo |
| Bias & compliance | Giskard |
| Novel research | TruLens |

## Enterprise Recommendation
Most enterprises end up using 2-3 tools:
1. **RAGAS or DeepEval** for offline evaluation
2. **LangSmith or Phoenix** for production observability
3. **Giskard** for bias and compliance testing

---

*Previous: [← Governance](../governance/README.md)*

*Back to [main README](../../README.md)*
