# Decision Framework — Which Evaluation for Which Situation

## What are you building?

### Simple LLM prompt
→ LLM eval (llm_as_judge), basic validation, reference-based tests

### RAG system
→ RAG eval (all 6 metrics), retrieval quality metrics, faithfulness > 0.85

### AI agent
→ Agent eval (tool selection, trajectory), hallucination detection, safety classifier

### Multi-agent system
→ Multi-agent eval, coordination metrics, per-agent quality, bottleneck detection

### High-stakes domain (medical, legal, financial)
→ ALL of the above + red teaming + bias audits + governance framework + human oversight

## What phase are you in?

### Development
→ Offline eval, unit tests, snapshot tests, iterate

### Pre-launch
→ Full eval suite, red teaming, bias audit, human eval on sample, compliance review

### Post-launch
→ Online monitoring, drift detection, A/B tests, feedback loops, quarterly reviews

## What tools?

- **Just starting?** RAGAS + Pydantic
- **LangChain stack?** + LangSmith
- **RAG-heavy?** + Phoenix
- **Bias/compliance-critical?** + Giskard
- **Everything?** RAGAS + LangSmith + Giskard + Phoenix + custom
