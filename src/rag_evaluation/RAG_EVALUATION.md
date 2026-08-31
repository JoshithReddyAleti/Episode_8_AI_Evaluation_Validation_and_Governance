# RAG Evaluation — Frontier-Lab Depth (Metrics · Measurement · Production Thresholds)

> Episode 8 · AI Evaluation, Validation & Governance — AI Engineering Roadmap 2026
>
> All formulas are written in plain monospaced blocks so they render in **any** markdown viewer (GitHub, VS Code, mobile) — no LaTeX required. For each metric you get: **what is measured → how it's measured → which metrics to watch → the strategy to measure it → the production target/alert threshold.**

> ⚠️ **Two caveats.** (1) Citations (author + year) are from memory — verify before publishing. (2) The production target numbers below are **typical starting ranges**, not universal constants. Always calibrate to your **baseline**, your **risk tier**, and **human performance** on the task. Treat them as where to start a conversation, not law.

---

## 0 · The causal chain (why RAG eval ≠ LLM eval)

A RAG answer is produced by two stages, and quality confounds both:

```
answer = generate( query , retrieve(query, corpus) )
                              └─ retrieved context ─┘
```

A correct answer can come from (a) good retrieval + faithful generation, OR (b) **bad retrieval + the model's parametric memory** — which looks fine on your eval and silently fails the day the corpus changes. So frontier RAG eval never reports only end-to-end; it **isolates** retrieval and generation (§4) so every number is attributable to a stage.

The **RAG triad** you monitor:

```
context relevance  → is retrieval good?          (retriever)
faithfulness       → did generation use context? (generator)
answer relevance   → did it answer the question?  (end-to-end)
```

---

## 1 · Retrieval metrics

**What is measured (this whole group):** the *ranking quality* of the retriever — did the evidence needed to answer land in the top-k chunks fed to the generator, and how high?
**How it's measured:** per query you need a set of **relevant** items (the "qrels" — from human labeling or a golden set); you compare the retriever's ranked top-k against them.

### 1.1 Precision@k and Recall@k

```
                 (# relevant items in top-k)
Precision@k  =   ---------------------------
                             k

                 (# relevant items in top-k)
Recall@k     =   ---------------------------
                    (total # relevant items)
```

- **Precision@k** = of the k you retrieved, how many were relevant → measures **context noise**.
- **Recall@k** = of all relevant items, how many made the top-k → measures **evidence coverage**.
- **Which to watch:** for RAG, **Recall@k is the binding constraint** — if the needed chunk isn't in the top-k, no generation quality can recover it. Precision@k is second (noise dilutes context and triggers "lost in the middle").
- **Strategy:** plot the **recall–k curve** and pick k at the *knee* — where extra chunks stop adding recall and start adding cost/noise.
- **Prod target (starting ranges):** Recall@k (at the k you actually feed the generator) **≥ 0.90** for factoid QA, **≥ 0.95** for high-stakes; alert if it drops **> 5 pp below baseline** (corpus/embedding drift). Precision@k tolerance is looser (**≥ 0.5–0.7**) since the generator can ignore some noise.

### 1.2 MRR — Mean Reciprocal Rank (position of first relevant)

```
              1        1
MRR   =  ---------- · Sum  ------
          |queries|   q    rank_q

rank_q = rank of the FIRST relevant item for query q  (→ 0 if none found)
```

- **What/which:** rewards putting *a* relevant chunk near the top. Right metric when **one** good chunk suffices (factoid).
- **Prod target:** **≥ 0.7–0.8** typical for well-tuned factoid retrieval; calibrate to baseline.

### 1.3 MAP — Mean Average Precision (whole-ranking quality)

```
              Sum_k [ Precision@k · rel(k) ]
AP        =   -----------------------------      rel(k) = 1 if item at rank k is relevant, else 0
                   (total # relevant)

               1
MAP       =  ------ · Sum   AP_q
             |Q|        q
```

- **What/which:** rewards ranking **all** relevant items high — the metric for **multi-hop** where several chunks are needed. Watch this (not MRR) when answers require synthesizing multiple sources.

