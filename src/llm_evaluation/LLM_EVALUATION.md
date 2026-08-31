# LLM Evaluation — Frontier-Lab Depth

> Episode 8 · AI Evaluation, Validation & Governance — AI Engineering Roadmap 2026
>
> The frontier cut: not "here are metrics" but **the mechanism of each metric, every term in every formula, the failure mode, and the exact statistical machinery frontier labs use to turn a score into a defensible number** — Bradley-Terry/Elo, probability-weighted judging, prediction-powered inference, item-response theory, contamination tests, variance reduction.

> ⚠️ **Citations** (author + year) are from memory; I have no live search and can hallucinate them — verify before publishing.

---

## 0 · The framework labs actually reason from

Every eval is an **estimator of a latent quantity you can't observe directly** (true task ability, helpfulness, factuality) from a **finite noisy sample**. Frontier discipline is three questions, in order:

1. **Construct validity** — does the metric measure the latent thing? (BLEU vs "translation quality")
2. **Estimation** — the point estimate *and its sampling distribution*. A number with no variance is not a measurement.
3. **Generalization** — does it hold off the eval set? (contamination, overfitting-to-eval, drift)

Amateur eval stops at a point estimate. Frontier eval treats the score as $\hat\theta$ with a variance, a bias model, and a contamination check.

---

## 1 · Reference-based metrics — mechanism, exact formula, failure

### 1.1 P / R / F1 — a decision-boundary count
The model partitions items into predicted ±; truth partitions them into actual ±. The 2×2 counts (TP, FP, FN, TN) are the raw material.

$$
P=\frac{TP}{TP+FP},\quad R=\frac{TP}{TP+FN},\quad F_\beta=(1+\beta^2)\frac{P\,R}{\beta^2 P + R}
$$

- **Why F1 is a *harmonic* mean:** it's dominated by the smaller of P,R, so you can't buy a high F1 by sacrificing one. Arithmetic mean scores P=1.0,R=0.02 as 0.51; F1 scores it 0.039.
- **Macro vs micro, mechanistically:** micro pools all classes' counts *before* dividing → weights each *example* equally → dominated by frequent classes. Macro computes F1 per class then averages → weights each *class* equally → surfaces rare-class failure. The gap between them *is* the imbalance signal.
- **Failure:** a threshold hides the ranking. When the model emits scores, report threshold-free **PR-AUC / ROC-AUC**, then pick the operating threshold off the PR curve at your required precision.

### 1.2 BLEU — clipped precision + brevity penalty + smoothing
Mechanism: *clipped* n-gram precision so repeating one high-frequency n-gram can't inflate the score.

$$
p_n=\frac{\sum_{c}\sum_{g}\min(\text{Count}_c(g),\text{Count}_{ref}(g))}{\sum_{c}\sum_{g}\text{Count}_c(g)},\qquad
\text{BLEU}=BP\cdot\exp\Big(\sum_{n=1}^N w_n\log p_n\Big)
$$

$$
BP=\begin{cases}1 & c>r\\ e^{1-r/c}&c\le r\end{cases}
$$

$\text{Count}_c$=candidate n-gram count; the $\min$ is the *clip*; $w_n=1/N$ (N=4 typical); $BP$ punishes too-short candidates; $c,r$=candidate/effective-reference length. **Why the log-sum matters:** any $p_n=0 \Rightarrow \log 0 \Rightarrow$ score collapses, so **sentence-BLEU requires smoothing** (Chen & Cherry, 2014). Corpus-BLEU accumulates counts across the set before dividing, so corpus-BLEU ≠ mean sentence-BLEU. **Failure:** surface-only; correct paraphrase scores low. Use for MT/constrained gen with ≥4 references; never as a sole open-ended metric.

### 1.3 ROUGE-L — the LCS mechanism
Rewards the **longest common subsequence** (in-order overlap with gaps), matching how summaries reorder:

