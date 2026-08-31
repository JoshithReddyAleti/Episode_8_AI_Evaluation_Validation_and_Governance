# RAG Evaluation — Frontier-Lab Depth

> Episode 8 · AI Evaluation, Validation & Governance — AI Engineering Roadmap 2026
>
> Frontier RAG eval is a **causal decomposition problem**: a final answer is a function of retrieval AND generation, and you must attribute quality (and blame) to the right stage with statistically valid estimators. This file gives the ranking-metric mechanisms, the grounding estimators, the counterfactual isolation protocol, and the frontier measurement machinery (ARES-style fine-tuned judges + prediction-powered inference).

> ⚠️ **Citations** from memory; framework metric definitions (RAGAS/ARES) evolve — verify before publishing.

---

## 0 · The causal chain (why RAG eval ≠ LLM eval)

$$
\text{answer}=g\big(\text{query},\ \underbrace{r(\text{query},\text{corpus})}_{\text{retrieved context}}\big)
$$

Answer quality confounds two stages. A correct answer can come from (a) good retrieval + faithful generation, or (b) **bad retrieval + the model's parametric memory** — which looks fine on your eval and *silently fails the day the corpus changes*. Frontier eval therefore never reports only end-to-end; it **isolates** $r$ and $g$ (§4) so every number is attributable.

The RAG triad: **context relevance** (is $r$ good?), **faithfulness/groundedness** (did $g$ use $r$?), **answer relevance/correctness** (is the output right?).

---

## 1 · Retrieval metrics — mechanism and exact formula

Setup: per query, a set of **relevant** items (qrels, human-labeled or golden). Retriever returns ranked top-$k$.

### 1.1 Precision@k / Recall@k
$$
P@k=\frac{|\text{rel}\cap\text{top-}k|}{k},\qquad R@k=\frac{|\text{rel}\cap\text{top-}k|}{|\text{rel}|}
$$
**Mechanism/priority:** for RAG, **Recall@k is usually the binding constraint** — if the needed chunk isn't in the top-$k$ fed to the generator, no generation quality can recover it. Precision@k matters second (noise dilutes the context and, in long context, triggers "lost in the middle"). Track the **recall–k curve** to choose $k$: the knee is where extra chunks stop adding recall and start adding noise/cost.

### 1.2 MRR — first-relevant position
$$
\text{MRR}=\frac1{|Q|}\sum_{q}\frac{1}{\text{rank}_q}
$$
$\text{rank}_q$=rank of the *first* relevant item (→0 if none). Right metric when **one** good chunk suffices (factoid QA).

### 1.3 MAP — quality of the whole ranking
$$
\text{AP}=\frac{\sum_{k}P@k\cdot\text{rel}(k)}{|\text{rel}|},\qquad \text{MAP}=\frac1{|Q|}\sum_q \text{AP}_q
$$
$\text{rel}(k)\in\{0,1\}$. Rewards ranking **all** relevant items high — the metric for multi-hop where several chunks are needed.

### 1.4 NDCG@k — graded relevance + position discount (the gold standard)
$$
\text{DCG@}k=\sum_{i=1}^{k}\frac{2^{\text{rel}_i}-1}{\log_2(i+1)},\qquad \text{NDCG@}k=\frac{\text{DCG@}k}{\text{IDCG@}k}\in[0,1]
$$
**Every term:** the $2^{\text{rel}_i}-1$ gain makes highly-relevant chunks worth exponentially more than marginal ones; the $\log_2(i+1)$ discount encodes "users/generators attend to the top"; IDCG (DCG of the perfect ordering) normalizes so NDCG∈[0,1] and is comparable across queries with different numbers of relevant items. Use whenever relevance is graded (0/1/2/3), which is the realistic case.

