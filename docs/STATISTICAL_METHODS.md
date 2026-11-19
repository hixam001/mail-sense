# MailSense — Statistical and Probabilistic Methodology

**Version:** 1.2 · **Date:** 2026-11-19
**Purpose:** Academic formulas, assumptions, verifiable examples and reproducibility rules  
**Status:** Statistics engine and numerical verification implemented; Gate 2 complete. Models remain tracked in the handoff.

## 1. Statistical units and data definitions

**Observation:** One deduplicated, parsed email from the approved SpamAssassin corpus.  
**Response variable:** `Y=1` when spam and `Y=0` when ham.  
**Word-presence feature:** `X_w=1` when a normalized word appears at least once, otherwise 0.  
**Word count:** Number of tokenizer-produced tokens per email.  
**Character count:** Length of normalized subject/body text.  
**Population caveat:** The historical corpus is a curated collection, not a probability sample of modern-world emails. Intervals and p-values should be interpreted **conditional on assumptions and on this dataset design**.

All views label their subset (`all`, `train` or `test`). Only training records can fit ML features or models. Word analysis and inference may explore all records for pedagogy but should not drive post-hoc tuning against the test split.

### Canonical tokenization (`unicode-word-v1`)

Apply Python `str.lower()` to normalized `model_text`, then extract Unicode
word runs matching `(?u)\b\w\w+\b`: at least two letters/digits/underscore
characters. Punctuation separates tokens; single-character runs are excluded.
Keep repeated tokens for `token_count`/TF and take a set for document presence.
Use unigrams, no stop words, accent stripping, stemming or learned filtering.
For example, `FREE free e-mail foo_bar 42 I` yields
`[free, free, mail, foo_bar, 42]` (five tokens, four distinct tokens).
Case remains unchanged in stored text and exact-content deduplication.

This fixed rule matches the pinned CountVectorizer's default word analyzer;
tests compare tokens without calling `fit`. See the
[official CountVectorizer documentation](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html).
MSE-301 must reuse these parameters and fit its vocabulary only on training
records. Summary token counts require no corpus-fitted state or vocabulary.

## 2. Descriptive statistics

For a numeric sample `x1,...,xn`:

- Mean: `x̄ = (Σ xi)/n`.
- Median: central ordered value, or average of the two central values when `n` is even.
- Mode: most frequent exact value. When tied, report the smallest tied mode **and** `mode_tied=true`.
- Sample variance: `s² = Σ(xi − x̄)²/(n−1)` for `n >= 2`.
- Sample standard deviation: `s = sqrt(s²)`.
- Quartiles: 25th and 75th percentiles using an explicitly documented numeric interpolation convention (NumPy linear quantiles is the recommended consistent choice).
- IQR: `Q3 − Q1`.

Create frequency tables/histograms and box plots for text character counts and tokenizer token counts, stratified by spam vs ham. Label units and note that long-tailed distributions make mean and median different. When a class subset has fewer than two values, variance/standard deviation are undefined rather than zero.

## 3. Probability definitions

Let `S` mean spam and `W` mean that selected normalized word `w` occurs **at least once** in the email. On a dataset of `N` records:

| Symbol | Calculation | Interpretation |
|---|---|---|
| `P(S)` | `n(S)/N` | Prior spam fraction |
| `P(W)` | `n(W)/N` | Probability word present |
| `P(S ∩ W)` | `n(S ∩ W)/N` | Joint probability |
| `P(W | S)` | `n(S ∩ W)/n(S)` | Likelihood word appears given spam |
| `P(S | W)` | `n(S ∩ W)/n(W)` | Empirical posterior given word |

Bayes' theorem:

`P(S | W) = P(W | S) × P(S) / P(W)` whenever `P(W)>0`.

### 3.1 Verified synthetic teaching example

A **made-up** 1,000-email dataset contains:

| | Word present | Word absent | Row total |
|---|---:|---:|---:|
| Spam | 180 | 120 | 300 |
| Ham | 70 | 630 | 700 |
| Column total | 250 | 750 | 1000 |

