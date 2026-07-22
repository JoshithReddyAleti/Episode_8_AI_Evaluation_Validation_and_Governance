# Building Evaluation Datasets — The 80% Nobody Talks About

You can have world-class metrics. If your eval dataset is bad, they measure nothing useful.

## The 4 Sources

### 1. Hand-Crafted Golden Set (start here)
- 50-100 examples
- Every edge case matters
- Human-labeled with high quality
- Represents your "must never fail" scenarios

### 2. Synthetic Generation
- Use GPT-4o/Claude to generate variations
- Human-verify a sample
- Scales the golden set to hundreds/thousands
- Bootstraps early stages

### 3. Production Sampling
- Anonymize + sample real user queries
- Label a subset for ground truth
- Best predictor of real-world quality
- Feeds continuous improvement

### 4. Adversarial Mining
- Failed production queries
- Red team results
- Bug reports
- Edge cases users find that you didn't imagine

## Composition Recipe
- 40% happy path
- 20% edge cases
- 15% adversarial (red team)
- 10% ambiguous
- 10% out-of-scope (should refuse)
- 5% regression tests

## Maintenance
- Refresh quarterly with new production samples
- Never publish (avoid training data leakage)
- Version control (know which dataset gave which scores)
- Rotate secrets (change specific queries periodically)