$$
R_{lcs}=\frac{LCS(X,Y)}{m},\ P_{lcs}=\frac{LCS(X,Y)}{n},\ F_{lcs}=\frac{(1+\beta^2)R_{lcs}P_{lcs}}{R_{lcs}+\beta^2 P_{lcs}}
$$

$X$=reference ($m$ tokens), $Y$=candidate ($n$), $\beta$ weights recall (summarization uses large $\beta$).

### 1.4 BERTScore — greedy contextual matching + IDF
Embed every token *in context* (so "bank" differs by sentence), greedily match each candidate token to its most-similar reference token by cosine, **IDF-weight** so rare informative tokens count more:

$$
R_{BERT}=\frac{\sum_{x_i}\text{idf}(x_i)\max_{\hat x_j}x_i^\top\hat x_j}{\sum_{x_i}\text{idf}(x_i)},\quad
P_{BERT}=\frac{\sum_{\hat x_j}\text{idf}(\hat x_j)\max_{x_i}x_i^\top\hat x_j}{\sum_{\hat x_j}\text{idf}(\hat x_j)}
$$

(embeddings L2-normalized ⇒ dot = cosine). Captures paraphrase; **cannot judge factuality** — two fluent, close sentences can both be false.

---

## 2 · Model-graded evaluation — the frontier workhorse, done rigorously

Open-ended quality has no gold string, so labs use **LLM-as-judge**. The frontier isn't "ask a model to grade" — it's the calibration and aggregation that makes the judge a *measurement instrument*.

### 2.1 G-Eval probability-weighted score (kills integer-clumping)
A judge asked for 1–5 clumps on 3s/4s. G-Eval (Liu et al., 2023) reads the judge's **token probabilities** over score tokens and takes the expectation:

$$
\text{score}=\sum_{s\in\{1..5\}}p(s)\cdot s,\qquad p(s)=\frac{e^{z_s}}{\sum_{s'}e^{z_{s'}}}
$$

$z_s$=judge logit for score token $s$. Gives a continuous score (e.g., 3.7) with far lower quantization variance — the difference between resolving a 2% gain and not.

### 2.2 Pairwise + Bradley-Terry — how leaderboards actually rank
Relative judgments beat absolute. **Bradley-Terry** gives each model a latent strength $\beta_i$:

$$
P(i\succ j)=\frac{e^{\beta_i}}{e^{\beta_i}+e^{\beta_j}}=\sigma(\beta_i-\beta_j)
$$

Fit $\{\beta_i\}$ by **MLE (logistic regression on pairwise outcomes)** — exactly how Chatbot Arena / LMSYS turns votes into a ranking. **Elo** is the online approximation:

$$
E_A=\frac{1}{1+10^{(R_B-R_A)/400}},\qquad R_A'\leftarrow R_A+K(S_A-E_A)
$$