### 1.4 NDCG@k — graded relevance + position discount (the gold standard)

```
              k        2^(rel_i) - 1
DCG@k   =    Sum     ----------------          rel_i = graded relevance of item at rank i (e.g. 0,1,2,3)
             i=1        log2(i + 1)

              DCG@k
NDCG@k  =   ---------          in [0, 1]        IDCG@k = DCG@k of the PERFECT ranking (ideal order)
             IDCG@k
```

- **How / every term:** the gain `2^(rel_i) - 1` makes a highly-relevant chunk worth exponentially more than a marginally-relevant one; the discount `log2(i+1)` encodes "items near the top matter more" (a relevant chunk at rank 1 counts far more than at rank 10); dividing by IDCG (the score of the perfectly-sorted list) normalizes to [0,1] so queries with different numbers of relevant items are comparable.
- **Which:** use whenever relevance is **graded** (0/1/2/3), which is the realistic case. This is the retrieval metric frontier teams report first.
- **Prod target:** **≥ 0.8** is strong for graded relevance; alert on a significant drop vs baseline.

### 1.5 Reference-free retrieval quality (no human qrels — for production)

```
Context Precision (RAGAS-style):
   an LLM/NLI judge marks each retrieved chunk relevant / not,
   weighted by the POSITIONS of the relevant chunks (rewards good ordering)

                     (# reference-answer sentences supported by retrieved context)
Context Recall  =   -------------------------------------------------------------
                             (total # reference-answer sentences)
```

- **Strategy:** these need no qrels, so they're what you run **online** (where you have no gold ranking). Context Recall is the reference-free proxy for "did we retrieve enough to answer."
- **Prod target:** Context Recall **≥ 0.85**, Context Precision **≥ 0.7**; both calibrated to baseline.

---

## 2 · Generation / grounding metrics

