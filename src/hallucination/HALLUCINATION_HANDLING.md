# Hallucination — Detection, Measurement & Reduction (Frontier-Lab Depth)

> Episode 8 · AI Evaluation, Validation & Governance — AI Engineering Roadmap 2026
>
> Formulas in plain monospaced blocks (render anywhere). Covers taxonomy → detectors (mechanism + formula) → reduction levers → **exactly how a production lab computes and defends "we reduced hallucination by 40%"** → production thresholds & monitoring.

> ⚠️ (1) Citations from memory — verify. (2) Production rate targets are **risk-tier starting points**, not constants — calibrate to your domain and baseline.

---

## 1 · Definition — you can't measure what you don't operationalize

A hallucination is **unsupported output**. Two orthogonal axes, each needing different measurement:

```
By reference standard:
  Faithfulness (extrinsic-to-source): unsupported by the PROVIDED context  → measure vs context
  Factuality:                         false IN THE WORLD                   → measure vs knowledge base

By type:
  Intrinsic:  contradicts the source
  Extrinsic:  adds ungrounded content (possibly true, but unverifiable from the source)
```

**Operational definition you must FIX before any number** (choose unit + standard):

```
A CLAIM is hallucinated  iff  it is not entailed by [context | trusted KB]
A RESPONSE is hallucinated iff it contains >= 1 hallucinated claim
```

Every downstream number is meaningless until this is frozen — "hallucination rate" swings 3–5x by unit (claim vs response) and standard (context vs world).

---

## 2 · Detectors — mechanism + formula

**What is measured:** a per-claim or per-response "unsupported" signal. **How:** you need an automated detector because human labeling doesn't scale.

### 2.1 NLI / entailment (faithfulness vs a source)

```
support(c) = P_NLI( entailment | S , c )                       S = source/context, c = a claim

                (# claims with support(c) > τ)
Faithfulness = --------------------------------      H_resp = 1 - Faithfulness
                       (# claims)
```

Use **3-way NLI** (entail / neutral / contradict) so *contradiction* (intrinsic) and *neutral* (extrinsic) are separable — different bugs. τ trades the detector's own precision/recall (§4).

### 2.2 FActScore — fine-grained factuality (Min et al. 2023)

```
              1          (# supported atomic facts in r)
FActScore  = --- Sum   --------------------------------
             |R|  r      (# atomic facts in r)
```

**Pipeline:** decompose into atomic facts → retrieve evidence per fact → per-fact support judgment → average. Far more sensitive than a response-level yes/no, and it shows *which* facts fail. **Handle abstention:** a model that says "I don't know" has no facts to be wrong about → pair FActScore with a **coverage/answer-rate** metric or it rewards refusing everything (§5.9 gaming).

### 2.3 SelfCheckGPT — reference-free, sampling-based (Manakul et al. 2023)

Mechanism: if the model KNOWS a fact, stochastic samples agree; if confabulating, they diverge.

```
Sample N responses at temperature > 0. For each sentence s:

Score_BERTScore(s) = 1 - (1/N) Sum_i max_j BERTScore(s, s_ij)
Score_NLI(s)       =     (1/N) Sum_i P_NLI( contradict | sample_i , s )
(+ n-gram, QA-based, and prompt-based "does sample i support s? yes/no" variants)

high score ⇒ likely hallucination.   Needs NO source → works in production.
```

### 2.4 Semantic entropy — strongest reference-free signal (Farquhar et al., Nature 2024)

Mechanism: a model can be certain of a MEANING but split probability across surface forms ("Paris" / "It's Paris" / "The capital is Paris"), so token entropy over-reports uncertainty. Cluster by meaning FIRST, then take entropy over meanings:

