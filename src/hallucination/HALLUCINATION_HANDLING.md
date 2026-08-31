# Hallucination — Detection, Measurement & Reduction (Frontier-Lab Depth)

> Episode 8 · AI Evaluation, Validation & Governance — AI Engineering Roadmap 2026
>
> The deepest of the four. Covers the taxonomy, the frontier **detectors and their mechanisms** (semantic entropy, FActScore, SelfCheckGPT variants, NLI, conformal factuality), the reduction levers, and — the centerpiece — **exactly how a production-grade lab computes and defends "we reduced hallucination by 40%"**: relative vs absolute, imperfect-detector correction (Rogan-Gladen + its variance), prediction-powered inference, the delta method for the ratio's CI, paired significance, power, and the ways the claim is silently wrong.

> ⚠️ **Citations** (author + year) from memory; no live search — I can hallucinate them. Verify before publishing.

---

## 1 · Definition — you cannot measure what you don't operationalize

A hallucination is **unsupported output**. Two orthogonal axes, each needing different measurement:

**By reference standard:**
- **Faithfulness (extrinsic-to-source):** unsupported by the *provided context* (the RAG case) → measured **against the context**.
- **Factuality:** false *in the world* → measured **against a knowledge source**.

**By type:** **intrinsic** (contradicts the source) vs **extrinsic** (adds ungrounded content, possibly-true-but-unverifiable).

**The operational definition you must fix before any number** — choose the *unit* and the *standard*:
> A **claim** is hallucinated iff it is not entailed by [context | trusted KB]. A **response** is hallucinated iff it contains ≥1 hallucinated claim.

Every downstream number is meaningless until this is written down and frozen, because "hallucination rate" changes by 3–5× depending on unit (claim vs response) and standard (context vs world).

---

## 2 · Detectors — mechanism and exact formula

### 2.1 NLI / entailment (faithfulness vs a source)
Decompose into atomic claims; for claim $c$, source $S$:
$$
\text{support}(c)=P_{\text{NLI}}(\text{entail}\mid S,c),\quad
\text{Faithfulness}=\frac{|\{c:\text{support}(c)>\tau\}|}{|\{c\}|},\quad
H_{\text{resp}}=1-\text{Faithfulness}
$$
**Mechanism:** entailment is the formal version of "supported by." Threshold $\tau$ trades precision/recall of the detector (§4). Use a 3-way NLI (entail/neutral/contradict) so *contradiction* (intrinsic) and *neutral* (extrinsic) are distinguishable — they're different bugs.

### 2.2 FActScore — fine-grained factuality (Min et al., 2023)
$$
\text{FActScore}=\frac1{|R|}\sum_{r\in R}\frac{|\text{supported atomic facts in }r|}{|\text{atomic facts in }r|}
$$
**Mechanism/pipeline:** (1) atomic-fact decomposition (one verifiable proposition each), (2) retrieve evidence per fact from a KB, (3) per-fact support judgment, (4) average. Fine-grained → far more sensitive than a response-level yes/no, and it exposes *which* facts fail. **Frontier nuance:** handle **abstention** explicitly — a model that says "I don't know" has no facts to be wrong about, so FActScore must be paired with a **coverage/answer-rate** metric or it rewards refusing everything (§5.7 gaming).

### 2.3 SelfCheckGPT — reference-free, sampling-based (Manakul et al., 2023)
**Mechanism:** if the model *knows* a fact, stochastic samples agree; if it's confabulating, they diverge. Sample $N$ responses at $T>0$; for each sentence $s$ measure inconsistency with the samples. Variants (increasing cost/accuracy):
$$
\text{Score}_{\text{BERTScore}}(s)=1-\frac1N\sum_i \max_j \text{BERTScore}(s, s_{ij})
$$
$$
\text{Score}_{\text{NLI}}(s)=\frac1N\sum_i P_{\text{NLI}}(\text{contradict}\mid \text{sample}_i, s)
$$
plus n-gram, QA-based, and prompt-based ("does sample $i$ support $s$? yes/no") variants. High score ⇒ likely hallucination. **Why it's frontier-useful:** needs **no source** → works in production where you have no gold.