From the table:

- `P(S) = 300/1000 = 0.30`
- `P(W) = 250/1000 = 0.25`
- `P(S ∩ W) = 180/1000 = 0.18`
- `P(W | S) = 180/300 = 0.60`
- `P(S | W) = 180/250 = 0.72`
- Bayes check: `(0.60×0.30)/0.25 = 0.72`.

This example proves the calculation method. **It is not a result observed in SpamAssassin.** The API/UI must calculate dataset-specific counts after ingestion. If `n(W)=0`, the empirical posterior is undefined; display `null` + explanation.

## 4. Bernoulli and binomial distributions

### Bernoulli feature

For one email, `X_w=1` if the word occurs, otherwise `0`. Treat `X_w ~ Bernoulli(p)` with empirical `p = n(W)/N` for illustration:

`P(X_w=x)=p^x (1−p)^(1−x), x∈{0,1}`.

Expected value `E[X_w]=p`; variance `Var(X_w)=p(1−p)`.

### Binomial count of emails containing the word

If `n` trials were **independent and identically distributed**, `K ~ Binomial(n,p)`:

`P(K=k) = C(n,k) p^k (1−p)^(n−k)` for `k=0,...,n`.

Example from the synthetic table: `p=0.25`, `n=10`, `k=1`. Then `P(K=1)=10×0.25×0.75^9≈0.187711`. These assumptions are an illustrative model, not proof of independence between emails from the real curated corpus.

## 5. Statistical inference

### 5.1 Pearson chi-square test for association

**Research question:** Is the chosen word's presence associated with spam/ham class?

- `H0`: word presence and email class are independent.
- `H1`: word presence and email class are associated.
- Significance level `α = 0.05` by default.
- Observed counts `Oij` are the 2×2 contingency table.
- Expected counts under independence: `Eij = (row_total_i×column_total_j)/N`.
- Statistic `χ² = ΣΣ (Oij−Eij)²/Eij`.
- Degrees of freedom for 2×2: `(2−1)(2−1)=1`.
- Use **Pearson chi-square without Yates continuity correction** for reproducibility; report this choice.

For the synthetic example, the expected table is:

| | Word present | Word absent |
|---|---:|---:|
| Spam | 75 | 225 |
| Ham | 175 | 525 |

The exact Pearson statistic is `χ²=280.0`, df `1`, with p-value approximately `7.50924×10⁻⁶³`. At α=0.05, reject H0 **for that synthetic table**. This indicates an association under the test assumptions, **not causation**.

**Assumptions and warnings:** independent observations; expected counts sufficiently large for chi-square approximation (for v1.0, warn if any expected count `<5` or any expected count is zero). If unsuitable, show the observed table and a warning; return no automatic reject/retain conclusion. Duplicates should have been removed before analysis; remaining dependency or selection effects may still exist.

### 5.2 Confidence interval for spam proportion

For `x` spam emails in `n` observations, `p̂ = x/n`. Use two-sided **Wilson score interval** (default 95%) rather than a Wald interval:

Let `z` be the standard normal quantile for `(1+confidence)/2` and `d=1+z²/n`.

`center = (p̂ + z²/(2n))/d`

`halfwidth = [z/d] × sqrt( p̂(1−p̂)/n + z²/(4n²) )`

`CI = [center−halfwidth, center+halfwidth]`.

For the synthetic example `x=300`, `n=1000`, `p̂=0.30` and `confidence=0.95`, the interval is approximately `[0.2724,0.3291]` (rounding dependent). **Interpretation limitation:** Because the corpus is curated historical data rather than a random sample of present-day emails, treat this as an educational uncertainty calculation, not a reliable prevalence estimate for today's email traffic.

## 6. From probability theory to supervised machine learning

### 6.1 Shared text features

Fit a single `CountVectorizer` vocabulary on the training set only (unigrams, documented tokenization). Hold the vocabulary fixed when transforming test or pasted user text.

