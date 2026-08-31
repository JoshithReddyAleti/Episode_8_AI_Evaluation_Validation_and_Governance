# LLM Evaluation — Frontier-Lab Depth (Metrics · Measurement · Production Thresholds)

> Episode 8 · AI Evaluation, Validation & Governance — AI Engineering Roadmap 2026
>
> Formulas in plain monospaced blocks so they render in **any** markdown viewer. For each metric: **what is measured → how → which to watch → measurement strategy → production target/alert.**

> ⚠️ (1) Citations are from memory — verify. (2) Production numbers are **calibration starting points**, not universal constants — anchor to your baseline, risk tier, and human performance.

---

## 0 · The framework labs reason from

Every eval is an **estimator of a latent quantity you can't observe** (true ability, helpfulness, factuality) from a **finite noisy sample**. Discipline = three questions in order:

```
1. Construct validity — does the metric measure the latent thing?   (BLEU vs "quality")
2. Estimation         — point estimate AND its sampling distribution (a number with no
                        variance is not a measurement)
3. Generalization     — does it hold off the eval set?               (contamination, drift)
```

Amateur eval stops at a point estimate. Frontier eval treats a score as `θ̂` with a variance, a bias model, and a contamination check.

---

## 1 · Reference-based metrics

**What is measured:** agreement between model output and a **gold reference**. **How:** compare predicted vs gold via counts (classification), overlap (generation), or embeddings (semantic).

### 1.1 Precision / Recall / F1 — a decision-boundary count

```
        TP                 TP                        P · R
P  =  -------      R  =  -------      F_beta = (1+b²)·-----------
      TP + FP            TP + FN                      b²·P + R

TP true-positive  FP false-positive  FN false-negative
F1 = F_beta with b=1
```

- **Mechanism:** F1 is a **harmonic** mean → dominated by the smaller of P,R, so you can't buy a high F1 by sacrificing one (arithmetic mean scores P=1.0,R=0.02 as 0.51; F1 scores 0.039).
- **Macro vs micro:** *micro* pools all classes' counts before dividing → weights each **example** → dominated by frequent classes. *Macro* averages per-class F1 → weights each **class** → surfaces rare-class failure. The gap between them **is** the imbalance signal.
- **Which to watch:** when the model emits scores, watch **PR-AUC / ROC-AUC** (threshold-free) and pick the operating threshold off the PR curve at your required precision.
- **Prod target:** task-specific; gate on "no significant drop vs baseline." For safety classifiers, watch **recall** (missing a violation is worse than a false alarm) with a floor like ≥ 0.95.

### 1.2 BLEU — clipped precision + brevity penalty + smoothing

```
             Sum_c Sum_g  min( Count_cand(g) , Count_ref(g) )      ← the "clip"
p_n     =   -----------------------------------------------
                    Sum_c Sum_g  Count_cand(g)

BLEU    =   BP · exp( Sum_{n=1..N} w_n · log p_n )       w_n = 1/N  (N=4 typical)

              | 1              if c > r
BP      =     | exp(1 - r/c)   if c <= r          c = candidate length, r = reference length
```

- **Mechanism:** the `min(...)` clip stops a candidate gaming the score by repeating one high-frequency n-gram; BP punishes too-short candidates. **Any p_n = 0 ⇒ log 0 ⇒ score collapses**, so **sentence-BLEU needs smoothing** (Chen & Cherry, 2014). Corpus-BLEU accumulates counts before dividing → ≠ mean sentence-BLEU.
- **Which/when:** MT / constrained gen with ≥4 references. **Never** the sole metric for open-ended generation (correct paraphrase scores low).

### 1.3 ROUGE-L — longest common subsequence

```
          LCS(X,Y)          LCS(X,Y)              (1+b²)·R_lcs·P_lcs
R_lcs =  ----------  P_lcs = ---------  F_lcs =  --------------------
             m                   n                  R_lcs + b²·P_lcs

X = reference (m tokens), Y = candidate (n tokens); summarization uses large b (recall-weighted)
```

LCS rewards in-order overlap **with gaps**, matching how summaries reorder.

### 1.4 BERTScore — greedy contextual matching + IDF

```
           Sum_i idf(x_i) · max_j ( x_i · x̂_j )
R_bert =  ------------------------------------      (embeddings L2-normalized ⇒ dot = cosine)
                 Sum_i idf(x_i)

P_bert =  same, swapping candidate/reference          F_bert = harmonic mean(P_bert, R_bert)
```

Embeds each token **in context** ("bank" differs by sentence), greedily matches by cosine, IDF-weights so rare informative tokens count more. Captures paraphrase; **cannot judge factuality** (two fluent, close sentences can both be false).

---

## 2 · Model-graded evaluation (LLM-as-judge) — the frontier workhorse

**What is measured:** open-ended quality with no gold string. **How:** a strong model grades, but the frontier is the **calibration + aggregation** that makes the judge a *measurement instrument*.

### 2.1 G-Eval probability-weighted score (kills integer-clumping)

A judge asked for 1–5 clumps on 3s/4s. Read the judge's **token probabilities** over score tokens and take the expectation:

