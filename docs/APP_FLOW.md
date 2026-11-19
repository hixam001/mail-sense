# MailSense — Application Flow (APP_FLOW)

**Version:** 1.1 · **Date:** 2026-11-19 · **Status:** All six routes implemented and production browser workflows verified

## 1. Context and entry points

MailSense is a **local, single-user academic application**. React/Vite hosts the interface and FastAPI provides read-only analytics plus in-memory prediction. It has **no registration, login, OAuth, account settings, password reset, invitation codes, email notifications, marketing links, search indexing or cloud-hosted entry points**.

### Supported entry points
- Browser at `http://localhost:5173/`: dashboard with dataset/model status.
- Direct local routes while the local dev server is running: `/dataset`, `/probability`, `/statistics`, `/detect`, `/evaluation`.
- Navigation via the persistent left/top menu and page-level related-analysis links.
- Local API schema for developers at `http://127.0.0.1:8000/openapi.json`. CDN-dependent Swagger/Redoc pages are disabled for offline operation.

### First-run setup (replaces onboarding/account creation)
1. Developer obtains the approved SpamAssassin archives and installs local dependencies.
2. Developer executes data ingestion/preprocessing and training CLI commands (specified by the future repository README).
3. Developer starts FastAPI bound to `127.0.0.1:8000` and Vite bound to `localhost:5173`.
4. Student opens the dashboard; React requests `/api/v1/health` and `/api/v1/dataset/summary`.
5. If ready, navigation is available. If dataset/models are unavailable, show missing prerequisite information and offer retry. Dataset exploration may work even when prediction models are unavailable.

**Success:** Readiness summary is honest and app modules have data/artifacts required for their functions.  
**Failure:** Backend missing, source data missing, models missing or incompatible manifests are shown as explicit blockers. Never fabricate results.

## 2. Navigation map

```text
MailSense (/) [local, no auth]
├── Dashboard (/)
│   ├── Open Dataset Explorer
│   ├── Open Probability Analysis
│   ├── Open Statistical Inference
│   ├── Open Spam Detector
│   └── Open Model Evaluation
├── Dataset Explorer (/dataset)
│   ├── Summary / class counts
│   ├── Descriptive statistics
│   └── Histograms / box plots / top words
├── Probability Analysis (/probability)
│   ├── Word contingency table
│   ├── Bayes calculation
│   ├── Bernoulli distribution
│   └── Binomial distribution
├── Statistical Inference (/statistics)
│   ├── Chi-square independence test
│   └── Wilson confidence interval
├── Spam Detector (/detect)
│   ├── Paste email
│   ├── Multinomial result
│   ├── Bernoulli result
│   └── Word contribution details
└── Model Evaluation (/evaluation)
    ├── Shared split summary
    ├── Side-by-side metrics
    └── Confusion matrices / errors
```

Links between Probability Analysis and Statistical Inference preserve the selected normalized word in local UI state or a non-sensitive query parameter such as `?word=free`; email bodies should **not** be embedded in URLs.

## 3. Core flow F-01: Dataset exploration

**Entry:** Dashboard → Dataset Explorer.  
**Purpose:** Understand what the corpus contains before making probability claims.

| Step | Screen / UI | User action | System response / validation | Next state |
|---|---|---|---|---|
| 1 | Dashboard, status indicator | Click **Dataset Explorer** | Navigate to `/dataset` | Loading |
| 2 | Dataset Explorer, scope dropdown | Choose `all`, `train` or `test` | GET dataset summary, statistics, distributions for selected scope | Summary |
| 3 | Class cards, charts | Select email length or word count | Re-render chart and units from same subset | Charts |
| 4 | Top-word table | Inspect a word | Show DF and label; allow navigating to probability analysis | Word selection |
| 5 | Source notes | Read inclusion/exclusion report | Show true retained counts, duplicate exclusions, historical limitation | End |

**Success:** Counts reconcile, units/subset explicit, no unvalidated fake chart data.

**Errors:** Invalid scope rejected; missing dataset → warning with setup instruction; backend timeout → retry; empty subset → empty state.  
**Edge cases:** Rapid scope toggles must discard stale responses; browser back restores route and optionally scope; page abandonment makes no persistent changes; reload recomputes from backend.

## 4. Core flow F-02: Probability exploration

**Entry:** `/probability`, optionally `?word=free`.  
**Purpose:** Turn document-presence frequencies into empirical probability formulas.

