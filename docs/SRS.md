# MailSense — Software Requirements Specification (SRS)

**Version:** 1.0 (LOCKED)  
**Baseline approved:** 2026-11-19  
**System:** Statistical Analysis and Probabilistic Email Spam Detection  
**Status:** Design requirements approved; not implemented

## 1. Introduction

### 1.1 Purpose
Specify verifiable functional, data, mathematical, interface, operational and testing requirements for the locally deployed MailSense educational application. This SRS is the authoritative acceptance baseline.

### 1.2 Intended users
- Student: examine and explain probability/statistics and classify sample emails.
- Instructor: verify mathematical correctness and fair comparison of classifiers.
- Developer: implement data ingestion, API, models, frontend and tests.

### 1.3 Terminology
- **spam:** positive class, label `spam` / numeric 1 in internal processing.
- **ham:** legitimate email, label `ham` / numeric 0.
- **document frequency (DF):** number of messages containing a word at least once.
- **token frequency (TF):** number of occurrences of a word across messages.
- **empirical posterior:** `spam-and-word-present / all-word-present` when denominator > 0.
- **model probability:** Naive Bayes `predict_proba`, **not** a calibrated risk guarantee.
- **training set / test set:** disjoint partitions assigned after deduplication, before vocabulary fitting.

## 2. Scope and locked constraints

**Dataset:** SpamAssassin Public Corpus; canonical recent snapshot per group, source archives recorded.  
**Frontend:** React + Vite.  
**Backend:** Python + FastAPI.  
**Statistics:** Pandas, NumPy, SciPy.  
**Models:** Multinomial Naive Bayes and Bernoulli Naive Bayes, both required.  
**Charts:** Recharts; Matplotlib permissible for static report figures.  
**Deployment:** 127.0.0.1 / localhost, local files, no database, no accounts.  
**Split:** 80% train, 20% test; stratified, seed 42, duplicate removal before splitting.  
**Model smoothing:** Laplace `alpha=1.0` initially.  
**Primary input:** user-pasted subject/body text; no live inbox.

## 3. Functional requirements

| ID | Requirement | Verification |
|---|---|---|
| FR-01 | Prepare corpus via local CLI ingestion, distinguish `spam` and `ham` from approved group folders | Ingestion integration test |
| FR-02 | Parse MIME subject/plain text; convert HTML body to safe text when no plain-text alternative exists; never execute attachment content | Parser fixtures |
| FR-03 | Log archive/file provenance, parse errors, exclusions, duplicate counts and stable message IDs | Manifest inspection |
| FR-04 | Produce a deterministic stratified 80/20 train/test split before learning vocabulary | Split test |
| FR-05 | Show retained record count, spam/ham counts/proportions and subset (`all`, `train`, `test`) | Dataset API/UI test |
| FR-06 | Calculate mean, median, mode, quartiles, sample variance and sample standard deviation for email length and token count | Numerical unit tests |
| FR-07 | Render labeled histogram, box plot and top-word/document frequency views | UI test |
| FR-08 | For a chosen normalized word return full 2×2 word-present vs class contingency table | Known-table unit test |
| FR-09 | Show prior, joint, marginal, conditional and empirical Bayes posterior probabilities with numerators/denominators | Known-table unit test |
| FR-10 | Provide illustrative Bernoulli and binomial calculations with inputs and assumptions displayed | Distribution tests |
| FR-11 | Perform chi-square independence test; show H0/H1, observed/expected counts, chi-square statistic, df, p-value and suitability warnings | Inference tests |
| FR-12 | Calculate a two-sided 95% Wilson confidence interval for spam prevalence; label sample/subset and confidence level | Reference test |
| FR-13 | Train Multinomial NB with term counts from training-only vocabulary | Training test |
| FR-14 | Train Bernoulli NB with binary word presence using the same training-only vocabulary | Training test |
| FR-15 | Persist both fitted models, vocabulary/preprocessing configuration, split ID and metrics locally | Artifact test |
| FR-16 | Accept pasted text and produce both classifications and model-estimated spam probabilities | Prediction API test |
| FR-17 | Provide accurate token-contribution explanations, including relevant class priors; disclose Bernoulli absent-word effects | Explanation test |
| FR-18 | Evaluate both models on the identical untouched test IDs with accuracy, precision, recall, F1, false-positive rate and confusion matrices | Evaluation reconciliation |
| FR-19 | Display a side-by-side comparison and model agreement/disagreement without claiming certainty | UI test |
| FR-20 | Report readiness, empty states, invalid input and offline/missing-model errors with actionable messages | API/UI negative tests |

### 3.1 Business and mathematical rules
- **Class labeling:** Derive labels from corpus collection type, never an email's own `Subject`, `X-Spam-Status` or headers that encode evaluation labels.
- **Feature source:** Subject + body text only. Do not use original full transport headers, sender reputation, source folder strings or filename as ML predictors.
- **Word presence:** Case-normalized token matching; DF uses each email at most once per word, even if the word occurs repeatedly.
- **Length metrics:** `character_count` counts normalized subject/body characters; `token_count` counts tokenizer-produced tokens. Display these units.
- **Missing word:** If DF=0, mark the empirical posterior undefined due to zero denominator, not 0% spam. The classifier may still make a prior-based prediction.
- **Statistics population:** Dataset exploration may summarize all retained records, while classifier model fitting must access only train labels/features. Analyses using test labels must not feed model selection/training.
- **Chi-square:** If expected counts are too small for valid approximation, return a warning and do not overclaim significance; optional Fisher exact fallback may be mentioned as future scope, not silently used.
- **Confidence interval:** Wilson method, two-sided, default 95%; interpreted as an interval estimate from the observed sample under sampling assumptions, not a guaranteed interval for modern email.
- **Probability output:** Format estimated probabilities to reasonable precision; avoid implying perfect calibration.
- **Metric positive class:** Always `spam`, and distinguish **false positive = ham classified as spam** from **false negative = spam classified as ham**.
- **Evaluation:** Use test set only for final reporting. If development adjusts preprocessing/model choices using test outcomes, document that it invalidates the untouched-test claim and create a new holdout.

