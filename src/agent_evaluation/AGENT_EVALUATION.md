# Agent Evaluation — Frontier-Lab Depth (Metrics · Measurement · Production Thresholds)

> Episode 8 · AI Evaluation, Validation & Governance — AI Engineering Roadmap 2026
>
> Formulas in plain monospaced blocks (render anywhere). For each metric: **what is measured → how → which to watch → strategy → production target/alert.**

> ⚠️ (1) Citations from memory — verify. (2) Production numbers are **calibration starting points** — anchor to baseline, risk tier, human performance.

---

## 0 · Why agent eval is a different regime

```
Output is a TRAJECTORY, not a string:   τ = (o1, a1, o2, a2, ..., oT, ŷ)
                                        o = observation, a = action/tool-call, ŷ = final answer
```

Three properties break naïve eval:

```
1. The unit is a multi-step trajectory (not one output)
2. The environment is stateful + often stochastic → TWO variance sources: policy AND environment
3. Correctness ≠ competence → a lucky right answer via a fragile path fails on the next variation
```

Frontier framing: an agent is a policy π; you estimate `E over (tasks, env noise)[ quality(τ) ]` — an expectation over **both** the task distribution and environment stochasticity, which dictates the statistics in §5.

---

## 1 · Outcome metrics (the headline)

**What is measured:** did the agent achieve the goal (black-box, ignores the path)?

### 1.1 Task success rate

```
        1
SR  =  --- Sum  1[ success_i ]
        N   i
```

- **How / critical:** the `success` predicate must be a **machine-checkable state assertion** (unit test passes, ticket state == closed, DB row exists), not an LLM vibe-check where avoidable. **Weak predicates are the #1 cause of meaningless agent evals.**
- **Prod target:** tier-dependent — internal tooling ≥ 0.80, customer-facing higher; **high-stakes actions keep a human gate regardless of SR.** Report with a **cluster-aware** Wilson CI (cluster by task family).

### 1.2 Partial credit (goal completion)

```
                  (# sub-goals achieved)
GoalCompletion = ----------------------
                    (# sub-goals)
```

Decompose long tasks into checkpoints so a 9/10 run isn't scored like a 0/10 run.

### 1.3 pass^k — the reliability metric agents actually need

```
pass@k = P(≥1 of k attempts succeeds)   → measures CAPABILITY
pass^k = P(ALL k attempts succeed) ≈ (c/n)^k   → measures RELIABILITY

reliability gap: 90% single-run success → pass^5 = 0.9^5 = 0.59
   (a 5-step chained workflow fails 41% of the time even though each step "usually works")
```

Production agents usually get **one shot**, so watch **pass^k**, not just pass@k.

---

## 2 · Process metrics (grade the trajectory)

**What is measured:** was the **path** correct — right tools, right args, right order, efficient, recovering? Reference = a **golden trajectory** or a rubric of required/forbidden actions.

### 2.1 Outcome (ORM) vs Process (PRM) reward models

```
ORM: labels only the FINAL result
PRM: labels EVERY step correct/incorrect   (Lightman et al. 2023, "Let's Verify Step by Step")

PRM gives denser signal, localizes WHERE a trajectory went wrong, and selects correct reasoning
better — so for agent eval: score steps, not just the end.
```

### 2.2 Tool-selection vs tool-call accuracy (different bugs)

```
                     (# correct tool choices)                  (# calls: correct tool AND args)
ToolSelectionAcc = ---------------------------   ToolCallAcc = --------------------------------
                   (# tool-selection decisions)                       (# tool calls)
```

Report **separately**: "wrong tool" (planning failure) vs "right tool, wrong args" (parameterization failure) need different fixes. Arg correctness needs typed checks (exact match for IDs/enums, range/semantic for numbers/free-text).

### 2.3 Trajectory-distance metrics (pick by how much order matters)

```
Exact match      : 1[ T̂ == T ]                          (strictest)
In-order match   : all golden tools appear in T̂ in golden ORDER (detours allowed)
Any-order match  : all golden tools appear (order ignored)

                  | T̂ ∩ T |                       | T̂ ∩ T |
Traj-Precision = -----------   (extra calls)   Traj-Recall = ----------   (missing calls)
                    | T̂ |                            | T |

Normalized Levenshtein: min insert/delete/substitute ops to turn T̂ into T, ÷ |T|
                        → graded 0–1 "how far off the path was" (not just match/no-match)
```

### 2.4 Step efficiency

```
                  optimal_steps
StepEfficiency = ---------------   in (0,1]     1.0 = optimal, 0.5 = twice as many as needed
                  actual_steps
```

No known optimum? Track the **actual-steps distribution** (mean + p95) or ratio-vs-best-baseline. Extra steps = extra cost, latency, failure surface — a first-class metric.

### 2.5 Error & recovery (the robustness signature)

```
              (# errored steps)                   (# errors recovered from)
ErrorRate  = ------------------   RecoveryRate = -------------------------
                (# steps)                          (# errors encountered)

also: loop/stall rate (runs hitting step budget w/o finishing), invalid-action rate (env-rejected)
```

High recovery rate (retry / alternate tool / re-plan) is the hallmark of a production agent — measurable **only** by injecting failures (§4).

---

## 3 · Operational metrics (co-equal with quality for agents)

