# MailSense — Test Plan and Acceptance Checklist

**Version:** 1.1 · **Date:** 2026-11-19
**Status:** Gates 1–5 verified. Domain, API and UI suites have execution evidence; MSE-601 consolidates T01–T08 release acceptance, followed by privacy/offline/performance checks.
**Scope:** React/Vite, FastAPI, SpamAssassin ingestion, probability/statistics, Multinomial NB and Bernoulli NB.

## 1. Test philosophy

Prioritize mathematical correctness, scientific reproducibility and honest failure handling over superficial UI polish. Treat two independent types of data separately:

- **Synthetic, known-answer fixtures:** Small constructed datasets with exactly checkable results.
- **Actual SpamAssassin corpus:** Real historical email inputs whose retained record counts and model accuracy must be **measured after preprocessing**; never substitute synthetic numbers.

Testing framework proposal: `pytest`, FastAPI `TestClient`, React Testing Library with Vitest, and optional Playwright for one end-to-end smoke path. No heavy infrastructure or cloud test services required.

## 2. Critical release-blocking scenarios

| Test ID | Scenario | Action / input | Expected result | FR/NFR |
|---|---|---|---|---|
| T01 | Corpus ingestion provenance | Prepare chosen archives with known fixture messages and a malformed email | Correct label, source manifest, accepted/rejected counts; never crash or execute content | FR01–03, NFR08 |
| T02 | Duplicate and split isolation | Include duplicate text across source groups, then run split twice | Duplicates removed before split; train/test disjoint; fixed seed yields identical membership | FR03–04, NFR05 |
| T03 | Descriptive math | Fixture token counts `[2,4,4,6]` | Mean=4; median=4; mode=4; sample variance=8/3; sample SD≈1.63299 | FR06, NFR10 |
| T04 | Conditional/Bayes probability | Synthetic 2×2 table 180,120,70,630 | `P(spam)=0.3`, `P(word)=0.25`, `P(spam|word)=0.72`, correct denominators | FR08–09 |
| T05 | Chi-square and interval | Same table, 95% Wilson for 300/1000 | Pearson χ²=280, df=1, p≈7.50924e-63; Wilson interval approximately [0.2724, 0.3291] | FR11–12 |
| T06 | Shared two-model evaluation | Train both on tiny fixture / full corpus once prepared | Shared train-only vocabulary and test ID hash; metrics reconcile with confusion matrices | FR13–15, FR18, NFR05 |
| T07 | Valid and invalid detection | Send nonempty text, blank text and over-50k input | Both model results on valid text; `422` for invalid text; never store pasted bodies | FR16–17, FR20, NFR06–07 |
| T08 | Backend/model failure | Stop FastAPI, then remove test model artifact in separate staging environment | UI shows retry/unavailable; dataset modules usable when models missing; no fake success | FR20, NFR08 |

**Pass rule:** All T01–T08 must be run successfully for project acceptance; checks are not marked passed in advance.

## 3. Additional numerical and edge-case tests

| Test ID | Input | Expected result |
|---|---|---|
| T09 | `word` absent from every document | Zero presence counts; `P(spam|word)=null` with explanation; no divide-by-zero |
| T10 | `word` repeated 10 times within one spam email | Word document frequency increments by 1; token frequency may increment by 10 |
| T11 | `successes=11, trials=10` | Request rejected `422`; descriptive validation shown |
| T12 | `p=.25, n=10, k=1` binomial | PMF≈0.187711, explicit independence assumption |
| T13 | Table with expected count <5 | Chi-square assumptions warning; no automatic reject-null decision |
| T14 | Sample of one email | Sample variance and SD reported undefined rather than 0 |
| T15 | Corpus source folder incorrectly named | Import fails or rejects file with clear source-label error, rather than assigning arbitrary label |
| T16 | MIME with HTML, invalid encoding and attachment | Safe readable text or recorded skip; no script execution or remote fetch |
| T17 | Dataset empty or missing | Readiness `degraded`; dataset endpoints `503`, no fabricated graphs |
| T18 | Model metadata split ID differs from vectorizer | Inference/evaluation blocked with `503` |
| T19 | Token only in test records | Token not added during train vocabulary fitting; test transform handles unknown safely |
| T20 | Valid input with no recognized tokens | Returns defined model behavior plus warning; does not invent token explanation |
| T21 | Two rapid changing word requests | Stale earlier response never overwrites later selected word |
| T22 | Metrics fixture TP=50,FN=10,FP=5,TN=135 | Accuracy .925, precision≈.90909, recall≈.83333, F1≈.86957, FPR≈.03571 |
| T23 | Word explanation output | Multinomial log-odds direction matches learned token weights; Bernoulli includes absent-feature contribution in full score |
| T24 | Large but allowed 50,000-character text | No unbounded memory/processing, predicted or safe bounded error |
| T25 | Source archive with path traversal member | Unsafe member rejected; no file written outside staging directory |
| T26 | Direct URL navigation/refresh to `/statistics` | App route renders correctly without login or 404 from dev server |
| T27 | Network disconnected after setup | Local app and inference function without public internet |
| T28 | Screen reader/keyboard smoke | Labels visible, form reachable via keyboard; non-color cue identifies spam/ham |

## 4. API contract tests

