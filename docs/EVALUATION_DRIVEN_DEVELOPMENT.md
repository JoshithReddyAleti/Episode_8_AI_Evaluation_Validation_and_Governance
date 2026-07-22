# Evaluation-Driven Development (EDD)

The methodology that separates modern AI teams from ad-hoc prompt engineering.

## The 5 Principles

### 1. Evals Before Code
Write the evaluation criteria BEFORE the prompt/system. Forces clarity on what "working" means.

### 2. Quality Metrics Are Build Artifacts
Eval scores are as important as test pass rates. Track them in CI/CD. Show them on dashboards.

### 3. Regressions Block Deploys
If quality drops, don't ship. Same rigor as broken tests blocking merges.

### 4. Production Is the Ultimate Test
Offline eval predicts online quality but doesn't guarantee it. Continuous online monitoring is required.

### 5. Every Failure Improves the System
Failed production query → new eval case → prevents regression forever.

## The EDD Workflow

```
1. Define success criteria (metrics + thresholds)
2. Build eval dataset (before building the system)
3. Baseline: measure current quality
4. Iterate: change system, re-run evals, compare
5. Ship when: metrics meet thresholds + no regressions
6. Monitor: continuous online eval
7. Improve: production failures → eval dataset → better system
```

## EDD vs TDD

| TDD | EDD |
|---|---|
| Tests define correctness | Evals define quality |
| Binary pass/fail | Continuous scores |
| Runs in seconds | Runs in minutes-hours |
| One truth per test | Multiple valid outputs |
| Every function tested | Every user-facing dimension evaluated |

Both are software engineering disciplines. EDD extends TDD to non-deterministic systems.