## 4. External interfaces

### 4.1 User interface / routes
- `/` — Dashboard/readiness
- `/dataset` — Dataset Explorer
- `/probability` — Probability Analysis
- `/statistics` — Statistical Inference
- `/detect` — Spam Detector
- `/evaluation` — Model Evaluation

No login or permissions checks. Screens must support loading, success, empty, invalid, and server-error states as applicable. Direct links to local routes work while the dev server is running.

### 4.2 Backend
API prefix `/api/v1`; OpenAPI documentation generated by FastAPI. Concrete routes, types and examples in `API_CONTRACT.md`. Errors use a shared JSON structure and HTTP 4xx/5xx status codes. CORS limited to the configured local React origin.

### 4.3 Local file interfaces
Data under `data/raw`, `data/processed`, artifacts under `artifacts/models` and `artifacts/reports`. The project does **not** require a database. Data is read-only during app usage; preparation/training occur via CLI scripts.

## 5. Data requirements

- Source archives include group label, archive filename, downloaded file checksum and acquisition date in a manifest.
- The developer selects latest coherent archives per group (for example 20030228 easy_ham, hard_ham, easy_ham_2, spam, plus 20050311 spam_2) and does **not** concatenate dated replacements blindly.
- Enforce safe archive extraction (block path traversal/symlinks), bounded file decoding and no executable attachment processing.
- Generate stable identifiers from normalized source identity, deduplicate exact text-content hashes before partitioning and record class conflicts rather than silently choosing labels.
- Preserve raw source independently; processed records carry `message_id`, `source_group`, `label`, text, token/character counts and split. Text previews should avoid unnecessarily exposing addresses.
- Document final usable counts after processing; **do not assume** original published totals match the cleaned corpus.
- See `DATA_MODEL.md` for full fields, relationships and schema validation.

## 6. Non-functional requirements

| ID | Requirement | Acceptance method |
|---|---|---|
| NFR-01 | Work offline after prerequisites and corpus are downloaded | Disconnect-network smoke test |
| NFR-02 | Run React and FastAPI on local loopback, not LAN or internet by default | Binding check |
| NFR-03 | Respond to normal single-text prediction within 3 seconds at p95 on designated demo hardware after warm-up | Timed test, record hardware |
| NFR-04 | Typical cached dataset summary request ≤ 5 seconds on demo hardware | Timed test |
| NFR-05 | Repeated preprocessing/training with same archives, config and seed reproduces split and predictions | Determinism test |
| NFR-06 | Do not send, store persistently or log pasted email bodies in normal inference | Code/log review |
| NFR-07 | Limit prediction text length to 50,000 characters; reject empty/whitespace-only inputs | Validation tests |
| NFR-08 | Handle malformed messages, invalid encodings, missing artifacts and unavailable backend without crash or fake success | Fault tests |
| NFR-09 | Make primary navigation/forms keyboard accessible; text/chart contrasts and labels interpretable | Manual accessibility review |
| NFR-10 | Automated tests cover statistical algorithms, API validation, split reproducibility and prediction contract | Test suite |
| NFR-11 | Do not expose local file paths, tracebacks or raw private message bodies through public responses | Security review |

Performance targets may be revised only with recorded hardware evidence and an approved SRS change.

## 7. Acceptance criteria (release gates)

- AC-01: Successful local installation and readiness check from the README.
- AC-02: Source manifest and dataset counts demonstrably follow selected archives/cleanup.
- AC-03: Three manually worked descriptive/probability examples match backend.
- AC-04: Chi-square test and Wilson interval match known reference calculations.
- AC-05: Both classifiers use the same split and share a train-fitted vocabulary.
- AC-06: Both produce predictions, probabilities and defensible explanations for a valid new input.
- AC-07: Every reported evaluation metric matches confusion-matrix arithmetic.
- AC-08: Loading, empty, missing model, invalid input and backend-offline UI states work.
- AC-09: No external email connections or API calls are required during demo.
- AC-10: Results and limitations can be explained in the university report.

## 8. Exclusions

No accounts, cloud hosting, arbitrary upload UI, live email inbox, SMS support, production filtering, external reputation lookups, LLMs, neural classifiers, database, queued jobs or user prediction history. See `PRD.md`.

## 9. Traceability and change control

`PRD.md` states user value; `SRD.md` summarizes scope; this SRS controls implementation requirements; `API_CONTRACT.md`, `DATA_MODEL.md`, `APP_FLOW.md`, `ARCHITECTURE.md`, `STATISTICAL_METHODS.md` and `TEST_PLAN.md` operationalize them. No functionality is claimed built or tested until evidence is recorded.

**Locked design choices:** SpamAssassin, React/FastAPI, both Naive Bayes models, local deployment, probability-first academic focus. Change requests must state reason, affected FR/NFR IDs, impact on tests, date and incremented document version.