- **Multinomial NB:** feature `xj` is count of token `j` in the email.
- **Bernoulli NB:** feature `bj=1[xj>0]` is presence/absence of token `j`.

Two models use the same 80/20 stratified split, random seed 42, initial Laplace parameter `α=1.0`, and are evaluated on identical test IDs.

The implemented `stratified-v1` split sorts verified retained IDs before
calling the pinned
[sklearn split function](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html)
with `test_size=0.2`, `random_state=42`, `stratify=labels` and `shuffle=True`.
Test size rounds up, train is the complement and integer class allocation is
recorded explicitly. Observed membership is 4,689 train (3,285 ham, 1,404 spam)
and 1,173 test (822 ham, 351 spam). Sorted ID lists, membership hashes and full
runtime/configuration are frozen in the split manifest; no vocabulary has been
fitted. Training code must consume only the verified `train` scope. Exact-text
isolation does not prove independence or eliminate near-duplicate content.

### 6.2 Multinomial Naive Bayes

The score for class `c` is proportional to:

`log P(c) + Σj xj log P(token_j | c)`.

With Laplace smoothing and vocabulary size `V`, token likelihood:

`P(token_j | c) = (count(token_j in class c training texts) + α) / (total training token count in c + αV)`.

Naive conditional-independence assumptions and model-specific generative assumptions are approximations. The output of `predict_proba` is a model estimate, **not** an empirically calibrated certainty.

### 6.3 Bernoulli Naive Bayes

The score for class `c` is proportional to:

`log P(c) + Σj [ bj log θjc + (1−bj) log(1−θjc) ]`,

where `θjc = (training emails in class c containing token_j + α)/(training emails in c + 2α)`.

**Important:** Bernoulli NB uses both present and **absent** features. An explanation that merely lists present words without disclosing absent contributions would be incomplete. Model explanation is based on signed log-posterior-odds contributions, including prior odds and—where appropriate—absent-token contributions.

### 6.4 Comparison caveats

- Same held-out set and source corpus is necessary for fair comparison.
- Model scores may be overconfident and are not necessarily calibrated posterior probabilities.
- Explain disagreements; do not silently choose one 'winner' by a hidden rule.
- Models may excel on different metrics; especially discuss false-positive rate because ham mistaken for spam is consequential.
- Train/test on the same historical corpus is **not** evidence of modern out-of-distribution robustness.

## 7. Performance metrics

With `spam` as positive:

| Actual / Predicted | Predicted spam | Predicted ham |
|---|---:|---:|
| Actual spam | TP | FN |
| Actual ham | FP | TN |

- `Accuracy = (TP+TN)/(TP+TN+FP+FN)`.
- `Precision = TP/(TP+FP)`.
- `Recall = TP/(TP+FN)`.
- `F1 = 2×Precision×Recall/(Precision+Recall)` or `2TP/(2TP+FP+FN)`.
- `False positive rate = FP/(FP+TN)`.

Define `zero_division_policy` explicitly. Recommended: return `null` plus a note if the mathematical denominator is zero in manual reporting; do not silently assume a favorable score. Scikit-learn can be configured consistently for automated comparisons.

### Illustrative, internally consistent evaluation table

A **synthetic** 200-email test set yields `TP=50, FN=10, FP=5, TN=135`:

- Accuracy `185/200 = 0.925`.
- Precision `50/55 ≈ 0.90909`.
- Recall `50/60 ≈ 0.83333`.
- F1 `100/115 ≈ 0.86957`.
- FPR `5/140 ≈ 0.03571`.

These numbers are for testing math and UI structure, **not observed SpamAssassin results**.

## 8. Model integrity and leakage audit

- Deduplicate before splitting to prevent identical text in train/test.
- Remove label-derived header fields, paths and archive names from predictors.
- Fit vocabulary, token filters and any learnable normalization on `train` only.
- Avoid tuning hyperparameters after inspecting final test metrics; if tuning is needed in the future, carve validation from training.
- Confirm both trained models and evaluations share `dataset_id`, `split_id`, test ID hash and positive label.
- Persist Python/sklearn versions, `alpha`, seed and preprocessing config.
- Never claim guaranteed accuracy or probability calibration from a small historical test sample.