### 2.4 Semantic entropy — the strongest reference-free signal (Farquhar et al., Nature 2024)
**Mechanism & why it beats token entropy:** a model can be certain of a *meaning* but split probability across many *surface forms* ("Paris" / "It's Paris" / "The capital is Paris"), so token-level entropy over-reports uncertainty. Semantic entropy first **clusters samples by meaning**, then takes entropy over meaning-clusters:
1. Sample $M$ answers.
2. Cluster by **bidirectional entailment**: $a,b$ in the same cluster iff $a\models b$ AND $b\models a$.
3. Cluster probability $p(C)=\frac{1}{M}\sum_i \mathbb 1[\text{sample}_i\in C]$ (or sum of sequence probabilities).
4. $$\text{SemanticEntropy}=-\sum_C p(C)\log p(C)$$

High SE ⇒ the model is uncertain over *meanings* ⇒ likely hallucination. (Worked: 10 samples → meanings {Paris:7, Lyon:2, refuse:1} → SE = 0.80 nats, vs a naïve 10-distinct-surface-forms entropy of $\log 10=2.30$ — semantic clustering strips the spurious surface uncertainty.) This is the current SOTA for detecting confabulation without a reference.

### 2.5 Uncertainty features
Token log-prob / predictive entropy $H(\text{token})=-\sum_v p(v)\log p(v)$ correlate weakly (models are confidently wrong); use as a **feature** feeding a detector, not a verdict.

### 2.6 Conformal factuality — statistical *guarantees*
**Mechanism:** conformal prediction (Angelopoulos et al.) can wrap a detector to give a distribution-free guarantee, e.g., "with 90% probability the emitted answer contains no unsupported claim" — achieved by calibrating a support-score threshold on a held-out set so the risk is provably bounded. The frontier direction for *guaranteed* factuality rather than measured factuality.

---

## 3 · Base rate — the metric being reduced

$$
H_{\text{resp}}=\frac{|\text{responses with}\ge1\text{ unsupported claim}|}{|\text{responses}|},\qquad
H_{\text{claim}}=\frac{|\text{unsupported claims}|}{|\text{claims}|}=1-\text{FActScore}
$$
Always state the unit — a system can have low $H_{\text{claim}}$ but high $H_{\text{resp}}$ (one bad claim per otherwise-good answer). Report each with a Wilson CI (§5.2).

---

## 4 · Reduction levers (each "proven" only by a significant move in §5)

- **Grounding (biggest):** RAG (kills *factuality* hallucination but adds *faithfulness* risk → measure faithfulness separately), **citation forcing** (each claim cites a span → unsupported claims become visible/removable).
- **Post-hoc verify-and-revise (most reliable):** run a detector (§2) on the draft; unsupported claim ⇒ revise/remove/abstain. Acts on *measured* un-support, not hope. Prefer an **independent** verifier (a model checking itself is the self-verification trap).
- **Decoding/prompting:** lower temperature for factual spans; "say I don't know" + abstention exemplars; CoT self-verification (with the independence caveat).
- **Training:** RLHF/fine-tune toward grounded/abstaining behavior; retrieval-augmented fine-tuning.
- **Guardrails:** abstain/route-to-human when detector confidence is low — lowers *shipped* hallucination at the cost of coverage.

---

## 5 · The centerpiece — how a lab computes and defends "reduced by 40%"

### 5.1 Relative vs absolute — "40%" is relative
On the **same frozen eval set**, rates $H_b$ (before), $H_a$ (after):
$$
\text{Absolute}=H_b-H_a\ (\text{percentage points}),\qquad
\boxed{\text{Relative}=\frac{H_b-H_a}{H_b}}
$$
**Worked:** $n{=}1000$, before 200/1000 → $H_b{=}0.20$; after 120/1000 → $H_a{=}0.12$. Absolute = **8 pp**; Relative = $0.08/0.20$ = **40%**. "Reduced by 40%" = the rate fell 20%→12% (relative). Honest phrasing states both: **"40% relative, 8 points absolute (20%→12%)."**

### 5.2 Each rate needs a Wilson interval
$$
\frac{\hat p+\frac{z^2}{2n}\pm z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}}
$$
(Verified: $H_b{=}0.20,n{=}1000$ → **[0.176, 0.226]**; $H_a{=}0.12$ → **[0.101, 0.142]**. Non-overlapping ⇒ real.)