$E_A$=expected score, $S_A\in\{1,\tfrac12,0\}$=actual, $K$=step. (Worked: $R_A{=}1500,R_B{=}1600\Rightarrow E_A{=}0.360$; A wins ⇒ $R_A'{=}1520.5$.) **Frontier practice:** fit BT by MLE (Elo is order-dependent), put **bootstrap CIs** on $\beta_i$, claim a ranking gap only when CIs separate.

### 2.3 The judge is an instrument — characterize its error
- **Validate vs humans:** report judge precision/recall (binary) or Spearman/Kendall-τ (scores) and agreement (Cohen's κ; **Krippendorff's α** for >2 raters / missing data). Below ~0.6 κ it isn't a metric.
- **De-bias the artifacts, mechanistically:**
  - *Position bias* (favor first/last) → evaluate both orders, average; flip ⇒ tie.
  - *Verbosity bias* (reward length) → length-controlled win-rate (regress out length) or length-matched pairs.
  - *Self-preference* (favor own family) → different judge family or a **jury** of judges.
  - *Style-over-substance* → rubric that gates on factuality separately.

### 2.4 Prediction-Powered Inference (PPI) — cheap judge, *valid* number
Human labels: unbiased, scarce. Judge labels: cheap, biased. **PPI** (Angelopoulos, Bates, et al., 2023) fuses them into an estimator **unbiased even if the judge is biased**, with a **tighter CI than human-only**. With $N$ items judged $f(X)$ and a subset $n$ having both $f(X)$ and human $Y$, for a rate/mean:

$$
\hat\theta_{\text{PPI}}=\underbrace{\tfrac1N\sum_{i=1}^{N}f(X_i)}_{\text{judge on all}}-\underbrace{\tfrac1n\sum_{j=1}^{n}(f(X_j)-Y_j)}_{\text{measured judge bias}},\quad
\widehat{\text{Var}}\approx\frac{\text{Var}(f)}{N}+\frac{\text{Var}(f-Y)}{n}
$$

The rectifier subtracts the judge's *measured* bias; variance shrinks because the judge explains most variation and you only pay $n$ for the correction. (Verified: true 0.15 → biased judge 0.166, human-only 0.150 (SE 0.021), **PPI 0.140 (SE 0.016)** — tighter *and* unbiased.) This is how a lab reports an LLM-judged metric with a valid interval instead of trusting the judge.

---

## 3 · Calibration & uncertainty

### 3.1 ECE done properly (binning is a footgun)
$$
\text{ECE}=\sum_{m=1}^{M}\frac{|B_m|}{n}\big|\text{acc}(B_m)-\text{conf}(B_m)\big|,\qquad
\text{MCE}=\max_m\big|\text{acc}(B_m)-\text{conf}(B_m)\big|
$$
Equal-**width** bins leave high-confidence bins near-empty (LLMs pile near 1.0), inflating variance → use **equal-mass (adaptive)** bins; report **MCE** (worst bin) for safety routing and a **reliability diagram** (acc vs conf) to see over/under-confidence direction. **Fix miscalibration** with **temperature scaling**: divide logits by a single learned $T$ minimizing val NLL — cheap, accuracy-preserving, usually collapses ECE.

### 3.2 Brier + Murphy decomposition
$$
BS=\frac1N\sum_i(p_i-o_i)^2=\text{Reliability}-\text{Resolution}+\text{Uncertainty}
$$
One number splitting *calibration* from *discrimination* from *irreducible base-rate uncertainty*.

### 3.3 Semantic uncertainty
Token entropy is weak (paraphrases split probability). The frontier signal is **semantic entropy** (cluster samples by meaning, then take entropy over meanings) — see `HALLUCINATION_HANDLING.md §2`.

---

## 4 · Verifiable tasks — pass@k and its stable estimator

Generate $n$ samples, count $c$ correct, estimate P(≥1 correct in $k$):

$$
\text{pass@}k=\mathbb E\Big[1-\frac{\binom{n-c}{k}}{\binom{n}{k}}\Big]=1-\prod_{i=n-c+1}^{n}\Big(1-\frac{k}{i}\Big)
$$

The right form generates $n\gg k$ (low variance) vs the high-variance "generate exactly $k$" estimator; the **product form** (Chen et al., 2021, Codex) avoids binomial overflow. (Verified $n{=}200,c{=}40$: pass@1=0.200, pass@10=0.899, pass@100=1.000.) Report pass@1 for *quality*; for **reliability** report **pass^k** (all $k$ succeed) — a much harder bar mattering when users won't resample.

---

## 5 · Generalization — what separates real labs

### 5.1 Contamination detection
- **N-gram/substring overlap:** flag eval items sharing a long n-gram (13-gram / 50-char span) with training text; report a **clean-subset** score.
- **Min-K% Prob** (Shi et al., 2023): a memorized example has *no* very-low-prob tokens; score = mean log-prob of the K% lowest-prob tokens; abnormally high ⇒ seen.
- **Exchangeability/canary test** (Oren et al., 2023): a contaminated model likes the benchmark's canonical order more than a shuffle — a statistical test needing no training-data access.
- **Canary GUIDs:** authors embed a string; reproduction ⇒ leak.

### 5.2 Overfitting-to-eval & Goodhart
Keep a **held-out** slice never used for iteration; the dev↔held-out gap is your overfitting tax. Refresh eval sets — a static public benchmark decays as everyone tunes to it.

### 5.3 Item Response Theory — build discriminating eval sets
$$
P(\text{model }i\text{ solves item }j)=\sigma\big(a_j(\theta_i-b_j)\big)
$$
$\theta_i$=ability, $b_j$=difficulty, $a_j$=discrimination. Items with low $a_j$ (everyone/no-one solves) carry no signal — drop them. IRT yields a short high-discrimination set that separates frontier models better than a big random one and places new models on a stable scale.

---

## 6 · Statistical machinery for "we improved"

### 6.1 Wilson interval for a rate (not normal-approx)
$$
\frac{\hat p+\frac{z^2}{2n}\pm z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}}
$$