| Step | Screen / UI | User action | System response / validation | Next state |
|---|---|---|---|---|
| 1 | Word form | Enter a normalized token | One-token, nonempty and length check | Valid selection |
| 2 | Scope control | Choose `all/train/test` | GET `/probability/word` | Loading |
| 3 | 2×2 counts | Inspect present/absent × spam/ham | Show table and cross-check sums | Formula cards |
| 4 | Formula cards | Read prior, joint, conditional, posterior | Display empirical fraction and calculated rate | Bayes output |
| 5 | Distribution controls | Set `trials` and `successes` | GET `/probability/distributions` | Bernoulli/binomial PMF |
| 6 | Related analysis | Click **Test association** | Navigate `/statistics?word=<token>` | Inference |

**Success:** Empirical probabilities clearly derived from observed counts, theoretical distribution assumptions stated.

**Errors:** Word not observed → explicit undefined `P(spam|word)`; invalid token or impossible `successes>trials` → validation message; service outage → retry.  
**Edge cases:** Toggling words before a request completes ignores stale result; counts from different scopes never mix; back navigation preserves word only (not any private email).

## 5. Core flow F-03: Hypothesis test and confidence interval

**Entry:** `/statistics` or link from Probability Analysis.  
**Purpose:** Distinguish observed association from statistical evidence.

| Step | Screen / UI | User action | System response / validation | Next state |
|---|---|---|---|---|
| 1 | Statistical Inference | Enter/select word, scope and alpha (default `.05`) | Validate inputs | Configured |
| 2 | Test button | Click **Run chi-square test** | POST `/statistics/hypothesis-test` | Loading |
| 3 | Test results | Inspect table, expected counts, chi-square, df and p | Display H0/H1, conclusion/assumption warning | Result |
| 4 | Interval section | Set scope/confidence (default `.95`) | GET `/statistics/confidence-interval` | Wilson interval |
| 5 | Interpretation | Read limitations | Note corpus is curated/historical; p-value does not prove causation | End |

**Success:** Test conclusion is conditioned on approximation assumptions and the interval names its method.

**Errors:** If expected-count assumptions fail, show `insufficient evidence for chi-square approximation` and no automatic reject/retain decision; invalid alpha/confidence rejected.  
**Edge cases:** Changes in word/scope clear outdated output; browser back does not rerun a POST until requested again; if user abandons page, nothing persists.

## 6. Core flow F-04: Spam detection

**Entry:** `/detect`.  
**Purpose:** Apply learned probabilities to pasted text without sending it to any external service.

| Step | Screen / UI | User action | System response / validation | Next state |
|---|---|---|---|---|
| 1 | Spam Detector, textarea | Paste subject/body text | Trim and validate 1–50,000 characters | Ready to classify |
| 2 | Classify button | Submit | POST `/predict`; disable duplicate submissions for this request | Loading |
| 3 | Result cards | Read Multinomial and Bernoulli predictions | Show both spam probabilities, labels and agreement status | Results |
| 4 | Explanation lists | Expand explanation | Show directional log-odds contributions and limitations | Explained |
| 5 | Compare models link | Click **Evaluation details** | Navigate `/evaluation` | Comparison |

**Success:** Two results from same artifact generation, probability range valid, explanations faithful to models.

**Errors:** Empty/whitespace input → inline error; excessive length → inline error; missing artifacts → `Model unavailable` with setup hint; request timeout → retry.  
**Edge cases:** Multiple clicks do not duplicate request; if text changes while prediction is in flight, stale result cannot be presented as current; email content is not stored as session history; browser reload clears text unless local in-memory React state persists naturally on same page.

## 7. Core flow F-05: Model evaluation

**Entry:** `/evaluation`.  
**Purpose:** Interpret held-out evaluation, including how each model fails.

| Step | Screen / UI | User action | System response / validation | Next state |
|---|---|---|---|---|
| 1 | Evaluation page | Open route | GET `/models/comparison`, optionally `/models/metrics` | Loading |
| 2 | Split banner | Read split ID/test count | Confirm same test IDs for both models | Valid comparison |
| 3 | Metric cards | Compare accuracy, precision, recall, F1, FPR | Show metrics with units | Metrics |
| 4 | Confusion matrices | Inspect TP/TN/FP/FN | Explain FP as legitimate email blocked, FN as spam missed | Interpretation |
| 5 | Limitations section | Read bias/calibration note | Distinguish historical holdout performance from real-world performance | End |

**Success:** All metrics reconcile mathematically and are attributed to actual artifacts.

