# Agent Evaluation — Frontier-Lab Depth

> Episode 8 · AI Evaluation, Validation & Governance — AI Engineering Roadmap 2026
>
> Agents are the hardest thing to evaluate because the unit is a **stochastic multi-step trajectory in a mutable environment**, and a correct answer via a wrong/lucky/unsafe path is a latent failure. This file covers outcome vs process reward modeling, exact trajectory-distance and reliability estimators (pass@k vs **pass^k**), the environment-variance problem and its statistical treatment, and the frontier measurement protocol.

> ⚠️ **Citations** from memory; agent benchmarks/frameworks evolve fast — verify before publishing.

---

## 0 · Why agent eval is a different regime

Three properties break naïve eval:

1. **The output is a trajectory**, not a string: $\tau=(o_1,a_1,o_2,a_2,\dots,o_T,\hat y)$ — observations, actions (tool calls), final answer.
2. **The environment is stateful and often stochastic** — the same policy on the same task can produce different trajectories (tool nondeterminism, seed, timing). Your metric now has **two variance sources**: policy and environment.
3. **Correctness ≠ competence:** a lucky right answer via a fragile path will fail on the next variation. So you must grade the **process**, not just the outcome.

Frontier framing: an agent is a policy $\pi$; you're estimating $\mathbb E_{\text{task}\sim D,\ \text{env noise}}[\text{quality}(\tau)]$ — an expectation over *both* the task distribution and environment stochasticity, which dictates the statistics in §5.

---

## 1 · Outcome reward — the headline, done right

### 1.1 Task success rate
$$
\text{SR}=\frac1N\sum_{i=1}^N \mathbb 1[\text{success}_i]
$$
The **success predicate must be a machine-checkable state assertion** (unit test passes, ticket state == closed, DB row exists), *not* an LLM vibe-check where avoidable. Weak predicates are the #1 cause of meaningless agent evals. Report with a **cluster-aware** Wilson CI (cluster by task family — §5).

### 1.2 Partial credit
$$
\text{GoalCompletion}=\frac{|\text{sub-goals achieved}|}{|\text{sub-goals}|}
$$
Binary SR is too brutal for long tasks; decompose into checkpoints so a 9/10 run isn't scored identically to a 0/10 run.

### 1.3 Reliability: pass^k (the metric agents actually need)
pass@k (≥1 of $k$ succeeds) measures *capability*. Agents in production usually get **one** shot, so what matters is **consistency**:
$$
\text{pass}^k=\Pr[\text{all }k\text{ independent attempts succeed}]\approx\Big(\tfrac{c}{n}\Big)^k
$$
The gap between pass@k (optimistic) and pass^k (pessimistic) is the **reliability gap** — an agent with 90% single-run success has $0.9^5\approx 0.59$ pass^5: it will fail a 5-step chained workflow 41% of the time even though each step "usually works." Frontier evals report both.

---

## 2 · Process reward — grade the trajectory

Reference = a **golden trajectory** (ideal tool sequence) or a **rubric** of required/forbidden actions. Let agent tool calls $\hat T=(\hat t_1,\dots,\hat t_m)$ vs golden $T=(t_1,\dots,t_n)$.

### 2.1 Outcome (ORM) vs Process (PRM) reward models
From "Let's Verify Step by Step" (Lightman et al., 2023): an **ORM** labels only the final result; a **PRM** labels **every step** correct/incorrect. PRMs give denser signal, localize *where* a trajectory went wrong, and are markedly better at selecting correct reasoning — the basis of step-level verification. For agent eval this means: score steps, not just the end, so you can attribute failure to a specific action.

### 2.2 Tool-selection vs tool-call accuracy (different bugs)
$$
\text{ToolSelectionAcc}=\frac{|\text{correct tool choices}|}{|\text{tool-selection decisions}|},\quad
\text{ToolCallAcc}=\frac{|\text{correct tool AND args}|}{|\text{tool calls}|}
$$
Report separately: "wrong tool" (planning failure) and "right tool, wrong args" (grounding/parameterization failure) demand different fixes. Argument correctness needs typed checks — exact match for IDs/enums, range/semantic checks for numbers/free-text.

### 2.3 Trajectory-distance metrics (choose by how much order matters)
- **Exact match:** $\mathbb 1[\hat T=T]$ — strictest.
- **In-order match:** all golden tools appear in $\hat T$ in golden order (detours allowed).
- **Any-order match:** all golden tools appear (order ignored).
- **Set precision/recall/F1:**
$$
\text{TrajP}=\frac{|\hat T\cap T|}{|\hat T|}\ (\text{penalizes extra calls}),\quad
\text{TrajR}=\frac{|\hat T\cap T|}{|T|}\ (\text{penalizes missing calls})
$$
- **Normalized Levenshtein on the tool sequence:** min insert/delete/substitute ops to turn $\hat T$ into $T$, ÷ $|T|$ → a graded 0–1 divergence capturing *how far off* the path was, not just match/no-match.

### 2.4 Step efficiency
$$
\text{StepEfficiency}=\frac{\text{optimal\_steps}}{\text{actual\_steps}}\in(0,1]
$$
1.0 = optimal; 0.5 = twice as many steps as needed. No known optimum? Track the **actual-steps distribution** (mean + p95) or ratio-vs-best-baseline. Extra steps = extra cost, latency, and failure surface, so this is a first-class metric, not a footnote.