```
                                          exp(z_s)
score = Sum_{s in 1..5} p(s) · s     p(s) = -----------      z_s = judge logit for score token s
                                          Sum_s' exp(z_s')
```

Yields a continuous score (e.g. 3.7) with far lower quantization variance — the difference between resolving a 2% gain and not.

### 2.2 Pairwise + Bradley-Terry — how leaderboards actually rank

```
                 exp(beta_i)
P(i beats j) = --------------------- = sigmoid(beta_i - beta_j)
               exp(beta_i)+exp(beta_j)

Fit {beta_i} by MLE (logistic regression on pairwise win/loss outcomes).   ← Chatbot Arena / LMSYS

Elo (online approximation):
                    1
   E_A = --------------------------      R_A' = R_A + K·(S_A - E_A)
          1 + 10^((R_B - R_A)/400)       S_A in {1, 0.5, 0} = actual result
```

Worked: R_A=1500, R_B=1600 → E_A=0.360; if A wins, R_A'=1520.5. **Frontier practice:** fit Bradley-Terry by MLE (Elo is order-dependent), put **bootstrap CIs** on beta_i, claim a ranking gap only when CIs separate.

### 2.3 The judge is an instrument — characterize its error

- **Validate vs humans:** report judge precision/recall (binary) or Spearman/Kendall-τ (scores) and agreement (Cohen's κ; **Krippendorff's α** for >2 raters). **Below ~0.6 κ it isn't a metric.**
- **De-bias the known artifacts:**

```
Position bias   (favor first/last)  → evaluate BOTH orders, average; a flip ⇒ tie
Verbosity bias  (reward length)     → length-controlled win-rate (regress out length)
Self-preference (favor own family)  → different judge family, or a JURY of judges
Style>substance (fluent-wrong wins) → rubric that gates factuality separately
```

### 2.4 Prediction-Powered Inference (PPI) — cheap judge, VALID number

Human labels: unbiased, scarce. Judge labels: cheap, biased. PPI (Angelopoulos, Bates, et al., 2023) fuses them → **unbiased even if the judge is biased**, with a **tighter CI than human-only**:

```
          1                   1
θ_ppi  = --- Sum f(X_i)   -  --- Sum ( f(X_j) - Y_j )
          N   (all N)         n   (labeled n)
       └ judge on everything ┘ └── measured judge bias ──┘

Var(θ_ppi) ≈ Var(f)/N + Var(f - Y)/n         f = judge label, Y = human label
```

Verified demo: true rate 0.15 → biased judge 0.166, human-only 0.150 (SE 0.021), **PPI 0.140 (SE 0.016)** — tighter *and* unbiased. This is how a lab reports an LLM-judged metric with a valid interval.

---

## 3 · Calibration & uncertainty

**What is measured:** does the model's stated confidence match its actual accuracy (needed for routing/abstention)?

### 3.1 ECE (binning is a footgun)

```
          M  |B_m|
ECE  =   Sum ----- · | acc(B_m) - conf(B_m) |          MCE = max_m | acc(B_m) - conf(B_m) |
         m=1   n

B_m = the m-th confidence bin
```

Equal-**width** bins leave high-confidence bins near-empty (LLMs pile near 1.0) → inflated variance → use **equal-mass (adaptive)** bins; report **MCE** (worst bin) for safety routing and a **reliability diagram** to see over/under-confidence direction. **Fix miscalibration** with **temperature scaling**: divide logits by one learned T minimizing val NLL — cheap, accuracy-preserving, usually collapses ECE.
- **Prod target:** ECE **< 0.05** excellent, **< 0.10** acceptable for confidence-routing; **> 0.15 → recalibrate**.

### 3.2 Brier + Murphy decomposition

```
       1
BS  = --- Sum (p_i - o_i)²  = Reliability - Resolution + Uncertainty
       N   i                   (calibration) (discrimination) (base rate)

p_i = predicted probability, o_i in {0,1} = outcome
```

One number splitting calibration from discrimination from irreducible base-rate uncertainty.

### 3.3 Semantic uncertainty
Token entropy is weak (paraphrases split probability). The frontier signal is **semantic entropy** — cluster samples by meaning first — see `HALLUCINATION_HANDLING.md §2`.

---

## 4 · Verifiable tasks — pass@k and its stable estimator

**What/how:** for code/math with an executable checker, generate n samples, count c correct, estimate P(≥1 correct in k):

```
                  C(n-c, k)                          n
pass@k = 1 -  ---------------  =  1 -  Product   ( 1 - k/i )     ← numerically stable form
                  C(n, k)             i=n-c+1                       (Chen et al. 2021, Codex)
```

The stable product form avoids binomial overflow. Verified n=200,c=40: pass@1=0.200, pass@10=0.899, pass@100=1.000. Report pass@1 for **quality**; for **reliability** report **pass^k** (ALL k succeed ≈ (c/n)^k) — the harder bar that matters when users won't resample.

---

## 5 · Generalization — what separates real labs

### 5.1 Contamination detection (is the test in training data?)