## 9. Manual verification checklist

Before presenting, calculate by hand or independent script:
1. Mean and sample standard deviation of one small numeric list.
2. Q1, median, Q3 of a list with stated interpolation convention.
3. A 2×2 word-frequency table with all denominators and empirical Bayes posterior.
4. Pearson expected counts, χ² and interpretation.
5. Wilson confidence interval for known `(x,n)`.
6. Confusion-matrix accuracy, precision, recall, F1 and FPR.

Record the inputs and observed outputs in the test report. Do not mark any check complete before actual execution.

## 10. References

- Apache SpamAssassin public corpus: `https://spamassassin.apache.org/old/publiccorpus/`
- Corpus notes and reuse warning: `https://spamassassin.apache.org/old/publiccorpus/readme.html`
- Method implementation reference: NumPy, SciPy and scikit-learn official documentation (pin package versions in project environment when implementation begins).

## Executed implementation evidence

- MSE-201: Pure descriptive service passes `[2,4,4,6]`: mean/median/mode 4, Q1 3.5, Q3 4.5, sample variance 8/3 and SD sqrt(8/3). Uses linear interpolation, smallest tied mode with `mode_tied`, and null empty/singleton sample dispersion with notes. 181 tests passed; actual scope/class means and variances matched independent stdlib calculations.

- MSE-202: Numeric distributions use ten equal-width bins (one bin for constant data), left-closed/right-open except the inclusive final bin. Boxplots show the five-number summary with linear quartiles. Top words are document frequency with alphabetical ties; repeated occurrences count once per email. 191 tests passed and actual counts reconciled across all scope/class combinations.

- MSE-203: Empirical service verifies the synthetic 1000-document Bayes table (.3/.25/.18/.6/.72) and every numerator/denominator. Query words trim, NFC-normalize and lowercase, then must match one complete canonical token (punctuation/multiple tokens are rejected). Empty denominators return null with notes. Actual `free` presence: spam 811/1755, ham 577/4107; these are measured corpus counts, separate from the teaching fixture. 201 tests passed.

- MSE-204: Bernoulli probabilities/moments and binomial PMF are implemented with integer trials 1–100 and successes 0–trials. The .25/10/1 fixture gives .1877117156982422; endpoints and total probability mass match independent [SciPy binomial calculations](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binom.html). 221 tests passed; actual scoped p values match the direct combination formula. Independence is an assumption, not a corpus finding.

- MSE-205: Pearson service uses rows spam/ham, columns present/absent, no continuity correction. The synthetic table yields 280, df 1, p≈7.50924e-63; independent [SciPy contingency reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2_contingency.html) agrees. Any expected cell below 5 prevents an automatic conclusion; zero margins yield null statistic/p-value. Independence remains assumed and association is not causation. 240 tests passed. Actual `free` chi-square is 703.7827464379106 for all retained records.

- MSE-206: Two-sided Wilson score intervals use a normal quantile and confidence .80–.99. Known 300/1000 bounds round to [.2724,.3291]; zero/all successes and empty samples are covered. Actual retained spam fraction has 95% bounds [.2877962371144159,.3112382719988152]. This describes the curated historical dataset under assumptions, not modern prevalence. 264 tests passed.

- MSE-207 / Gate 2: `uv run --directory backend --frozen python -m scripts.verify_statistics run` writes [reproducible verification evidence](../artifacts/reports/statistics_verification.json). Thirteen golden-value checks cover the descriptive list, the 1000-message Bayes/binomial table, Pearson expected counts/statistic/tail and Wilson bounds. Tiny p-values use relative tolerance without a permissive absolute tolerance. Synthetic examples and measured corpus scopes are separate, with input/dataset/split identities. `verify` rederives the report and rejects staleness. 267 tests passed; statistics run without models/UI. Confusion-matrix verification follows model implementation.