| API | Positive assertion | Negative assertion |
|---|---|---|
| `GET /health` | Readiness booleans accurately match artifacts | Incomplete readiness is `degraded`, not a fake `ready` |
| `GET /dataset/summary` | Class count sum equals total | Invalid scope → `422`; missing data → `503` |
| `GET /dataset/statistics` | Known mean/variance agree | Wrong metric → `422` |
| `GET /dataset/distributions` | Bins and counts reconcile | `top_n=0` → `422` |
| `GET /probability/word` | All 2×2 and rate denominators reconcile | Blank/invalid token → `422` |
| `GET /probability/distributions` | PMF matches known formula | Negative/out-of-range trials → `422` |
| `POST /statistics/hypothesis-test` | χ², p, expected cells match synthetic fixture | Invalid alpha → `422` |
| `GET /statistics/confidence-interval` | Wilson interval matches independent result | Confidence outside allowed range → `422` |
| `POST /predict` | Both labels, valid probability bounds, explanations | Blank/overlimit → `422`; missing artifact → `503` |
| `GET /models/metrics` | Confusion matrix sums to test count | Missing/invalid model → `422` or `503` |
| `GET /models/comparison` | Both models share split ID and test hash | Inconsistent artifacts → `503` |
| `GET /models/explanations` | Training-derived token effect; absent word → null weight | Invalid model/token → `422` |

## 5. Model evaluation integrity checklist

- [ ] The two models are trained with the same retained dataset.
- [ ] Exact duplicate texts were removed before split.
- [ ] The `train` and `test` message ID sets do not overlap.
- [ ] The tokenizer/vocabulary was fitted using training messages only.
- [ ] Both models use alpha=1.0 and the same training/test IDs.
- [ ] Evaluation uses no test-derived tuning or feature selection.
- [ ] Both models report TP, TN, FP and FN with spam as positive class.
- [ ] Reported metrics equal independent confusion-matrix arithmetic.
- [ ] Probability outputs are labeled estimates, not calibrated certainties.
- [ ] Failing and disagreement examples are discussed in the report.

## 6. Non-functional verification

| Requirement | Check |
|---|---|
| Local-only | API listens on 127.0.0.1 by default; frontend local; no public bind |
| Offline | Disconnect internet after installation; dashboard, statistics, prediction still work |
| Privacy | No email body logs, storage, telemetry or URL query parameters |
| Request limits | 50k-character ceiling; predictable error envelope |
| Performance | 30 warmed-up single-email requests; document p95 time and hardware; target ≤3 seconds |
| Chart labels | Each chart specifies dataset scope, class, units and axis meaning |
| Accessibility | Keyboard navigation and clearly labeled form controls |
| Determinism | Repeat preprocessing + training in same pinned environment; compare manifests and results |
| Artifact safety | Only trusted local joblib files load; metadata and checksums verified |

## 7. Manual university demonstration acceptance

1. Start the two local processes and show backend `ready`.
2. Explore spam/ham class proportions and two descriptive distributions.
3. Check a manually computed mean, variance and quartile example.
4. Select `free`, show its empirical 2×2 table, Bayes' theorem, and Bernoulli/binomial explanation.
5. Run Pearson chi-square, inspect expected counts, assumptions and a Wilson 95% confidence interval.
6. Paste an example email; obtain Multinomial and Bernoulli predictions and model-faithful explanations.
7. Compare the classifiers on identical test IDs and interpret false positives/negatives.
8. Demonstrate empty text rejection and loss-of-backend recovery.
9. Explain corpus age, lack of random sampling and non-calibrated model probabilities.

## 8. Defect triage and exit criteria

- **Blocker:** wrong probability denominator, train/test leakage, classifier missing, contradictory artifacts, fabricated results or unsafe extraction.
- **High:** incorrect metric arithmetic, broken key page, missing handling for corpus/model failure, email content inadvertently persisted/transmitted.
- **Medium:** confusing wording, inaccurate chart labels, minor responsive layout defect.
- **Low:** nonessential aesthetics.

**Release exit:** No open blockers or high-severity defects; every critical scenario T01–T08 and core walkthrough passes on the designated demo machine. Unsupported and untested behaviors must be documented, never reported as passing.

## 9. Test execution log template

| Test ID | Date | Environment/commit | Expected | Actual | Pass/Fail | Evidence |
|---|---|---|---|---|---|---|
| T01 | Not run | N/A | See §2 | Not measured | Not run | — |
| T02 | 2026-11-19 | Python 3.12.15, MSE-106 | See §2 | Duplicates/conflicts removed; repeated membership identical; IDs/content isolated | Pass | `backend/tests/test_corpus_split.py::test_t02_end_to_end_duplicate_conflict_removal_split_isolation_and_repeatability`; actual 4,689/1,173 membership independently reconciled |
| T03 | 2026-11-19 | Python 3.12.15, MSE-201 | See §2 | Mean/median/mode=4; sample variance=8/3; SD=sqrt(8/3) | Pass | `backend/tests/test_descriptive.py::test_t03_known_descriptive_fixture` |
| T04 | 2026-11-19 | MSE-203 | See §2 | .3/.25/.18/.6/.72 with visible denominators | Pass | `backend/tests/test_probability.py::test_t04_known_thousand_document_table_and_bayes` |
| T05 | 2026-11-19 | MSE-207 | See §2 | Pearson 280/df1/reference p; Wilson bounds round to .2724/.3291 | Pass | `test_numerical_verification.py` and `artifacts/reports/statistics_verification.json` |
| T06 | 2026-11-19 | MSE-305 | See §2 | Shared training-only vocabulary and test hash; both confusion matrices reconcile | Pass | `test_model_features.py`, `test_evaluation.py`, `artifacts/reports/evaluation.json` |
| T07 | Not run | N/A | See §2 | Not measured | Not run | — |
| T08 | Not run | N/A | See §2 | Not measured | Not run | — |

Tests may be marked passed **only** after actual execution. Rows marked Pass have observed domain-service and/or actual-corpus evidence.
Rows still marked Not run remain unexecuted as full release scenarios even where individual foundation unit tests cover parts of
their requirements; dependency compatibility tests do not prove domain math.