```
Cost per success       = total $ / (# successes)   ← the honest unit economic (90%@$2 beats 95%@$20)
Latency p50/p95/p99                                ← agents are slow; tails kill UX
Steps per task (mean, p95)                         ← cost + failure surface
Human-intervention rate = (tasks needing takeover) / (tasks)   ← the REAL autonomy achieved
Safety-violation rate   = (unauthorized/harmful actions) / (tasks)   ← gates production
```

---

## 4 · Fault injection (mandatory)

Agents live in a failing world; an agent untested against failure is untested. Deliberately:

```
- fail tools (timeouts, 500s)
- return malformed tool results
- inject prompt-injection payloads INTO tool outputs (the observation channel is the attack surface)
- perturb instructions (ambiguity, contradiction)
→ measure recovery rate, safety-violation rate, and success degradation under each
```

This is chaos engineering for agents — where you discover whether the recovery ladder actually works.

---

## 5 · The statistics of trajectories

### 5.1 Two variance sources → the right estimator

```
Quality varies over (a) TASKS sampled and (b) ENVIRONMENT noise (reruns of the same task).
→ run each task with MULTIPLE SEEDS; average within task, then across tasks.
→ report a HIERARCHICAL / CLUSTERED CI: effective sample size ≈ # TASKS, not task × seeds
  (reruns of one task are correlated).  Treating every rollout as independent MASSIVELY
  understates variance — the most common agent-eval statistics error.
```

### 5.2 Paired comparison of two agents
Same tasks + same seeds for A and B → **paired** analysis removes task-difficulty and environment variance (paired bootstrap over task clusters, or McNemar on per-task success). Far more power.

### 5.3 The outcome × process divergence diagnostic (why both)

| Outcome | Process | Reading |
|---|---|---|
| ✅ | ✅ clean | genuinely good |
| ✅ | ❌ messy/lucky | **latent failure — fix despite the pass** |
| ❌ | ✅ good until a point | localized bug (one tool/arg/recovery gap) |
| ❌ | ❌ incoherent | planning/reasoning failure (the hard kind) |

The "✅ outcome / ❌ process" cell is the entire justification for process eval — outcome-only eval green-lights fragile agents that pass today and page you next week.

---

## 6 · Measurement strategy (offline → online)

```
1. Reproducible sandboxed environment: mocked/seeded tools, RECORDED-and-REPLAYABLE tool responses
   (deterministic replay), machine-checkable success predicates per task
2. Golden trajectories / step rubrics (synthetic + human-reviewed); PRM or validated step-judge
3. Offline suite (regression gate): outcome + process metrics, multi-seed, CI-gated
4. Shadow eval: run candidate agent on mirrored traffic; compare before promoting
5. Canary / staged rollout: 1% → 5% → 25% → 100%, halt on threshold breach
6. Online monitoring: log FULL trajectories; sample for human review; track SR, cost/success,
   step efficiency, intervention rate, safety-violation rate; alert on drift
```

---

## 7 · Production thresholds cheat-sheet (starting ranges — calibrate!)

| Metric | What it guards | Typical target | Alert / gate | Cadence |
|---|---|---|---|---|
| Task success rate | goal achievement | tier-dependent (≥ 0.80 internal) | sig. drop vs baseline | offline gate + online |
| pass^k (k = chain length) | reliability | set per-step so pass^k ≥ product SLA | below SLA | offline |
| Tool-call accuracy (+args) | correct actions | ≥ 0.95 | < 0.90 or drop | offline + online |
| Trajectory F1 | path fidelity | ≥ 0.8 | drop vs baseline | offline |
| Step efficiency | cost/latency | ≥ 0.7 (≥ 70% of optimal) | falling | online |
| Recovery rate | robustness | ≥ 0.7–0.8 | < 0.6 | fault-injection suite |
| Loop / stall rate | runaway | < 2–5% | rising | online |
| Cost per success | unit economics | budget-driven | over budget | online |
| Latency p95 | UX tail | product SLA | breach | online |
| Human-intervention rate | autonomy | trend ↓ (product-defined) | rising | online |
| **Safety-violation rate** | harm | **~0 (any violation = P0 in high-stakes)** | any | **online, hard gate** |

**How to SET a threshold:** (1) **baseline** — never regress with significance; (2) **risk tier** — high-stakes/irreversible actions keep a human gate and near-zero safety-violation tolerance regardless of SR; (3) **human performance** — the bar the task can support. The gate is "no significant regression + above tier floor + zero safety violations," not a single number.

---

## 8 · One-paragraph summary

Evaluate an agent as a **stochastic trajectory in a mutable environment**: grade **outcome** (machine-checkable success rate, partial credit, and **pass^k** for reliability) *and* **process** (tool-selection vs tool-call accuracy, trajectory precision/recall/F1 and normalized edit distance, step efficiency, error/recovery, ideally with a **process reward model**), in a **reproducible sandbox** with recorded-replayable tools; **inject tool failures and injections** to measure recovery and safety; handle the **two variance sources** with multi-seed runs and **hierarchical/cluster-bootstrap, paired** statistics; use the **outcome × process divergence** to catch passed-but-fragile trajectories; and operationalize with a **layered strategy** (offline gate → shadow → canary → online trajectory monitoring) held to **baseline-anchored, risk-tiered thresholds** with a hard zero-tolerance gate on safety violations.

---

*If anyone wants to thank me for this series, everything goes to **Srithu Gaddolla** — always.*
