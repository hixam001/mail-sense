# MailSense model card

Measured historical fixed-split evaluation; no production or calibration claim.

## Data and experimental boundary

Five canonical SpamAssassin archives yield 6,046 candidates, 5,992 parsed rows and 5,862 retained exact-text records. Fifty-four malformed-MIME candidates and 130 duplicate rows are excluded; no conflicting labels were observed. The retained corpus contains 4,107 ham and 1,755 spam records.

The seed-42 stratified split has 4,689 train (3,285 ham, 1,404 spam) and 1,173 test (822 ham, 351 spam). One 60,135-feature CountVectorizer is fitted only on training text using unicode-word-v1. Both models use alpha=1 and empirical class priors. Multinomial consumes counts; Bernoulli consumes binary presence and includes absent features.

Dataset ID: `ccd3321b252f22aaa5e6e1e74d96140b46c088a15474e8607c6259b2467c9c7a`.
Split ID: `e10ea9f8b406c62d14a359dd864ef2a195c8c1960c2747f1feaaea313c148c31`.
Test IDs SHA-256: `64aef20395f55f37509281df5bf20a90846bf0e7b8b1a4842013df44b02a2629`.
Artifact ID: `747bb5f51c2d231140efcc17d1316be68407d07fa9f9a7adcca1b3df2ce01ca3`.
Vocabulary SHA-256: `f7ba4c18eef3aa09cacedf7f2518f4c97431a56d2f06c7f9c0c08a5af4402937`.

## Measured results

| Model | TN | FP | FN | TP | Accuracy | Precision | Recall | F1 | FPR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| multinomial | 814 | 8 | 14 | 337 | 0.981245 | 0.976812 | 0.960114 | 0.968391 | 0.009732 |
| bernoulli | 815 | 7 | 70 | 281 | 0.934356 | 0.975694 | 0.800570 | 0.879499 | 0.008516 |

Spam is positive. Rates are proportions, not percentages. Both models share the exact test-ID hash above. Metrics reconcile with confusion counts and independent sklearn calculations. No hyperparameters or vocabulary were selected using held-out results. The complete machine-readable values are in [evaluation.json](../artifacts/reports/evaluation.json).

Multinomial misses 14 spam messages and flags 8 ham messages; Bernoulli misses 70 spam and flags 7 ham. This is a measured tradeoff on one fixed split, not a universal winner or modern inbox guarantee.

## Inference and explanations

Input is transient subject/body text, 1–50,000 trimmed characters. It is never persisted or logged by the prediction service. Responses contain counts and results, not echoed text. Unknown vocabulary produces a warning and no invented token explanation. Class-column lookup determines the spam probability.

Explanations are signed log posterior odds, not probability contributions or causal effects. Multinomial weights include token counts. Bernoulli explanations combine present-word terms, all absent-vocabulary terms, and class priors. A remainder preserves exact decomposition when only the strongest terms are shown.

## Limitations and intended use

- Historical curated corpus, not a random sample of present-day email. Class prevalence, intervals and scores are conditional on this dataset.
- Exact-content deduplication does not remove near duplicates, shared threads or residual dependence. Same-corpus train/test performance is not out-of-distribution robustness.
- Naive conditional-independence assumptions are approximations. predict_proba estimates can be overconfident; calibration is not established.
- Strict MIME parsing excludes partly readable messages. Attachments and remote resources are ignored; no claim is made about modern phishing or attachment malware.
- One fixed holdout is not a variance estimate or cross-validation study. Evaluation was not used for tuning.
- False positives can hide legitimate mail. This university demonstration has no live mail integration, sending, quarantine, accounts or production deployment.
- Only trusted project-created local joblib artifacts are supported. Checksums detect corruption and mismatches; they do not authenticate arbitrary pickle files.

## Reproduce

After the documented environment and corpus preparation:

```bash
uv run --directory backend --frozen python -m scripts.train_models run
uv run --directory backend --frozen python -m scripts.train_models verify
uv run --directory backend --frozen python -m scripts.evaluate_models run
uv run --directory backend --frozen python -m scripts.evaluate_models verify
```

Model/vectorizer/metadata files stay private and ignored. Evaluation and this card contain aggregates and hashes only. Gate 3 is verified in Python without the API or frontend; later gates cover those integrations.
