# 🤖 Agent Evaluation — Complete Enterprise Deep Dive

> *Agents don't just produce outputs — they make decisions. Evaluating agents means evaluating the decision process, not just the result.*

---

## Why Agent Evaluation Is Different

An LLM produces text. You evaluate the text.

An agent produces a **trajectory** — a sequence of decisions:
1. Interpret the user's request
2. Decide which tool to call
3. Extract arguments for the tool
4. Interpret the tool's response
5. Decide the next step
6. Eventually, produce a final response

Any step can fail. A wrong tool selection makes everything downstream wrong. Agent evaluation must measure each step independently.

---

## The 6 Agent Evaluation Metrics

### 1. Tool Selection Accuracy (`tool_selection_accuracy.py`)

**Definition:** Did the agent pick the right tool for the query?

**How to measure:**
```
Ground truth: For query X, the correct tool is tool_A
Agent's choice: agent picked tool_B
Score: 0 (wrong tool)

Aggregate: correct_choices / total_queries
Production threshold: > 0.90
```

### 2. Task Completion Rate (`task_completion_rate.py`)

**Definition:** Did the agent achieve the user's goal?

**How to measure:**
- Binary: Did the final output satisfy the user's request? (LLM-as-judge)
- Weighted: For multi-step tasks, what fraction of sub-goals were completed?

**Production threshold:** > 0.85 for shipping.

### 3. Step Efficiency (`step_efficiency.py`)

**Definition:** Did the agent achieve the goal in a reasonable number of steps?

**Why it matters:** An agent that succeeds in 20 steps is worse than one that succeeds in 5. More steps = more cost, more latency, more failure modes.

**Metric:** `min_required_steps / actual_steps`. 1.0 = optimal.

### 4. Error Recovery (`error_recovery_eval.py`)

**Definition:** When something fails (tool error, bad input, unexpected response), does the agent recover gracefully?

**How to test:**
- Inject synthetic failures (tool returns error, malformed data)
- Measure: does the agent retry? try a different approach? gracefully report the failure?
- Score: successful_recoveries / injected_failures

### 5. Trajectory Analysis (`trajectory_analysis.py`)

**Definition:** Not a single metric — a diagnostic tool. Log every step of every agent run for post-hoc analysis.

**What to log per step:**
- LLM input (full prompt including scratchpad)
- LLM output (reasoning + tool call decision)
- Tool called + arguments
- Tool response
- Elapsed time
- Tokens used

**What to analyze:**
- Loop detection (agent calling same tool repeatedly)
- Reasoning quality per step (LLM-as-judge)
- Argument correctness (were tool inputs valid?)
- Time-to-first-progress (how many steps before the agent does something useful?)

### 6. Multi-Agent Evaluation (`multi_agent_eval.py`)

For CrewAI-style systems with multiple agents:
- Individual agent quality (each agent's task completion)
- Coordination quality (did agents share information effectively?)
- Delegation quality (did the manager delegate to the right specialist?)
- Bottleneck detection (which agent is the slow/weak link?)

---

## The Enterprise Agent Eval Framework

```
For each (query, expected_outcome) in agent_eval_dataset:
    1. Run agent → capture full trajectory
    2. Score each dimension:
       - Tool selection accuracy (per step)
       - Task completion (final outcome)
       - Step efficiency (steps taken vs min required)
       - Error recovery (if failures were injected)
    3. Trajectory analysis:
       - Detect loops
       - Score reasoning quality per step
       - Log for debugging
    4. Aggregate + regression check
```

---

*Previous: [← RAG Evaluation](../rag_evaluation/README.md) · Next: [Validation →](../validation/README.md)*

*Back to [main README](../../README.md)*