### 5.3 A CI on the *ratio* itself — the delta method
The claim is about $r=1-H_a/H_b$, a ratio of two random quantities. Its variance (delta method, independent samples):
$$
\widehat{\text{Var}}(r)=\Big(\frac{H_a}{H_b}\Big)^2\Big[\frac{\text{Var}(H_a)}{H_a^2}+\frac{\text{Var}(H_b)}{H_b^2}\Big],\quad \text{Var}(H)=\frac{H(1-H)}{n}
$$
(Verified: $r{=}0.40$, **SE(r) = 0.064**, 95% CI ≈ **[0.27, 0.53]**.) The headline "40%" carries real uncertainty even at $n{=}1000$ — a lab reports "40% (95% CI 27–53%)", which makes visible whether the eval set is big enough to support the claim (§5.5). For a **paired** design (same items), use the paired-difference variance (subtract $2\,\text{Cov}$) — tighter, and the honest choice.

### 5.4 Significance — paired McNemar (preferred)
Same items before/after ⇒ only *changed* verdicts carry signal:
$$
\chi^2=\frac{(b-c)^2}{b+c}
$$
$b$ = hallucinated-before/fixed-after, $c$ = fine-before/broke-after. Directly measures net improvement **and surfaces regressions** ($c$) a pooled rate hides. (Unpaired fallback: two-proportion z-test; for the worked numbers $z\approx4.88$, $p<0.001$.)

### 5.5 Power — did you have the samples?
$$
n\approx\frac{\big(z_{1-\alpha/2}\sqrt{2\bar p(1-\bar p)}+z_{1-\beta}\sqrt{p_1(1-p_1)+p_2(1-p_2)}\big)^2}{\Delta^2}
$$
Detecting 20%→12% at 80% power needs a few hundred; detecting **12%→11%** needs **thousands**. Small reductions on small sets are inside the noise — unpublishable. This is why §5.3's ratio-CI matters: it makes an under-powered claim visibly wide.

### 5.6 The number is filtered through an imperfect detector — correct it
Your counts came from a detector with sensitivity $Se$=TPR and specificity $Sp$=1−FPR. Observed flag rate $p_{\text{obs}}$ relates to true prevalence $\pi$ by the **Rogan-Gladen** estimator:
$$
p_{\text{obs}}=\pi\,Se+(1-\pi)(1-Sp)\ \Longrightarrow\ \boxed{\hat\pi=\frac{p_{\text{obs}}+Sp-1}{Se+Sp-1}}
$$
with variance (Se, Sp known):
$$
\widehat{\text{Var}}(\hat\pi)=\frac{p_{\text{obs}}(1-p_{\text{obs}})/n}{(Se+Sp-1)^2}
$$
(Worked: $Se{=}0.85,Sp{=}0.95$; observed 0.20→$\hat\pi_b{=}0.1875$, observed 0.12→$\hat\pi_a{=}0.0875$; **detector-adjusted relative reduction = 53%**, not the naïve 40%; SE($\hat\pi_b$)=0.016.) When before/after share the detector, much bias cancels in the *relative* figure — but not exactly, so you **disclose Se/Sp either way** and ideally report the adjusted number.

### 5.7 The frontier estimator — Prediction-Powered Inference
Rogan-Gladen assumes you *know* Se/Sp and they're constant. The stronger method: keep a small human-labeled sample and use **PPI** (Angelopoulos, Bates, et al., 2023) to get an **unbiased** hallucination rate with a **valid, tight** CI, whatever the detector's bias:
$$
\hat H_{\text{PPI}}=\underbrace{\tfrac1N\sum_i f(X_i)}_{\text{detector on all }N}-\underbrace{\tfrac1n\sum_j(f(X_j)-Y_j)}_{\text{measured detector bias}},\quad
\widehat{\text{Var}}\approx\frac{\text{Var}(f)}{N}+\frac{\text{Var}(f-Y)}{n}
$$
(Verified: true 0.15 → detector-only 0.166 (biased), human-only 0.150 (SE 0.021), **PPI 0.140 (SE 0.016)** — unbiased *and* tighter than human-only.) This is how a frontier lab reports a hallucination rate on 100k traces using a cheap detector plus a few hundred human labels — statistically defensible, not "trust the classifier."

