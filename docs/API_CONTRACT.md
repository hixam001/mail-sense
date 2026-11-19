# MailSense — REST API Contract

**Version:** 1.1 · **Date:** 2026-11-19 · **Status:** A01–A12 and shared safe errors implemented; local transport hardening implemented; cross-route contract suite follows
**Base URL:** `http://127.0.0.1:8000/api/v1`  
**Frontend:** `http://localhost:5173` (allowed local origin; adjust via configuration if necessary)  
**Access:** Local-only; no login or API tokens

## 1. Global conventions

- JSON encoded as UTF-8; `Content-Type: application/json` for request bodies.
- All timestamps use ISO-8601 UTC (e.g. `2026-11-19T06:00:00Z`).
- Class label enum: `spam`, `ham`. Positive class is `spam`.
- Scope enum: `all`, `train`, `test`, default `all` for analytical endpoints. The trained models are fitted **only on `train`**.
- Probability values are numbers from 0 to 1; when undefined, return `null` with an explanatory note.
- No pagination is required for aggregate endpoints; no endpoint returns a full raw-email dump.
- Empty statistical subset or missing model/dataset returns a structured error rather than invented numbers.
- Pasted email text is processed in memory and never intentionally persisted by this API.
- Server inputs are validated with Pydantic. FastAPI's validation errors should be normalized into the shared error envelope.

