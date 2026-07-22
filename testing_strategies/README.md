# 🧪 Testing Strategies — Non-Deterministic Systems in CI/CD

> *The hardest engineering problem in AI: making CI/CD work when outputs aren't deterministic.*

---

## The Core Problem

Traditional CI/CD tests fail on this:
```python
def test_summarize():
    result = summarize("Long article...")
    assert result == "Expected summary text"  # ← Will fail on every run
```

Same input, different outputs. Non-determinism breaks the fundamental assumption of test frameworks.

**The solution:** Different test paradigms for different test purposes.

---

## The 7 Testing Paradigms

### 1. Deterministic Tests (`deterministic_tests.py`)

Tests that don't involve LLM outputs. Test the surrounding infrastructure:
- Input parsing
- Output schema validation
- Tool execution logic
- State management
- Error handling paths

Use standard pytest. `temperature=0` for LLM calls doesn't guarantee determinism — but it minimizes variance.

### 2. Property-Based Tests (`property_based_tests.py`)

Instead of "output equals X", test properties that should ALWAYS hold:

```python
def test_summary_properties():
    for article in test_articles:
        summary = summarize(article)
        # Property 1: Summary is shorter than original
        assert len(summary) < len(article)
        # Property 2: Summary is not empty
        assert len(summary.strip()) > 0
        # Property 3: Summary contains no forbidden phrases
        assert not any(phrase in summary for phrase in FORBIDDEN_PHRASES)
        # Property 4: Summary is valid English (readability score check)
        assert readability_score(summary) > 30
```

Properties are much more resilient than exact matches.

### 3. Snapshot Tests (`snapshot_tests.py`)

Record outputs from a known-good version. Compare future outputs against those snapshots.

**Not exact comparison** — semantic comparison via embedding similarity:
```python
def test_snapshot_matches():
    current_output = model.generate("Query")
    saved_snapshot = load_snapshot("query_response")
    similarity = cosine_sim(embed(current_output), embed(saved_snapshot))
    assert similarity > 0.85  # Semantic match
```

**When outputs drift:** Update snapshots deliberately, review carefully, commit as intentional change.

### 4. Regression Tests (`regression_tests.py`)

Ensure quality doesn't regress between versions.

```python
def test_no_quality_regression():
    current_metrics = run_full_eval(current_version)
    prev_metrics = load_previous_metrics()
    for metric_name, current_value in current_metrics.items():
        prev_value = prev_metrics[metric_name]
        # Allow 2% degradation (accounts for noise)
        assert current_value >= prev_value - 0.02, f"{metric_name} regressed"
```

The most important test suite for production AI.

### 5. Integration Tests (`integration_tests.py`)

Test full pipelines end-to-end with mocked or real dependencies:
- Full RAG pipeline (loader → chunker → retriever → generator)
- Multi-agent workflows
- External API integrations
- Database operations

### 6. Smoke Tests (`smoke_tests.py`)

Minimal tests that verify the system is functional at all. Run on every deploy:
- Health check endpoint responds
- Sample query returns 200
- Model can be loaded
- Vector store is accessible

If smoke tests fail, don't deploy. If they succeed, more thorough tests can run in staging.

### 7. Contract Tests (`contract_tests.py`)

Verify that upstream and downstream systems maintain their contracts:
- LLM API returns expected schema
- Vector store honors similarity thresholds
- Downstream consumers accept your output format

Critical when systems interact — a schema change upstream can silently break your pipeline.

---

## Testing Non-Deterministic Systems (`testing_nondeterministic_systems.md`)

**Key strategies:**

1. **Statistical assertions:** Run N times, assert p% pass
   ```python
   scores = [eval_run() for _ in range(20)]
   assert sum(s > 0.7 for s in scores) / 20 > 0.9  # 90% pass rate
   ```

2. **Threshold-based:** Assert scores exceed thresholds
   ```python
   assert faithfulness_score > 0.85
   ```

3. **Multi-metric:** Any single metric can noise; require ALL metrics to hold
   ```python
   assert all(m > threshold for m, threshold in checks)
   ```

4. **Temperature=0 for regression:** Minimizes noise for regression checks

5. **Fixed random seeds:** For sampling operations, fix seeds

6. **Batching:** Amortize LLM cost by batching evaluation runs

---

## CI/CD Integration Pattern

```yaml
# .github/workflows/ai-tests.yml
on: [pull_request, push]

jobs:
  fast-tests:
    # < 1 minute
    - deterministic tests
    - unit tests
    - smoke tests

  medium-tests:
    # 5-10 minutes
    - integration tests
    - property-based tests
    - snapshot tests

  slow-tests:
    # 30+ minutes, run on merge to main
    - full eval suite
    - regression tests against baseline
    - bias audit
    - security tests

  block-deploy-on-regression:
    if: regression_detected
    - block deployment
    - alert team
```

---

*Previous: [← Metrics](../metrics/README.md) · Next: [Production Monitoring →](../production_monitoring/README.md)*

*Back to [main README](../../README.md)*