```
N-gram/substring overlap : flag eval items sharing a 13-gram / 50-char span with training text
Min-K% Prob (Shi 2023)   : memorized text has NO very-low-prob tokens; score = mean log-prob of
                           the K% lowest-prob tokens; abnormally high ⇒ seen in training
Exchangeability (Oren 23): a contaminated model likes the benchmark's canonical order more than a
                           shuffle — a statistical test needing no training-data access
Canary GUIDs             : authors embed a string; reproduction ⇒ leak
```

Report a **clean-subset** score.

### 5.2 Overfitting-to-eval & Goodhart
Keep a **held-out** slice never used for iteration; the dev↔held-out gap is your overfitting tax. Refresh eval sets — a static public benchmark decays as everyone tunes to it.

### 5.3 Item Response Theory — build discriminating eval sets

```
P(model i solves item j) = sigmoid( a_j · ( theta_i - b_j ) )

theta_i = model ability   b_j = item difficulty   a_j = item discrimination
```

Items with low a_j (everyone/no-one solves) carry **no signal** — drop them. IRT yields a short, high-discrimination set that separates frontier models better than a big random one.

---

## 6 · Statistical machinery for "we improved"

```
Wilson CI for a rate (use this, not normal-approx):

           p̂ + z²/2n  ±  z · sqrt( p̂(1-p̂)/n + z²/4n² )
Wilson =  ----------------------------------------------
                        1 + z²/n

Cluster bootstrap : items sharing templates/users/docs are correlated → resample the CLUSTERS,
                    keep them intact (plain bootstrap fakes precision)

Paired A vs B (same items) → McNemar for pass/fail:
          (b - c)²
   χ²  = ----------      b = A-right/B-wrong, c = A-wrong/B-right  (concordant pairs carry no signal)
           b + c

Sample size to detect absolute gap Δ:
        ( z_{1-α/2}·sqrt(2·p̄(1-p̄)) + z_{1-β}·sqrt(p1(1-p1)+p2(1-p2)) )²
   n ≈ ----------------------------------------------------------------
                                    Δ²

CUPED variance reduction: θ_cuped = Ȳ - γ·(X̄ - E[X]),  γ = Cov(Y,X)/Var(X)  → cuts variance by ρ²
```

---

## 7 · Measurement strategy (offline → online)

```
1. Frozen offline golden set → CI regression gate on every model/prompt change
2. Shadow eval              → run candidate on mirrored traffic, compare, before promoting
3. Canary / staged rollout  → 1% → 5% → 25% → 100%, halt on threshold breach
4. Online sampling          → score 1–5% of live traffic with the automated suite
5. Human audit loop (weekly)→ label N≈100–300; recalibrate auto-metrics via PPI
6. Drift detection          → control charts on key metrics + PSI on the input distribution
```

---

## 8 · Production thresholds cheat-sheet (starting ranges — calibrate!)

| Metric | What it guards | Typical target | Alert / gate | Cadence |
|---|---|---|---|---|
| Task accuracy / F1 | correctness | no sig. drop vs baseline | CI excludes 0 on the drop | offline gate |
| Safety-classifier recall | missed violations | ≥ 0.95 | any drop | offline + online |
| False-refusal rate | over-refusal | ≤ 2–5% | rises with safety gains | online |
| Judge–human κ | judge trust | ≥ 0.6 (use), ≥ 0.8 (primary) | < 0.6 → don't ship judge | pre-launch + monthly |
| Judge position-flip rate | judge bias | < 5–10% | rising | per eval run |
| ECE | calibration | < 0.05 (rout.), < 0.10 ok | > 0.15 → recalibrate | offline |
| pass@1 / pass^k | quality / reliability | task-specific | sig. regression | offline gate |
| Win-rate vs baseline | holistic quality | > 50% (CI excludes 50) | ≤ 50% | shadow + canary |
| PSI (input drift) | distribution shift | < 0.1 | > 0.25 → re-eval/retrain | daily |

**How to SET a threshold:** anchor to (1) **baseline** — never regress below the shipped number with statistical significance; (2) **risk tier** — regulated/safety-critical demand higher floors *and* human review; (3) **human performance** — don't demand a bar the task can't support. The gate is "no significant regression vs baseline, and above the tier floor," not a magic number.

---

## 9 · One-paragraph summary

Treat every score as an **estimator of a latent quantity** and defend it on **construct validity** (P/R/F1 mechanics, clipped-BLEU, LCS-ROUGE, IDF-BERTScore + failure modes), **estimation** (probability-weighted LLM judges, validated and de-biased, ranked by **Bradley-Terry MLE with bootstrap CIs**, reported via **prediction-powered inference**; calibration via adaptive ECE + temperature scaling; **pass@k** and **pass^k**), and **generalization** (contamination tests, held-out gaps, **IRT** items) — all with **Wilson/cluster-bootstrap CIs, paired McNemar, power analysis**; then operationalize with a **layered strategy** (offline gate → shadow → canary → online sampling → weekly human audit → PSI drift) held to **baseline-anchored, risk-tiered thresholds**.

---

*If anyone wants to thank me for this series, everything goes to **Srithu Gaddolla** — always.*
