# 📡 Production Monitoring — Watching AI in the Wild

> *Offline evaluation tells you if it worked yesterday. Production monitoring tells you if it's working right now.*

---

## Why Production Monitoring Is Different

Pre-production evaluation tests on known data. Production monitoring must:
- Detect issues **without ground truth** (users don't label their queries)
- Alert **in real-time** (not weekly reports)
- Handle **millions of queries** (not thousands of test cases)
- Balance **cost vs coverage** (can't evaluate every query)

---

## The 7 Production Monitoring Components

### 1. Online Evaluation (`online_evaluation.py`)

Continuous evaluation on a sample of production traffic.

**Sampling strategy:**
- 100% of high-value queries (paying customers, critical endpoints)
- 5-10% of medium traffic
- 1% of low-value traffic

**Metrics tracked:**
- All offline metrics (faithfulness, relevance, latency, cost)
- But scored on real production queries, not test data

**Feedback loop:** Failed queries → add to next eval dataset → improve offline testing

### 2. Drift Detection (`drift_detection.py`)

Detects when input distribution or output quality shifts:

**Input drift:**
- New topics appearing in queries
- Language/format changes
- User behavior shifts

**Output drift:**
- Response length trends
- Quality score trends
- Error rate trends

**Detection methods:**
- Statistical tests (KL divergence, PSI - Population Stability Index)
- Embedding-based (average embedding of queries this week vs last month)
- LLM-based (classify query types, track distribution)

**Response:**
- Alert when drift exceeds threshold
- Investigate root cause (new user segment? attack? competitor influence?)
- Retrain / update evaluation data / adjust system

### 3. Feedback Loops (`feedback_loops.py`)

Capture user signals for continuous improvement:

**Explicit signals:**
- Thumbs up/down
- Star ratings
- Written feedback
- Report-inaccuracy flags

**Implicit signals:**
- Session length (short = engaged, very short = failed)
- Retry patterns (user rephrasing = system misunderstood)
- Copy/paste behavior (user copying answer = success signal)
- Abandonment (user leaves mid-conversation)

**Enterprise pipeline:**
```
User signal → labeled example → next eval dataset → improved system
```

### 4. Alert Thresholds (`alert_thresholds.py`)

Automated alerts on quality issues:

```python
ALERTS = {
    "critical": {
        "error_rate > 5%": page_oncall,
        "p99_latency > 30s": page_oncall,
        "toxicity_rate > 0.1%": page_oncall,
    },
    "warning": {
        "faithfulness < 0.80": alert_slack,
        "user_thumbs_down > 15%": alert_slack,
        "cost_per_query > baseline * 1.5": alert_slack,
    },
    "info": {
        "new_query_pattern": log_only,
        "response_length_shift": log_only,
    }
}
```

### 5. A/B Testing (`ab_testing.py`)

Statistically compare two versions on real traffic:

```
Traffic split: 50% → version A, 50% → version B
Metrics: quality, latency, cost, user satisfaction

Statistical significance:
  - Sample size calculation upfront
  - p-value < 0.05 for shipping decision
  - Confidence intervals reported
  - Multiple comparison correction if testing multiple metrics
```

**Enterprise best practices:**
- Predefined success metrics (don't cherry-pick)
- Fixed test duration (avoid peeking bias)
- Guardrail metrics (some metrics can NOT get worse)
- Stratified analysis (does version B help/hurt specific user segments?)

### 6. Shadow Evaluation (`shadow_evaluation.py`)

Run a new version in parallel with production WITHOUT serving its outputs:

```
User query → 
  ├── Production version (returned to user)
  └── Shadow version (logged, evaluated, but not shown)

Compare outputs offline. Detect issues before affecting users.
```

**Perfect for:**
- Testing new prompts
- Evaluating new models
- Detecting regressions before A/B testing

**Cost:** 2x LLM calls, but zero user risk.

### 7. Dashboard Metrics (`dashboard_metrics.py`)

Real-time dashboards showing:

**Health metrics (updated every minute):**
- Requests/sec, error rate, p99 latency

**Quality metrics (updated every hour):**
- Average scores across recent traffic
- Failed query rate
- User satisfaction

**Cost metrics (updated daily):**
- Token usage
- LLM API costs
- Per-user, per-endpoint breakdowns

**Trend metrics (updated weekly):**
- Quality over time
- User engagement trends
- Distribution shifts

---

## The Production Monitoring Stack

```
┌─────────────────────────────────────────────────┐
│  Application                                      │
│  ├── Emits: traces, metrics, logs                │
│  └── Receives: alerts, feedback signals          │
├─────────────────────────────────────────────────┤
│  Observability Layer                              │
│  ├── LangSmith / Langfuse (LLM-specific traces)  │
│  ├── OpenTelemetry (distributed tracing)         │
│  ├── Prometheus (metrics)                         │
│  └── Datadog / Grafana (dashboards, alerts)      │
├─────────────────────────────────────────────────┤
│  Analytics Layer                                  │
│  ├── Drift detection                              │
│  ├── A/B test analysis                            │
│  ├── Cost analysis                                │
│  └── Quality trend analysis                       │
├─────────────────────────────────────────────────┤
│  Alerting                                         │
│  ├── PagerDuty (critical alerts)                  │
│  ├── Slack (warnings)                             │
│  └── Email (daily/weekly reports)                 │
└─────────────────────────────────────────────────┘
```

---

*Previous: [← Testing Strategies](../testing_strategies/README.md) · Next: [Governance →](../governance/README.md)*

*Back to [main README](../../README.md)*