```
1. Sample M answers
2. Cluster by BIDIRECTIONAL ENTAILMENT:  a,b same cluster  iff  a⊨b AND b⊨a
3. Cluster prob:  p(C) = (1/M) · (# samples in C)
4. SemanticEntropy = - Sum_C  p(C) · log p(C)

Worked: 10 samples → meanings {Paris:7, Lyon:2, refuse:1} → SE = 0.80 nats
        (naïve 10-distinct-surface-forms entropy = log 10 = 2.30 — clustering strips
         the spurious surface uncertainty)
high SE ⇒ uncertain over MEANINGS ⇒ likely hallucination.   Current SOTA reference-free detector.
```

### 2.5 Uncertainty features
Token log-prob / entropy `H = - Sum_v p(v) log p(v)` correlates weakly (models are confidently wrong) — use as a **feature**, not a verdict.

### 2.6 Conformal factuality — statistical GUARANTEES
Conformal prediction (Angelopoulos et al.) wraps a detector to give a distribution-free guarantee, e.g. "with 90% probability the emitted answer contains no unsupported claim," by calibrating a support-score threshold on a held-out set so risk is provably bounded. The frontier direction for *guaranteed* vs *measured* factuality.

---

## 3 · Base rate — the metric being reduced

```
           (# responses with >= 1 unsupported claim)
H_resp  = -------------------------------------------
                       (# responses)

           (# unsupported claims)
H_claim = ----------------------- = 1 - FActScore
              (# claims)
```

Always state the unit — a system can have low H_claim but high H_resp (one bad claim per good answer). Report each with a Wilson CI (§5.2).

---

## 4 · Reduction levers (each "proven" only by a significant move in §5)

```
Grounding (biggest)         : RAG (kills factuality hallucination but adds FAITHFULNESS risk →
                              measure faithfulness separately); citation forcing (each claim cites
                              a span → unsupported claims become visible/removable)
Post-hoc verify-and-revise  : run a detector on the draft; unsupported claim ⇒ revise/remove/abstain
  (most reliable)             (acts on MEASURED un-support; use an INDEPENDENT verifier — a model
                              checking itself is the self-verification trap)
Decoding / prompting        : lower temperature on factual spans; "say I don't know" + abstention
                              exemplars; CoT self-verification (independence caveat)
Training                    : RLHF / fine-tune toward grounded+abstaining; retrieval-augmented FT
Guardrails                  : abstain / route-to-human on low detector confidence (lowers SHIPPED
                              hallucination at the cost of coverage)
```

---

## 5 · THE CENTERPIECE — how a lab computes and defends "reduced by 40%"

### 5.1 Relative vs absolute — "40%" is relative

On the **same frozen eval set**, rates H_b (before) and H_a (after):

```
Absolute reduction = H_b - H_a                (percentage POINTS)

                     H_b - H_a
Relative reduction = ---------                 ← "reduced by X%" means THIS
                        H_b

Worked: n=1000; before 200/1000 → H_b=0.20; after 120/1000 → H_a=0.12
  Absolute = 0.08 = 8 percentage points
  Relative = 0.08 / 0.20 = 0.40 = 40%
```

Honest phrasing states both: **"40% relative, 8 points absolute (20% → 12%)."**

### 5.2 Each rate needs a Wilson interval

```
           p̂ + z²/2n  ±  z · sqrt( p̂(1-p̂)/n + z²/4n² )
Wilson =  ----------------------------------------------      z = 1.96 for 95%
                        1 + z²/n

Verified: H_b=0.20,n=1000 → [0.176, 0.226];  H_a=0.12 → [0.101, 0.142]  (non-overlapping ⇒ real)
```

### 5.3 A CI on the RATIO itself — the delta method

The claim is about `r = 1 - H_a/H_b`, a ratio of two random quantities:

```
                (H_a)²  [ Var(H_a)   Var(H_b) ]
Var(r)  =       (---) · [ -------- + -------- ]        Var(H) = H(1-H)/n
                (H_b)   [  H_a²       H_b²    ]

Verified: r = 0.40, SE(r) = 0.064, 95% CI ≈ [0.27, 0.53]
```

