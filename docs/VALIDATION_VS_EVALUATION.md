# Validation vs Evaluation — The Critical Distinction

Most engineers confuse these. They're fundamentally different.

## Validation
- **Question:** Does the output match the expected structure?
- **Answer:** Binary (yes/no) per output
- **When:** Every request in production
- **Speed:** Milliseconds
- **Tools:** Pydantic, JSON Schema, regex
- **Failure mode:** System error (throw, retry, fallback)
- **Example:** "Is this response valid JSON with all required fields?"

## Evaluation
- **Question:** Is the output good?
- **Answer:** Continuous score across multiple dimensions
- **When:** Sampled from production, full runs on eval datasets
- **Speed:** Seconds to minutes per query
- **Tools:** RAGAS, DeepEval, LLM-as-judge, human eval
- **Failure mode:** Quality issue (alert, investigate, retrain)
- **Example:** "How faithful is this response to the retrieved context, and how well does it address the query?"

## Both Are Non-Negotiable
- Validation catches structural failures (fast, deterministic)
- Evaluation catches quality issues (slow, statistical)
- Neither replaces the other
