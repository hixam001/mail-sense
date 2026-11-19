# Independent mathematical and artifact verification

MSE-603 passed the [independent verifier](../backend/scripts/verify_science.py)
against the actual frozen inputs. Its [aggregate result](../artifacts/reports/reproducibility.json)
contains no original email text or vocabulary listing. The only message included
is explicitly authored synthetic teaching text.

## Hand-checkable examples

For `[2,4,4,6]`, the sum is 16, mean/median/mode are 4, and the sum of squared
deviations is 8. Sample variance is `8/(4−1) = 8/3`; sample standard deviation is
`sqrt(8/3) = 1.632993161855452`. Linear interpolation at indices 0.75 and 2.25
gives Q1=3.5 and Q3=4.5.

The synthetic contingency table is:

| Class | Word present | Word absent | Total |
|---|---:|---:|---:|
| Spam | 180 | 120 | 300 |
| Ham | 70 | 630 | 700 |
| Total | 250 | 750 | 1,000 |

`P(spam)=300/1000=.3`; `P(word)=250/1000=.25`;
`P(word|spam)=180/300=.6`. Bayes gives `.6 × .3 / .25 = .72`,
the same as `180/250`.

Under independence the expected cells are `[75,225;175,525]`. Pearson's four
`(O−E)²/E` terms are `147+49+63+21=280`, with one degree of freedom and no
Yates correction. An independent normal-tail identity,
`erfc(sqrt(280/2))`, gives `7.509242653735255e−63`, agreeing with the SciPy
report within relative tolerance `1e−12`.

For Wilson's 95% interval at 300/1000, the verifier finds the normal critical
value by bisection of `erf`, independently of the service's inverse-normal call.
It obtains `z=1.9599639845400536`. With `d=1+z²/n`, the center is
`(.3+z²/(2n))/d` and the half-width is
`z sqrt(.3×.7/n+z²/(4n²))/d`. Bounds are
`[.2724068424770048, .3291238609172172]`.

For the binomial teaching example, `C(10,1) .25 .75⁹ = .1877117156982422`.
Independence and constant success probability are modeling assumptions.
For TN=135, FP=5, FN=10, TP=50, direct confusion arithmetic gives accuracy .925,
precision .9090909, recall .8333333, F1 .8695652 and FPR .0357143.

## Actual corpus and models

- All five canonical archive byte hashes/sizes match the public source manifest.
  Accepted/rejected source counts reconcile with the deduplication report.
- Every retained text hash, character count, token count, source group and label
  reconciles. The 5,862 retained content hashes are unique: 4,107 ham and 1,755 spam.
  The recorded 5,992 parsed inputs minus 130 duplicate exclusions and zero
  conflicting-label exclusions equals retention. The complete pipeline verifier
  also rederives the exclusion mapping; this independent check verifies retained
  uniqueness and accounting.
- Recomputing the seed-42 stratified split reproduces 4,689/1,173 membership,
  exact ID hashes and disjoint IDs/content between partitions.
- A separately wired CountVectorizer fits only training rows. Its 60,135 words,
  indices and vocabulary hash match the saved vectorizer. All 12,200 held-out-only
  tokens remain excluded.
- Separate in-memory Multinomial/Bernoulli fits use alpha=1, learned training
  priors and explicit binary presence for Bernoulli. All class counts, class log
  priors, feature counts and feature log-probability arrays are exactly equal to
  the stored models. This uses the same pinned estimator library, not a second
  implementation of scikit-learn itself.
- Held-out predictions and independently counted confusion matrices/rates match
  the evaluation report. Stored model, vectorizer, metadata and CSV bytes remain
  unchanged. No test-derived tuning occurs.
- Direct document-presence counting for `free` matches the statistical report in
  all/train/test scopes. Original corpus text is never included in this report.

## An honest disagreement example

The authored project-meeting text in the report is intended as ham. Multinomial
labels it spam with estimated P(spam)=.6385533772800012; Bernoulli labels it ham
with estimated P(spam)=1.6701648472268352e−12. This example exposes a false alarm
relative to the authored intent and disagreement between the assumptions. It is
not a corpus record and is excluded from held-out metrics. It illustrates why
the estimates are not calibrated certainty and why accuracy is not a guarantee
for an individual message.

## Reproduce and checklist

```bash
uv run --directory backend --frozen python -m scripts.verify_science run
uv run --directory backend --frozen python -m scripts.verify_science verify
```

Both commands recompute the checks and fit reference models in memory. `run`
writes the public aggregate report; `verify` compares with it. Hashes are checked
before loading the trusted local joblib bytes. The verifier does not call the
application's statistical, feature-fitting, training or metric service functions.

- [x] Hand examples and numerical report agree.
- [x] Canonical archive provenance and retained/excluded counts reconcile.
- [x] ID/content isolation and deterministic membership reproduce.
- [x] Training-only vocabulary excludes held-out-only tokens.
- [x] Both saved models match independent wiring of the approved fixed fit.
- [x] Positive class and every confusion-derived metric reconcile.
- [x] Authored failure/disagreement is discussed separately from held-out scores.
- [x] No private source text or model artifacts are redistributed.

The full [test checklist](TEST_PLAN.md) and [model card](MODEL_CARD.md) document
the same split and limitations. Historical curation, near duplicates, sampling
dependence and uncalibrated estimates remain limitations, not failed arithmetic.