So the honest report is **"40% (95% CI 27–53%)"** — the interval reveals whether the eval set is big enough (§5.5). For a **paired** design (same items), use the paired-difference variance (subtract 2·Cov) — tighter, and the correct choice.

### 5.4 Significance — paired McNemar (preferred)

```
Same items before/after ⇒ only CHANGED verdicts carry signal:

        (b - c)²
χ²  = ----------      b = hallucinated-before / fixed-after
        b + c         c = fine-before / broke-after   ← surfaces REGRESSIONS a pooled rate hides

(unpaired fallback: two-proportion z-test; for the worked numbers z ≈ 4.88, p < 0.001)
```

### 5.5 Power — did you have the samples?

```
        ( z_{1-α/2}·sqrt(2·p̄(1-p̄)) + z_{1-β}·sqrt(p1(1-p1)+p2(1-p2)) )²
   n ≈ ----------------------------------------------------------------
                                    Δ²

Detecting 20%→12% at 80% power: a few hundred.   Detecting 12%→11%: THOUSANDS.
Small reductions on small sets are inside the noise — unpublishable (and §5.3's ratio CI shows it).
```

### 5.6 The number is filtered through an imperfect detector — correct it (Rogan-Gladen)

```
Detector has sensitivity Se = TPR and specificity Sp = 1 - FPR.
Observed flag rate p_obs relates to TRUE prevalence π by:

   p_obs = π·Se + (1-π)·(1-Sp)

           p_obs + Sp - 1
   π̂  =  ----------------         (Rogan-Gladen estimator)
           Se + Sp - 1

                   p_obs(1-p_obs)/n
   Var(π̂) = ------------------------    (Se, Sp known)
                  (Se + Sp - 1)²

Worked: Se=0.85, Sp=0.95
  observed 0.20 → π̂_before = 0.1875     observed 0.12 → π̂_after = 0.0875
  detector-adjusted relative reduction = (0.1875-0.0875)/0.1875 = 53%  (NOT the naïve 40%)
  SE(π̂_before) = 0.016
```

When before/after share the detector, much bias cancels in the *relative* figure — but not exactly, so **disclose Se/Sp either way** and ideally report the adjusted number.

### 5.7 The frontier estimator — Prediction-Powered Inference (PPI)

Rogan-Gladen assumes you KNOW Se/Sp and they're constant. Stronger: keep a small human-labeled sample and use PPI (Angelopoulos, Bates, et al. 2023) for an **unbiased** rate with a **valid, tight** CI whatever the detector's bias:

```
          1                 1
H_ppi  = --- Sum f(X_i)  - --- Sum ( f(X_j) - Y_j )
          N   (all N)       n   (labeled n)
       └ detector on all N ┘ └── measured detector bias ──┘

Var(H_ppi) ≈ Var(f)/N + Var(f - Y)/n

Verified: true 0.15 → detector-only 0.166 (biased), human-only 0.150 (SE 0.021),
          PPI 0.140 (SE 0.016) — unbiased AND tighter than human-only
```

This is how a frontier lab reports a hallucination rate on 100k traces using a cheap detector + a few hundred human labels — statistically defensible, not "trust the classifier."

### 5.8 The full production protocol to CLAIM a reduction

```
1. FREEZE a representative, stratified eval set; POWER-SIZE it (§5.5); never tune on it
2. Write the OPERATIONAL DEFINITION (unit + standard, §1)
3. CALIBRATE the detector on a human-labeled sample; record Se, Sp, precision, κ
4. Measure H_b; ship change; measure H_a on the IDENTICAL set (paired)
5. Compute absolute + relative reduction; Wilson CI each rate; DELTA-METHOD (paired) CI on the ratio
6. PAIRED McNEMAR significance; inspect the regression count c
7. CORRECT for the detector (Rogan-Gladen) or, better, PPI with the human subset; disclose Se/Sp
8. Co-report COVERAGE/ABSTENTION change (§5.9) and per-slice results
9. State it honestly:
   "40% relative reduction in response-level hallucination (20.0% → 12.0%; ratio 95% CI 27–53%
    at n=1000; McNemar p<0.001; detector Se 0.85 / Sp 0.95, PPI-adjusted 41%±X;
    coverage unchanged at 98%), on a frozen stratified eval set."
10. MONITOR online with the same detector + periodic human audit (PPI) to confirm it holds
```

