# 📊 Evaluation Taxonomy — The Complete Classification

## The Two Fundamental Dimensions

### Dimension 1: WHERE the evaluation runs
- **Offline:** Before deployment, on curated datasets
- **Online:** In production, on real traffic
- **Shadow:** In production, without user impact

### Dimension 2: WHAT the evaluation measures
- **Quality:** Is the output good? (faithfulness, relevance, accuracy)
- **Structure:** Does it match schema? (validation)
- **Safety:** Is it harmful? (toxicity, bias, jailbreak resistance)
- **Performance:** Is it fast and cheap? (latency, cost, throughput)

## The Complete Grid

| | Quality | Structure | Safety | Performance |
|---|---|---|---|---|
| **Offline** | RAGAS, DeepEval | Pydantic validation | Red teaming, bias audits | Load testing |
| **Online** | Feedback loops, A/B tests | Runtime validation | Safety classifiers | APM monitoring |
| **Shadow** | Compare new vs old | Schema drift detection | Silent safety testing | Latency profiling |

Every production AI system needs coverage across all 12 cells.