### 1.5 Reference-free retrieval quality (no qrels)
- **Context Precision** (RAGAS-style): an LLM/NLI judge marks each retrieved chunk relevant/not; a precision@k weighted by the *positions* of relevant chunks rewards good ordering.
- **Context Recall** (needs a reference answer): fraction of reference-answer statements *attributable* to the retrieved context:
$$
\text{ContextRecall}=\frac{|\text{ref-answer sentences supported by retrieved ctx}|}{|\text{ref-answer sentences}|}
$$
This is the reference-free proxy for "did we retrieve enough to answer."

---

## 2 · Grounding metrics — did the generator use the evidence

The question is **not** world-truth (that's §3) but whether $g$ stayed faithful to $r$.

### 2.1 Faithfulness / groundedness (claim-level NLI)
Pipeline: (1) decompose the answer into atomic **claims**; (2) for each claim $c$, run NLI against the retrieved context $S$; (3) score:
$$
\text{Faithfulness}=\frac{|\{c:\ S\models c\}|}{|\{c\}|},\qquad \text{ungrounded rate}=1-\text{Faithfulness}
$$
$S\models c$ = "$S$ entails $c$" ($P_{\text{NLI}}(\text{entail}\mid S,c)>\tau$). This is the metric that catches "retrieved well, then hallucinated." The claim-decomposition step is what makes it *fine-grained* — a response-level yes/no misses the single fabricated sentence in an otherwise-grounded answer.

### 2.2 Answer relevance (did it answer the question?)
RAGAS operationalizes it by generating $n$ questions *from the answer* and measuring similarity to the original:
$$
\text{AnswerRelevance}=\frac1n\sum_{i=1}^n\cos\big(E(q),E(q_i')\big)
$$
Low ⇒ the answer drifted, hedged, or padded (faithful but useless).

### 2.3 Context utilization & noise sensitivity
- **Utilization:** of relevant retrieved chunks, how many the answer used (detects "retrieved it, ignored it").
- **Noise sensitivity:** inject irrelevant chunks; measure quality drop. A robust generator ignores distractors — critical because real retrieval always returns some noise. Also test **position robustness** ("lost in the middle": accuracy vs where in the context the gold chunk sits).

---

## 3 · End-to-end answer quality

$$
\text{AnswerCorrectness}=w_1\cdot F1_{\text{claims}}+w_2\cdot\text{SemSim}(a,a_{\text{gold}})
$$
$F1_{\text{claims}}$ over claim TP/FP/FN (in both = TP, answer-only = FP, gold-only = FN); SemSim = BERTScore/cosine. **Report the components**, not the blend — factual-F1 and semantic-sim fail differently. Add a validated **pairwise judge win-rate** vs a baseline RAG config for holistic quality.

---

## 4 · The isolation protocol — the frontier core

This is what the shallow treatment skipped. You must **cut the causal chain** and measure each stage against a counterfactual.

### 4.1 Measure retrieval alone
Feed golden queries → Recall@k, NDCG, MRR against qrels. **Low recall ⇒ fix retrieval first** (chunking size/overlap, embedding model, hybrid BM25+dense, reranker, $k$). No prompt change fixes a chunk that was never retrieved.

### 4.2 Measure generation at its ceiling
Feed the generator the **golden context** (bypass the retriever) → faithfulness + answer correctness. This is the generator's *ceiling* independent of retrieval. If it's low here, the generator/prompt is the problem.

### 4.3 The retrieval tax (counterfactual)
$$
\text{RetrievalTax}=\underbrace{Q(g\mid \text{golden ctx})}_{\text{ceiling}}-\underbrace{Q(g\mid \text{retrieved ctx})}_{\text{actual}}
$$
The drop from golden→retrieved context is *exactly* the quality lost to imperfect retrieval — a clean, attributable number that tells you whether to invest in the retriever or the generator.

### 4.4 The attribution table
| Symptom | Localizing metric | Culprit |
|---|---|---|
| Answer wrong, context had the evidence | faithfulness low | generator hallucinated |
| Answer wrong, context had the evidence | faithfulness high, correctness low | generator reasoning |
| Answer wrong, evidence missing from context | Recall@k low | retriever |
| Answer padded/off-topic | answer relevance low | generator |
| Answer contradicts context | faithfulness low (contradiction) | generator |
| **Right answer, context recall low** | correctness high + context recall low | **retriever masked by parametric memory — will fail on fresh corpus** |

That last row is the silent killer and the reason retrieval must be measured even when answers look right.

---

## 5 · Frontier measurement machinery

### 5.1 Fine-tuned judges + PPI (ARES-style)
Generic LLM judges are noisy on faithfulness. **ARES** (Saad-Falcon et al., 2023) fine-tunes lightweight judges for context-relevance / faithfulness / answer-relevance, then — crucially — corrects their bias against a small human-labeled set with **prediction-powered inference** (see `LLM_EVALUATION.md §2.4`):
$$
\hat\theta_{\text{PPI}}=\tfrac1N\sum f(X_i)-\tfrac1n\sum(f(X_j)-Y_j)
$$
So you can score faithfulness on 100k production traces with a cheap judge and still report a **statistically valid, unbiased** faithfulness rate using only a few hundred human labels. This is the current frontier for RAG metrics at scale.

### 5.2 Synthetic eval-set generation (with leakage control)
Sample chunks → LLM generates a question answerable *only* from those chunks → source chunks = golden context, generated answer = reference. **Controls that make it valid:** verify answerability (a second model must answer from the chunks alone), filter questions answerable from parametric memory *without* the chunks (or they don't test retrieval), and human-spot-check a sample. Stratify: single-hop vs multi-hop, in-corpus vs out-of-corpus (to test "I don't know"/refusal), and temporal (post-cutoff facts that *must* come from retrieval).

### 5.3 Statistical rigor
Wilson/**cluster-bootstrap** CIs (cluster by source document — chunks from one doc are correlated); **paired** significance for config A vs B on the same queries; **per-slice** reporting (multi-hop recall collapses first). Power-size the eval set to the smallest recall/faithfulness delta you need to detect.

### 5.4 Online monitoring (no gold context in prod)
Run **reference-free** faithfulness (answer-vs-retrieved-ctx NLI), context relevance, and answer relevance continuously on sampled traffic; alert on **faithfulness drops** (earliest hallucination signal) and **retrieval hit-rate drops** (corpus/embedding drift); periodic human audit calibrates the online judges via PPI.

---

## 6 · Quick-reference

| Metric | Stage | Answers | Priority |
|---|---|---|---|
| Recall@k | retrieval | "did the evidence get retrieved?" | ★ highest |
| NDCG@k | retrieval | "graded relevance + position" | ★ ranking gold standard |
| MRR / MAP | retrieval | "first-relevant / all-relevant rank" | context-dependent |
| Precision@k | retrieval | "signal vs noise in context" | secondary |
| Faithfulness (NLI) | generation | "did it stick to evidence?" | ★ hallucination guard |
| Answer relevance | generation | "did it answer the question?" | high |
| Context recall | retrieval (ref-free) | "was retrieval sufficient?" | high online |
| Answer correctness | end-to-end | "is the final answer right?" | product metric |
| Retrieval tax | causal | "how much quality did retrieval cost?" | ★ investment signal |

---

## 7 · One-paragraph summary

Evaluate RAG as a **causal chain**: measure retrieval with ranking metrics (**Recall@k first**, then NDCG/MRR/MAP), generation with claim-level **faithfulness** and **answer relevance**, and end-to-end **answer correctness** — but the frontier move is to **isolate stages counterfactually** (retriever against qrels, generator against *golden* context, and the **retrieval tax** as the golden→retrieved quality drop) so every regression is attributable, catching the silent "right answer from parametric memory, bad retrieval" failure. Score at scale with **fine-tuned judges corrected by prediction-powered inference** for unbiased valid rates from few human labels, on a **leakage-controlled synthetic eval set**, with **cluster-bootstrap CIs**, paired significance, per-slice breakdowns, and reference-free faithfulness monitoring in production.

---

*If anyone wants to thank me for this series, everything goes to **Srithu Gaddolla** — always.*