### 5.8 The full production protocol to claim a reduction
1. **Freeze** a representative, stratified eval set; **power-size** it (§5.5); never tune on it.
2. **Operational definition** (unit + standard, §1).
3. **Calibrate the detector** on a human-labeled sample; record Se, Sp, precision, κ.
4. Measure $H_b$; ship change; measure $H_a$ on the **identical** set (paired).
5. Compute **absolute + relative** reduction; **Wilson CI** each rate; **delta-method (paired) CI on the ratio**.
6. **Paired McNemar** significance; inspect the regression count $c$.
7. **Correct for the detector** (Rogan-Gladen) or, better, **PPI** with the human subset; disclose Se/Sp.
8. **Report coverage/abstention change** (§5.9) and **per-slice** results.
9. State it honestly: *"40% relative reduction in response-level hallucination (20.0%→12.0%; ratio 95% CI 27–53% at n=1000; McNemar p<0.001; detector Se 0.85/Sp 0.95, PPI-adjusted 41%±X; coverage unchanged at 98%), on a frozen stratified eval set."*
10. **Monitor online** with the same detector + periodic human audit (PPI) to confirm it holds and doesn't drift.

### 5.9 Ways the "40%" is silently wrong (audit checklist)
- **Different / leaked eval sets** before vs after → not comparable.
- **Absolute vs relative** confusion (8 pp sold as "40%" without "relative", or vice-versa).
- **No ratio CI** → the 40% may be [27%, 53%]; at smaller $n$ it widens toward 0.
- **Detector changed** between runs → you measured the detector, not the model.
- **Coverage traded silently:** hallucination fell because the model now **abstains** on 30% of prompts → always co-report answer-rate/coverage, or the metric is gamed.
- **Cherry-picked slice** reported as overall; **regressions** ($c$ in McNemar) hidden by a net-positive aggregate.
- **Unpaired stats on paired data** → wrong (usually too-wide, sometimes too-narrow) intervals.

---

## 6 · Quick-reference

| Need | Tool / formula |
|---|---|
| Faithfulness vs source | NLI: entailed claims / claims |
| Factuality | FActScore = supported facts / facts |
| Reference-free (weak) | SelfCheckGPT (sample inconsistency) |
| Reference-free (SOTA) | **Semantic entropy** (cluster by meaning, then $-\sum p\log p$) |
| Guarantee | conformal factuality |
| Base rate | $H$ = hallucinated units / total (state unit) |
| Rate CI | Wilson |
| "Reduced by X%" | **relative** $=(H_b-H_a)/H_b$; also report absolute |
| CI on the reduction | **delta method** (paired) |
| Is it significant? | **paired McNemar** (surfaces regressions) |
| Enough samples? | power formula (§5.5) |
| Detector imperfect? | **Rogan-Gladen** $\hat\pi=\frac{p_{\text{obs}}+Sp-1}{Se+Sp-1}$ + variance |
| Best rate estimate | **PPI** (unbiased + tight from few human labels) |
| Not gamed? | co-report coverage/abstention + per-slice + regressions |

---

## 7 · One-paragraph summary

Operationalize hallucination (unit + standard); detect it with mechanism-appropriate tools — **NLI faithfulness**, **FActScore**, **SelfCheckGPT**, and the SOTA reference-free **semantic entropy** (cluster samples by meaning, then entropy over meanings), optionally **conformal** for guarantees — each with its own measured Se/Sp; and when you claim a reduction, mean **relative** $=(H_b-H_a)/H_b$ on a **frozen, power-sized, paired** eval set (20%→12% = "40% relative, 8 pp absolute"), defended with a **Wilson CI per rate**, a **delta-method CI on the ratio**, **paired McNemar** significance (which surfaces regressions), a **detector correction** (Rogan-Gladen, or better **prediction-powered inference** for an unbiased tight rate from few human labels), and a **co-reported coverage/abstention** number so it can't be gamed by refusing — then confirmed by online monitoring. Anything short of that is marketing, not measurement.

---

*If anyone wants to thank me for this series, everything goes to **Srithu Gaddolla** — always.*