### Standard error envelope
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Provide nonempty email text.",
    "details": {"field": "text"}
  }
}
```

| Status | Meaning |
|---|---|
| `200` | Successful read or computation |
| `400` | Semantically invalid request (e.g. unrecognized scope) if not caught by validation |
| `404` | Requested supported resource or word result not found, where relevant |
| `422` | Field/type/length validation failure |
| `503` | Required dataset/model not ready or backend dependency unavailable |
| `500` | Unexpected processing failure; no stack trace in response |

**Do not return `401` or `403` for missing authentication**: MailSense has no authentication in v1.0. Bind server to loopback and configure CORS accordingly. CORS is not authorization.

## 2. Endpoints

### A01 — `GET /health`
**Purpose:** Return readiness without accessing sensitive email text.  
**Auth:** None (loopback server).  
**Request:** No parameters.

**200 example:**
```json
{
  "status": "ready",
  "dataset_ready": true,
  "models_ready": {"multinomial": true, "bernoulli": true},
  "evaluation_ready": true,
  "split_id": "split_seed42_80_20_example"
}
```
MSE-401 implements this route using verified content-hash-invalidated snapshots. Model flags indicate a usable consistent bundle, not file presence. Missing/stale evaluation also degrades readiness; dataset analytics remain available when only models are missing. The split ID is illustrative. If the dataset or a model is missing, return `200` with `status: "degraded"` and readiness flags `false`; affected analytics/prediction endpoints return `503`.

### A02 — `GET /dataset/summary`
**Purpose:** Dataset counts and corpus provenance.  
**Query:** `scope=all|train|test` (default `all`).  
**200 example:**
```json
{
  "scope": "all",
  "dataset_id": "corpus_sha256_example",
  "split_id": "split_seed42_80_20_example",
  "total": 1000,
  "class_counts": {"spam": 300, "ham": 700},
  "class_proportions": {"spam": 0.3, "ham": 0.7},
  "source_groups": {"easy_ham": 650, "hard_ham": 50, "spam": 300},
  "excluded_count": 12,
  "duplicate_count": 6
}
```
MSE-402 implements A02–A04 with typed aggregate responses over verified cached rows. Summary source groups and class proportions use the selected scope. `excluded_count`, `duplicate_count`, `parse_rejected_count` and `label_conflict_count` describe the global source corpus before splitting (`exclusion_scope: source_corpus_before_split`); exclusions have no train/test assignment. `source_archives` contains public canonical acquisition metadata only. Numeric distributions disclose bin closure and units; word items are document frequencies.

**Errors:** `422` bad scope; `503` dataset missing. Example counts are **synthetic**, not SpamAssassin measurements.

### A03 — `GET /dataset/statistics`
**Purpose:** Descriptive statistics by class.  
**Query:** `scope=all|train|test`, `metric=character_count|token_count`.  
**200 example:**
```json
{
  "scope": "all",
  "metric": "token_count",
  "unit": "tokens/email",
  "groups": {
    "spam": {"n": 300, "mean": 125.4, "median": 95, "mode": 85, "q1": 52, "q3": 170, "sample_variance": 4200.0, "sample_std": 64.81},
    "ham": {"n": 700, "mean": 90.2, "median": 73, "mode": 54, "q1": 36, "q3": 128, "sample_variance": 2900.0, "sample_std": 53.85}
  }
}
```
**Rule:** For tied modes, return the smallest mode and `mode_tied: true` (document this choice); for `n < 2`, sample variance/std are `null` with note.  
**Errors:** `422`, `503`. Values shown are illustrative.

### A04 — `GET /dataset/distributions`
**Purpose:** Chart-ready histogram/box-plot/top-word aggregates, not raw messages.  
**Query:** `scope` (default `all`), `metric=character_count|token_count|top_words` (required), `class_label=all|spam|ham` (default `all`), `top_n` integer 1–30 (default 15, used for top_words).  
**200 example:**
```json
{
  "scope": "all",
  "metric": "top_words",
  "class_label": "spam",
  "frequency_type": "document_frequency",
  "items": [{"word": "free", "count": 180}, {"word": "offer", "count": 142}],
  "bins": [],
  "boxplot": null
}
```
For numeric metrics `bins` holds `{lower,upper,count}` objects and `boxplot` holds `{min,q1,median,q3,max}`; `items` is empty. Top words are document frequencies by default (a word counted once per email).  
**Errors:** `422`, `503`.

### A05 — `GET /probability/word`
**Purpose:** Empirical 2×2 table and probability calculations for one normalized token.  
**Query:** `word` required, 1–64 characters normalized to exactly one token; `scope=all|train|test` default `all`.

**200 example (synthetic 1,000-email teaching table):**
```json
{
  "word": "free",
  "scope": "all",
  "total": 1000,
  "counts": {
    "spam_present": 180,
    "spam_absent": 120,
    "ham_present": 70,
    "ham_absent": 630
  },
  "probabilities": {
    "p_spam": {"numerator": 300, "denominator": 1000, "value": 0.3},
    "p_word": {"numerator": 250, "denominator": 1000, "value": 0.25},
    "p_spam_and_word": {"numerator": 180, "denominator": 1000, "value": 0.18},
    "p_word_given_spam": {"numerator": 180, "denominator": 300, "value": 0.6},
    "p_spam_given_word": {"numerator": 180, "denominator": 250, "value": 0.72}
  },
  "notes": []
}
```
**Rule:** If `spam_present+ham_present=0`, `p_spam_given_word.value` is `null`; return `200` with clear note `Word not observed in selected subset`. Never return a fabricated 0 posterior.  
**Errors:** `422` invalid word/scope; `503` data unavailable.

### A06 — `GET /probability/distributions`
**Purpose:** Teach Bernoulli/binomial calculations for observed probability of a token.  
**Query:** `word` (1–64 characters), `scope` (default `all`), `trials` integer 1–100 (default 10), `successes` integer 0–trials (default 1).  
**200 example:**
```json
{
  "word": "free",
  "scope": "all",
  "bernoulli_p": 0.25,
  "trials": 10,
  "successes": 1,
  "binomial_pmf": 0.187711,
  "assumptions": ["The repeated trials are modeled as independent with constant p."]
}
```
**Errors:** `422` invalid trial parameters; `503` dataset missing. The output is a mathematical demonstration, not a claim that real emails are independent.

### A07 — `POST /statistics/hypothesis-test`
**Purpose:** Pearson chi-square independence test for chosen word presence against spam/ham.  
**Auth:** None.  
**Request:**
```json
{"word":"free","scope":"all","alpha":0.05}
```
**200 example:**
```json
{
  "word": "free",
  "scope": "all",
  "test": "pearson_chi_square_independence",
  "null_hypothesis": "Word presence and email class are independent.",
  "alternative_hypothesis": "Word presence and email class are associated.",
  "observed": [[180,120],[70,630]],
  "expected": [[75,225],[175,525]],
  "chi_square": 280.0,
  "degrees_of_freedom": 1,
  "p_value": 7.50924e-63,
  "alpha": 0.05,
  "assumptions_satisfied": true,
  "warnings": [],
  "reject_null": true
}
```
**IMPORTANT:** The displayed chi-square and p-value are computed from the **synthetic** teaching table; they are not measurements from the SpamAssassin corpus and must never be hardcoded into implementation. Use the same observed/expected orientation throughout: rows `[spam,ham]`, columns `[present,absent]`. Prefer Pearson chi-square with continuity correction **disabled** and state this in the result. When expected-count assumptions fail, include warning and set `reject_null: null` rather than offering a conclusive test decision.  
**Errors:** `422` invalid word/alpha; `503` dataset missing.

### A08 — `GET /statistics/confidence-interval`
**Purpose:** Wilson interval for spam proportion.  
**Query:** `scope=all|train|test` (default `all`), `confidence` number `0.80–0.99` (default `0.95`).  
**200 example:**
```json
{
  "scope": "all",
  "method": "wilson",
  "confidence": 0.95,
  "sample_size": 1000,
  "spam_count": 300,
  "point_estimate": 0.3,
  "lower": 0.2724,
  "upper": 0.3291,
  "limitations": "Historical, curated corpus; interval does not guarantee population representativeness."
}
```
**Errors:** `422`, `503`. Values are illustrative; use formula for actual bounds.

MSE-403 implements A05–A08 over cached verified records. Query words must normalize to one complete unicode-word-v1 token; punctuation/multiple tokens are rejected with safe 422 responses. Trials/successes and confidence/significance bounds are enforced, including successes≤trials. Empty selected scopes return structured 503; absent words and unsuitable expected counts retain their explicit null values/decisions.

### A09 — `POST /predict`
**Purpose:** Classify pasted subject/body text with both persisted models.  
**Request:**
```json
{"text":"Free entry in our prize draw. Claim your offer today!"}
```
**200 example:**
```json
{
  "input": {"character_count": 53, "recognized_token_count": 7},
  "models": {
    "multinomial": {
      "prediction": "spam",
      "spam_probability": 0.92,
      "top_contributions": [
        {"token":"free","presence":"present","log_odds_contribution":1.1,"direction":"spam"}
      ]
    },
    "bernoulli": {
      "prediction": "spam",
      "spam_probability": 0.85,
      "top_contributions": [
        {"token":"free","presence":"present","log_odds_contribution":0.7,"direction":"spam"}
      ],
      "absence_terms_included": true
    }
  },
  "agreement": true,
  "warnings": ["Probabilities are model estimates, not calibrated certainty."]
}
```
**Rules:** Text length 1–50,000 after trimming; whitespace-only invalid; model input is not stored. Explanation values represent signed contributions to **log posterior odds**, not probabilities. The implemented service also supplies `class_prior_log_odds`, `other_present_log_odds`, `absence_log_odds_contribution` and `log_odds` so truncated top terms still reconcile with the full score. `input.character_count` counts trimmed submitted characters; features use canonical normalization. For Bernoulli, the underlying score must include absent-vocabulary terms as well as present terms. If no known tokens are present, return a warning and both model results without inventing token contributions. Output numbers are illustrative.
**Errors:** `422` invalid input; `503` missing models, vocabulary or metadata; `500` unexpected error.

### A10 — `GET /models/metrics`
**Purpose:** Per-model held-out evaluation.  
**Query:** `model=multinomial|bernoulli` required.  
**200 example:**
```json
{
  "model": "multinomial",
  "split_id": "split_seed42_80_20_example",
  "positive_class": "spam",
  "test_count": 200,
  "confusion_matrix": {"tn":135,"fp":5,"fn":10,"tp":50},
  "accuracy": 0.925,
  "precision": 0.909091,
  "recall": 0.833333,
  "f1": 0.869565,
  "false_positive_rate": 0.035714
}
```
**Errors:** `422` invalid model; `503` metrics missing. Example metrics are arithmetically consistent to rounding and not actual corpus results.

### A11 — `GET /models/comparison`
**Purpose:** Both model metrics, same split, side-by-side.  
**200 shape:**
```json
{
  "split_id": "split_seed42_80_20_example",
  "same_test_ids": true,
  "models": {
    "multinomial": {"accuracy":0.925,"precision":0.909091,"recall":0.833333,"f1":0.869565,"false_positive_rate":0.035714},
    "bernoulli": {"accuracy":0.91,"precision":0.88,"recall":0.80,"f1":0.838,"false_positive_rate":0.04}
  }
}
```
**Rule:** Reject or return `503` if models have mismatched split IDs or evaluation sets. Numbers are illustrative, not measured.  
**Errors:** `503` artifacts unavailable/inconsistent.

### A12 — `GET /models/explanations`
**Purpose:** Explain a **specified vocabulary word's general model weight**, not a stored email. Per-email explanations are delivered in `POST /predict`.  
**Query:** `word` one normalized token (required), `model=multinomial|bernoulli` (required).  
**200 example:**
```json
{
  "model":"multinomial",
  "word":"free",
  "in_vocabulary":true,
  "log_odds_when_present":1.1,
  "interpretation":"This token favors spam in this fitted model; it does not imply causation."
}
```
For Bernoulli, response must also disclose that absent-word effects influence classification. If `in_vocabulary=false`, set weight `null` and explain, rather than claiming the weight is 0.  
**Errors:** `422` bad parameters; `503` model unavailable.

## 3. Contract-wide invariants

1. `source_groups` tally to `total`; `class_counts.spam + class_counts.ham == total`.
2. `present + absent` per class matches corresponding class count.
3. Binomial outputs use observed document-frequency proportion, not token count proportion.
4. `predict` cannot access test labels and must load both models from the same artifact generation.
5. `models/metrics` and `models/comparison` must match their persisted confusion matrices.
6. No endpoint should accept arbitrary filesystem paths or remote URLs.
7. Request logging excludes email bodies; error logs should avoid leaking raw message text.
8. No API endpoint to train models or upload a general-purpose new corpus in v1.0.

## 4. Implementation note

A01–A12 are implemented with FastAPI/Pydantic. MSE-405–406 add local transport hardening and cross-route contract coverage. Shared errors redact input values, contexts, paths and tracebacks; validation details contain only known field names and error types. When code is written, update this document to reflect actual response schemas and keep `SRS.md`, `DATA_MODEL.md`, `APP_FLOW.md` and tests aligned. The numeric examples are synthetic and cannot be represented as real model results.

MSE-404 implements A09–A12 from cached, verified artifacts. Prediction bodies forbid extra fields and validate trimmed text including normalized emptiness. Metrics preserve test-ID hashes and zero-division notes; comparison includes dataset/artifact/split identities and limitations. General word explanations always expose the absence flag and a nullable absent-word weight. Prediction returns no submitted text and writes no files.

MSE-405 bounds the HTTP body to 512 KiB and queries to 4 KiB (413/414), rejects foreign origins (403) and non-loopback hosts (400), and explicitly permits the local port-5173 origins without credentials. The supported loopback launcher disables raw URL access logs and forwarded-header trust; application logs omit input, queries and exception details. Cached report reads are bounded.