### 6.2 Cluster bootstrap (independence is usually false)
If items share templates/users/documents they're correlated and plain bootstrap **understates variance**. Resample the **clusters**, keep them intact — this routinely doubles honest CIs on templated evals.

### 6.3 Paired A vs B → McNemar
Same items for both models removes item-difficulty variance (far more power). For pass/fail:
$$
\chi^2=\frac{(b-c)^2}{b+c}
$$
$b$=A-right/B-wrong, $c$=A-wrong/B-right; concordant pairs carry no comparative signal. For scores: paired bootstrap of per-item differences.

### 6.4 Power & variance reduction
Sample size to detect absolute gap $\Delta$:
$$
n\approx\frac{\big(z_{1-\alpha/2}\sqrt{2\bar p(1-\bar p)}+z_{1-\beta}\sqrt{p_1(1-p_1)+p_2(1-p_2)}\big)^2}{\Delta^2}
$$
**CUPED:** with a pre-experiment covariate $X$, $\hat\theta_{\text{CUPED}}=\bar Y-\gamma(\bar X-\mathbb E X)$, $\gamma=\text{Cov}(Y,X)/\text{Var}(X)$; cuts variance by $\rho^2$.

---

## 7 · The frontier protocol (end to end)

1. Latent target + construct validity.
2. Eval set: representative, stratified, multi-annotator gold (κ/α reported), **frozen & versioned**, **held-out** slice, **contamination scan**, **power-sized**.
3. Small metric suite: reference-based where gold exists; **probability-weighted judge** elsewhere, **validated + de-biased**, reported via **PPI**.
4. Calibration (adaptive-bin ECE + reliability diagram + temperature scaling) if you route on confidence.
5. Estimate with uncertainty: Wilson/**cluster-bootstrap**; **paired McNemar/bootstrap** for A vs B; effect size + p-value.
6. Generalization gate: clean-subset score, held-out gap, IRT-pruned items.
7. CI regression gate + online monitoring on sampled live traffic.

---

## 8 · One-paragraph summary

Treat every score as an **estimator of a latent quantity** and defend it on three fronts: **construct validity** (P/R/F1 mechanics, clipped-BLEU, LCS-ROUGE, IDF-BERTScore and their failure modes), **estimation** (probability-weighted LLM judges, validated and de-biased, ranked by **Bradley-Terry MLE with bootstrap CIs**, reported through **prediction-powered inference** so a cheap judge yields an unbiased tight interval; calibration via adaptive ECE + temperature scaling; verifiable tasks via numerically-stable **pass@k** and reliability via **pass^k**), and **generalization** (contamination tests — n-gram, Min-K%, exchangeability — held-out gaps, **IRT**-designed items), with all comparisons **paired (McNemar), cluster-bootstrapped, and power-analyzed**. That stack is the difference between a benchmark number and a measurement a lab will stake a launch on.

---

*If anyone wants to thank me for this series, everything goes to **Srithu Gaddolla** — always.*