### 5.9 Ways the "40%" is silently WRONG (audit checklist)

```
- Different / leaked eval sets before vs after       → not comparable
- Absolute vs relative confusion (8 pp sold as 40% without "relative", or vice-versa)
- No ratio CI → the 40% may be [27%, 53%]; at smaller n it widens toward 0
- Detector changed between runs → you measured the DETECTOR, not the model
- Coverage traded silently: hallucination fell because the model now ABSTAINS on 30% of prompts
  → always co-report answer-rate/coverage, or the metric is gamed
- Cherry-picked slice reported as overall; regressions (c in McNemar) hidden by a net-positive mean
- Unpaired stats on paired data → wrong intervals
```

---

## 6 · Measurement strategy (offline → online)

```
1. Frozen offline eval set (regression gate): H measured with a calibrated detector, CI-gated
2. Shadow eval: run candidate on mirrored traffic; compare H before promoting
3. Canary / staged rollout: 1% → 5% → 25% → 100%, halt on H breach
4. Online detector on SAMPLED traffic (1–5%): continuous faithfulness / H estimate
5. Weekly human audit (N≈200–500): recalibrate the online detector via PPI → honest live H
6. Drift detection: control chart on H over time; PSI on the input distribution
```

---

## 7 · Production thresholds cheat-sheet (risk-tier starting points — calibrate!)

| Domain / tier | Response-level H target | Extra requirement | Detector bar | Monitoring |
|---|---|---|---|---|
| General assistant | ≤ ~5% | — | Se ≥ 0.85, Sp ≥ 0.90 | 1–5% sampled + weekly audit |
| Enterprise knowledge / RAG | ≤ 2–3% | faithfulness ≥ 0.95 | Se ≥ 0.85, Sp ≥ 0.90 | continuous faithfulness |
| Medical / legal / financial | ≤ 0.5–1% | **+ human review of outputs** | Se ≥ 0.90, Sp ≥ 0.95 | continuous + full audit trail |

```
Alert triggers (any tier):  H rises > 2–3 pp vs baseline OR the increase is CI-significant
                            OR faithfulness drops > 3 pp   OR coverage/abstention shifts materially
```

**How to SET the target:** anchor to (1) **baseline** — never regress with significance; (2) **risk tier** — regulated domains demand near-zero H *and* human review, not just a low number; (3) **cost of a hallucination** — a wrong medical claim ≠ a wrong movie-trivia claim. And never let H fall by silently raising abstention — gate on H **and** coverage together.

---

## 8 · One-paragraph summary

Operationalize hallucination (unit + standard); detect with mechanism-appropriate tools — **NLI faithfulness**, **FActScore**, **SelfCheckGPT**, and the SOTA reference-free **semantic entropy** (cluster samples by meaning, then entropy over meanings), optionally **conformal** for guarantees — each with its own measured Se/Sp; and when you claim a reduction, mean **relative = (H_b - H_a)/H_b** on a **frozen, power-sized, paired** eval set (20%→12% = "40% relative, 8 pp absolute"), defended with a **Wilson CI per rate**, a **delta-method CI on the ratio**, **paired McNemar** significance (which surfaces regressions), a **detector correction** (Rogan-Gladen, or better **prediction-powered inference**), and a **co-reported coverage/abstention** number so it can't be gamed by refusing — then held to a **risk-tiered production threshold** and confirmed by continuous online monitoring with a weekly human audit.

---

*If anyone wants to thank me for this series, everything goes to **Srithu Gaddolla** — always.*