**Errors:** Missing or mismatched evaluations → block comparison and show `503` guidance, never compare unrelated splits.  
**Edge cases:** Refresh uses same persisted model artifacts; no runtime retraining on navigation; requests finishing out of order cannot mix models from two generations.

## 8. Recovery and operational flows

### Backend unavailable
- `IF health request fails THEN` show global disconnected status and a **Retry connection** action.
- Retain currently selected route/control values; do not display unmarked stale metrics as current data.
- On reconnection, re-fetch readiness and required datasets/models.

### Corpus not prepared
- `IF dataset_ready=false THEN` show setup checklist for ingestion and disable dataset-dependent calculations.
- Model status may independently be `false`; explain separate prerequisites.

### Missing models
- `IF models_ready` is incomplete `THEN` show usable dataset/statistical pages while disabling incomplete prediction/comparison workflows.
- Show instructions to rerun trusted local training script; **not** an API-based training button.

### Malformed or unsupported inputs
- `IF token is invalid THEN` reject before request and show expected one-token format.
- `IF email text is empty/overlong THEN` reject and focus the field.
- `IF status is 422 THEN` display field-specific error; `IF status is 500 THEN` show generic error without stack trace.

### Offline behavior
- Browser/server communication is over localhost, so working without the internet is supported **after all code/dependencies/data are present**. No service worker/cache-first guarantee is required.

## 9. Decision-point matrix

| Condition | System decision | UI consequence |
|---|---|---|
| Backend health `ready` | Continue | Normal controls |
| Dataset missing | Block dataset analytics | Setup instruction and retry |
| Model missing | Block detect/evaluation only | Model artifact warning |
| Unknown probability word (DF=0) | Return undefined posterior | Show zero counts and `undefined`, not 0% |
| `trials<successes` | Reject | Validation message |
| Insufficient chi-square expected counts | Decline automatic significance decision | Warning and explanation |
| Models have different test IDs | Reject comparison | Error; no scores shown |
| Model predictions disagree | No tie-breaking model | Display both predictions transparently |
| User text changes mid-inference | Invalidate stale request | Clear/ignore previous prediction |
| User refreshes page | No saved account/session | Reload route, fetch aggregates anew |

## 10. Screen inventory

| Route | Access | Key elements | Actions | States |
|---|---|---|---|---|
| `/` | Local public | App overview, readiness, module links | Navigate; retry health | loading/ready/degraded/offline |
| `/dataset` | Local public | Scope dropdown, class cards, descriptive table, charts | Choose subset/metric; open word analysis | loading/success/empty/error |
| `/probability` | Local public | Word input, contingency, formulas, distribution inputs | Analyze word; change trials; go to inference | idle/loading/success/undefined/error |
| `/statistics` | Local public | Chi-square controls, observed/expected table, interval controls | Run test; set confidence | idle/loading/success/assumption warning/error |
| `/detect` | Local public | Textarea, submit, dual result cards, explanation | Classify; open evaluation | idle/invalid/loading/success/model-missing/error |
| `/evaluation` | Local public | Split metadata, metrics, confusion matrices, limitations | Compare models | loading/success/incompatible/missing/error |

All pages are unauthenticated. No `/login`, `/register`, `/account`, session expiry, OAuth callback or role-specific screens exist. There is no onboarding email or external navigation requirement.

## 11. UI state and data flow principles

- Keep **server data** separate from **transient view state**. Selected token/scope can be shared between related pages; raw email text must not be put in a URL.
- Use a typed API service wrapper and request cancellation or request IDs to avoid stale result races.
- Persist only the trained artifact generation and source corpus preprocessing results on disk. No student accounts, browsing history or classification history.
- Every probability/statistical chart must show its source scope and units.
- A displayed model probability must include an estimate/calibration caveat.
- No marketing campaigns, SEO/search engines or deep-email-links are applicable to a locally hosted demonstration.

## 12. Flow acceptance walkthrough

1. Run both local servers, verify dashboard readiness.
2. On `/dataset`, verify class totals and labeled histogram.
3. On `/probability`, enter `free`; verify present/absent counts and empirical posterior formula.
4. On `/statistics`, run chi-square with assumptions and review Wilson interval.
5. On `/detect`, paste nonempty text; show both models and contributions.
6. On `/evaluation`, verify the same held-out split and metrics.
7. Retry with empty text and disconnected backend; confirm truthful error handling.

No steps are marked completed until the implemented software passes the corresponding test cases in `TEST_PLAN.md`.