**What is measured:** NOT world-truth (that's §3) but whether the generator stayed **faithful to the context it was given**.

### 2.1 Faithfulness / groundedness (the hallucination guard)

**How it's measured (pipeline):** (1) decompose the answer into atomic **claims**; (2) for each claim, run NLI entailment against the retrieved context; (3) score.

```
                    (# claims entailed by retrieved context)
Faithfulness  =    ----------------------------------------
                            (total # claims)

ungrounded rate = 1 - Faithfulness

"entailed" = NLI(entailment | context, claim) > threshold τ
```

- **Which / why:** this catches "retrieved well, then made something up." The claim-decomposition is what makes it *fine-grained* — a response-level yes/no misses the one fabricated sentence in an otherwise-grounded answer. Use **3-way NLI** (entail / neutral / contradict) so *contradiction* (intrinsic) and *neutral* (extrinsic) are separable — different bugs.
- **Strategy:** run continuously on **sampled production traffic** — a faithfulness drop is the **earliest hallucination signal** you have.
- **Prod target:** Faithfulness **≥ 0.90** general, **≥ 0.95–0.98** for enterprise-knowledge / regulated; **alert if it drops > 3 pp** from baseline or below 0.85.

### 2.2 Answer Relevance (did it answer the question?)

**How:** generate n questions *from the answer*, measure their similarity back to the original question.

```
                       1
AnswerRelevance  =    --- · Sum   cosine( E(q) , E(q_i') )
                       n     i

E(·)   = embedding
q      = original question
q_i'   = i-th question generated from the answer
```

- **Which:** low score ⇒ the answer drifted, hedged, or padded (faithful but useless).
- **Prod target:** **≥ 0.85**; watch for drops when prompts or models change.

### 2.3 Context utilization & robustness (strategies, not single numbers)

- **Utilization:** of the relevant retrieved chunks, how many the answer used (detects "retrieved it, ignored it").
- **Noise sensitivity:** inject irrelevant chunks, measure the quality drop — a robust generator ignores distractors (real retrieval always returns noise).
- **Position robustness ("lost in the middle"):** measure accuracy vs *where* in the context the gold chunk sits; frontier models still degrade for mid-context evidence, so put the best chunks at the edges.

---

## 3 · End-to-end answer quality

```
AnswerCorrectness = w1 · F1_claims + w2 · SemSim(answer, gold_answer)

F1_claims: over claim TP/FP/FN
   TP = claim in both answer and gold
   FP = claim in answer only        (commission error)
   FN = claim in gold only          (omission error)
SemSim = BERTScore or embedding cosine
```

- **Strategy:** **report the components, not the blend** — factual-F1 (is it right?) and semantic-sim (does it read like the gold?) fail differently. Add a **validated pairwise judge win-rate** vs a baseline RAG config for holistic quality.

---

## 4 · The isolation protocol (the frontier core — cut the causal chain)

You must measure each stage against a **counterfactual**, or you can't attribute a regression.

**4.1 Retrieval alone** — feed golden queries → Recall@k / NDCG / MRR vs qrels. Low recall ⇒ **fix retrieval first** (chunk size/overlap, embedding model, hybrid BM25+dense, reranker, k). No prompt change fixes a chunk that was never retrieved.

**4.2 Generation at its ceiling** — feed the generator the **golden context** (bypass the retriever) → faithfulness + correctness. This is the generator's ceiling *independent of retrieval*. Low here ⇒ the generator/prompt is the problem.

**4.3 The retrieval tax (the attributable number):**

```
RetrievalTax = Quality(generator | GOLDEN context)      ← ceiling
             - Quality(generator | RETRIEVED context)   ← actual
```

The golden→retrieved drop is exactly the quality lost to imperfect retrieval — it tells you whether to invest in the retriever or the generator.

**4.4 Attribution table:**

| Symptom | Localizing metric | Culprit |
|---|---|---|
| Answer wrong, context had the evidence | faithfulness LOW | generator hallucinated |
| Answer wrong, context had the evidence | faithfulness high, correctness LOW | generator reasoning |
| Answer wrong, evidence missing from context | Recall@k LOW | retriever |
| Answer padded / off-topic | answer relevance LOW | generator |
| Answer contradicts context | faithfulness LOW (contradiction) | generator |
| **Right answer, context recall LOW** | correctness high + context recall low | **retriever masked by parametric memory — fails on fresh corpus** |

---

## 5 · Measurement strategy — offline, online, and in between

Real teams run a **layered** strategy, not one eval:

1. **Frozen offline golden set (regression gate).** A versioned, stratified set with golden answer + golden context per query. Runs in CI on every change. Blocks release on a statistically-significant regression (§7).
2. **Shadow evaluation.** Run the *candidate* pipeline on **mirrored production traffic** (no user impact); compare faithfulness/relevance against the current pipeline before promoting.
3. **Canary / staged rollout.** Ship to 1% → measure online metrics → expand to 5% → 25% → 100%, halting on threshold breach.
4. **Online reference-free monitoring.** Continuously score **sampled** live traffic (1–5%) with faithfulness / context-relevance / answer-relevance (no gold needed).
5. **Human audit loop.** Weekly, label a small sample (N ≈ 100–300) by hand; use it to **recalibrate** the automated judges (via prediction-powered inference, §6) so the online numbers stay honest.
6. **Drift detection.** Track retrieval hit-rate and faithfulness over time on a control chart; compute a **Population Stability Index** on the query/embedding distribution:

```
PSI = Sum_bins ( actual% - expected% ) · ln( actual% / expected% )

PSI < 0.1  : no significant drift
0.1–0.25   : moderate drift — investigate
> 0.25     : major drift — retrain/re-index
```

---

## 6 · Frontier measurement machinery (valid numbers at scale)

Generic LLM judges are noisy on faithfulness. **ARES**-style (Saad-Falcon et al., 2023) fine-tunes lightweight judges for context-relevance / faithfulness / answer-relevance, then corrects their bias against a small human-labeled set with **Prediction-Powered Inference (PPI)** (Angelopoulos, Bates, et al., 2023):

```
                 1                  1
H_ppi     =     --- Sum f(X_i)  -  --- Sum ( f(X_j) - Y_j )
                 N   i (all N)      n   j (labeled n)
              └ judge on everything ┘ └─ measured judge bias ─┘

Var(H_ppi) ≈ Var(f)/N + Var(f - Y)/n     (tighter than human-only)

f(X) = cheap judge label   Y = human label (on the small subset)
```

So you score faithfulness on 100k production traces with a cheap judge and still report a **statistically valid, unbiased** rate using only a few hundred human labels.

**Synthetic eval-set generation (with leakage control):** sample chunks → LLM generates a question answerable *only* from those chunks → source chunks = golden context, generated answer = reference. Validity controls: verify answerability from the chunks alone; **discard questions answerable from parametric memory without the chunks** (they don't test retrieval); human-spot-check a sample; stratify single-hop / multi-hop / out-of-corpus (tests "I don't know") / temporal (post-cutoff facts that *must* come from retrieval).

---

## 7 · Statistical rigor

- **Confidence interval on a rate** — use **Wilson** (not normal-approx, which underflows near 0/1):

```
            p̂ + z²/2n  ±  z · sqrt( p̂(1-p̂)/n + z²/4n² )
Wilson =   ----------------------------------------------
                          1 + z²/n
```

- **Cluster bootstrap** — chunks/queries from one **source document** are correlated; resample *documents*, keep them intact, or you fake precision.
- **Paired A vs B** — same queries for both configs; paired bootstrap of per-query differences, or McNemar on per-query success. Removes query-difficulty variance → far more power.
- **Regression gate:** block release only when the drop is **statistically significant** (CI on the difference excludes 0), not on noise.

---

## 8 · Production thresholds cheat-sheet (starting ranges — calibrate!)

| Metric | Stage | Typical prod target | Alert / regression trigger | Cadence |
|---|---|---|---|---|
| Recall@k (at generator k) | retrieval | ≥ 0.90 (≥ 0.95 high-stakes) | > 5 pp below baseline | offline + drift |
| NDCG@k | retrieval | ≥ 0.80 | significant drop vs baseline | offline |
| MRR | retrieval | ≥ 0.7–0.8 (factoid) | — | offline |
| Faithfulness | generation | ≥ 0.90 (≥ 0.95–0.98 regulated) | > 3 pp drop or < 0.85 | **online, continuous** |
| Answer relevance | generation | ≥ 0.85 | drop vs baseline | online |
| Context precision | retrieval (ref-free) | ≥ 0.7 | — | online |
| Answer correctness | end-to-end | product-specific | CI-significant regression | offline gate |
| Retrieval hit-rate | retrieval | ≥ baseline | drop → corpus drift | online + PSI |
| PSI (query/embedding drift) | infra | < 0.1 | > 0.25 → re-index/retrain | daily |

**How to SET a threshold (the principle):** anchor it to three things — (1) your **baseline** (never regress below the current shipped number with statistical significance); (2) your **risk tier** (regulated/medical/legal demand ≥ 0.95–0.98 faithfulness *and* human review); (3) **human performance** (don't demand super-human faithfulness the task can't support). Absolute numbers above are anchors; the *gate* is "no significant regression vs baseline, and above the tier's floor."

---

## 9 · One-paragraph summary

Evaluate RAG as a **causal chain**: retrieval with ranking metrics (**Recall@k first**, then NDCG/MRR/MAP), generation with claim-level **faithfulness** and **answer relevance**, end-to-end **answer correctness** — but **isolate the stages counterfactually** (retriever vs qrels, generator vs *golden* context, and the **retrieval tax** as the golden→retrieved drop) so every regression is attributable, catching the silent "right answer from parametric memory" failure. Score at scale with **fine-tuned judges corrected by prediction-powered inference**, on a **leakage-controlled synthetic + human golden set**, run a **layered strategy** (frozen offline gate → shadow eval → canary → online reference-free monitoring → weekly human audit → PSI drift detection), and hold each metric to a **baseline-anchored, risk-tiered production threshold** with cluster-bootstrap, paired significance.

---

*If anyone wants to thank me for this series, everything goes to **Srithu Gaddolla** — always.*