### 2.5 Error & recovery (the robustness signature)
$$
\text{ErrorRate}=\frac{|\text{errored steps}|}{|\text{steps}|},\qquad
\text{RecoveryRate}=\frac{|\text{errors recovered}|}{|\text{errors encountered}|}
$$
Also: **loop/stall rate** (runs hitting the step budget without finishing) and **invalid-action rate** (env-rejected calls). High recovery rate — retry, alternate tool, re-plan — is the hallmark of a production-grade agent, and you can *only* measure it by injecting failures (§4).

---

## 3 · Operational metrics (co-equal with quality for agents)

| Metric | Definition | Why it's first-class |
|---|---|---|
| **Cost per success** | total \$ ÷ #successes | the honest unit economic: 90%@\$2 beats 95%@\$20 |
| **Latency p50/p95/p99** | wall-clock per task | agents are slow; tails kill UX |
| **Steps per task** | mean & p95 trajectory length | cost + failure surface |
| **Human-intervention rate** | tasks needing takeover ÷ tasks | the *real* autonomy achieved |
| **Safety-violation rate** | unauthorized/harmful actions ÷ tasks | gates production |

---

## 4 · Fault injection — mandatory for agents

Agents live in a failing world; an agent untested against failure is untested. Deliberately: **fail tools** (timeouts, 500s), **return malformed results**, **inject prompt-injection payloads into tool outputs** (the observation channel is the attack surface), and **perturb instructions** (ambiguity, contradiction). Measure recovery rate, safety-violation rate, and success degradation under each. This is chaos engineering for agents and it's where you discover whether the recovery ladder actually works.

---

## 5 · The statistics of trajectories (the part labs get right)

### 5.1 Two variance sources → the right estimator
Quality varies over **tasks** (which items you sampled) and **environment noise** (reruns of the same task). To estimate policy quality:
- Run each task **multiple seeds**; average within task, then across tasks.
- Report a **hierarchical/clustered** CI: the effective sample size is closer to the number of *tasks*, not task×seeds, because reruns of one task are correlated. Ignoring this (treating every rollout as independent) massively **understates variance** — the most common agent-eval statistics error.

### 5.2 Paired comparison of two agents
Same tasks + same seeds for A and B → **paired** analysis removes task-difficulty and environment variance; use paired bootstrap over tasks (resample task clusters) or McNemar on per-task success. Enormously more power than unpaired.

### 5.3 The outcome×process divergence diagnostic (why both)
| Outcome | Process | Reading |
|---|---|---|
| ✅ | ✅ clean | genuinely good |
| ✅ | ❌ messy/lucky | **latent failure** — fix despite the pass |
| ❌ | ✅ good until a point | localized bug (one tool/arg/recovery gap) |
| ❌ | ❌ incoherent | planning/reasoning failure (the hard kind) |
The "✅ outcome / ❌ process" cell is the entire justification for process eval — outcome-only eval green-lights fragile agents that pass today and page you next week.

---

## 6 · The frontier protocol

1. **Reproducible sandboxed environment**: mocked/seeded tools, **recorded-and-replayable** tool responses (deterministic replay), machine-checkable success predicates per task.
2. **Golden trajectories / step rubrics** (synthetic + human-reviewed) for process scoring; a **PRM** or validated step-judge for step-level labels.
3. **Run multi-seed**; compute **outcome** (SR, partial credit, **pass^k**) and **process** (tool-selection/call accuracy, trajectory P/R/F1, Levenshtein, step efficiency, error/recovery) metrics.
4. **Inject faults** (tool failures, injections, ambiguity); measure recovery + safety degradation.
5. **Statistics:** hierarchical/**cluster-bootstrap** CIs (cluster by task), **paired** A-vs-B, power-sized to the smallest SR delta you need.
6. **Diagnose via outcome×process divergence**; attribute every failure to a stage/action.
7. **Production:** log full trajectories, sample for human review, monitor SR, cost-per-success, step efficiency, intervention rate, safety-violation rate for drift.

---

## 7 · Quick-reference

| Metric | Type | Answers |
|---|---|---|
| Task success rate | outcome | "did it achieve the goal?" |
| pass^k | outcome/reliability | "does it succeed *every* time?" |
| Goal completion | outcome | "how much of a multi-goal task?" |
| Tool selection / call accuracy | process | "right tool / right args?" |
| Trajectory P/R/F1, Levenshtein | process | "how close to the ideal path?" |
| Step efficiency | process | "as few steps as needed?" |
| Error / recovery rate | process | "fails — and recovers?" |
| Cost per success | operational | "unit economics" |
| Human-intervention rate | operational | "real autonomy" |
| Safety-violation rate | safety | "unauthorized actions?" |

---

## 8 · One-paragraph summary

Evaluate an agent as a **stochastic trajectory in a mutable environment**: grade **outcome** (machine-checkable success rate, partial credit, and — critically — **pass^k** for reliability, not just pass@k for capability) *and* **process** (tool-selection vs tool-call accuracy, trajectory precision/recall/F1 and normalized edit distance, step efficiency, error/recovery rate, ideally with a **process reward model** giving step-level labels), in a **reproducible sandbox** with recorded-replayable tools; **inject tool failures and injections** to measure recovery and safety; handle the **two variance sources** (task + environment) with multi-seed runs and **hierarchical/cluster-bootstrap, paired** statistics that don't fake precision; and use the **outcome×process divergence** to catch the latent failures — passed-but-fragile trajectories — that outcome-only eval ships to production.

---

*If anyone wants to thank me for this series, everything goes to **Srithu Gaddolla** — always.*
