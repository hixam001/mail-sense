# MailSense project handoff

Last updated: 2026-11-19 (Asia/Karachi).
Completed preparation: **MSE-100 — Delivery workflow** and **MSE-107 — Graphify memory consolidation**.
Completed maintenance: **MSE-108 — Ignore local agent tooling and generated/private files**.
Latest implementation: **MSE-402 — Typed dataset summary statistics and distribution APIs**.
Next implementation ticket: **MSE-403**.

## Read this at every task start

Read [AGENTS.md](../AGENTS.md), [memory guide](README.md),
[PRODUCT.md](../PRODUCT.md) and this handoff before selecting or resuming work.
Confirm progress against files and Git history. The
[implementation plan](../docs/IMPLEMENTATION_PLAN.md) owns dependencies and ticket
acceptance criteria; this handoff owns the live status of every ticket.
[SRS.md](../docs/SRS.md) remains the locked technical baseline.

## Next task

**MSE-403** — Expose A05–A08 with typed single-word/scope/trial/significance/confidence validation, known synthetic table tests through HTTP, safe null/unsuitable cases and actual-scope comparisons, commit/push then model prediction/evaluation APIs MSE-404.

Continue the application backlog autonomously after each verified commit/push. Analyze each task with Gravitas, preserve all remaining tickets, verify acceptance, update this handoff and graph, then commit/push without contributor trailers.

## Established and completed preparation

- The README and ten specification documents are present. They establish the
  product, scope, API/data contracts, workflows, architecture, mathematical
  methods, acceptance tests and all 39 implementation tickets.
- `PRODUCT.md` records the confirmed web platform, users, approved stack, five
  modules, educational purpose, local operation and evidence limitations.
- Project skills are installed locally under `.agents/skills/`: `gravitas`,
  `impeccable` and `security-audit`. They are ignored and untracked; a fresh
  clone needs its own skill installation. Local copies are retained.
- Impeccable installed its local engine and `.codex/hooks.json`. Product context
  initialization is complete. The frontend currently has a plain scaffold page;
  no product visual identity or `DESIGN.md` has been established.
- `AGENTS.md` persists the user's analyze → map → implement → verify → update
  handoff → final checks → commit → push workflow. Jira-style subjects use
  `MSE-<ticket>: <summary>`; no added contributor attribution or co-author/sign-off
  trailers. The previous duplicate memory index and workflow record are removed.
- `memory/` is the single project memory directory. This handoff owns progress;
  `README.md` documents retrieval. `graph.py` uses pinned Graphify to build
  `graphify-out/graph.json`, `graph.html` and `GRAPH_REPORT.md` from the actual
  documents, ticket dependencies, statuses and standing instructions. Generated
  graph data includes source locations and hashes so stale memory can be detected.
- `.gitignore` excludes local credentials, dependencies, runtime output, raw
  corpus messages, processed message text and trained model artifacts while
  retaining shared memory, application source, lockfiles, manifests and reports.
- **MSE-108:** `.agent/`, `.agents/`, `.codex/`, `.gravitas/` and `.impeccable/`
  are entirely local/ignored. Previously tracked `.agents/` and `.codex/` files
  are removed from the Git index only. Shared instructions no longer link to
  an untracked skill file as though it ships with a clone. Ignore rules also
  cover Python/Node caches, package/build/test output and editor temporaries.
  No application code or existing implementation-ticket status changes.
- MSE-100 and MSE-107 cover documentation/tooling preparation only. They do not complete
  any MSE-101–606 feature ticket or any product acceptance gate.

## Implemented application functionality

- **MSE-101 complete:** `frontend/` contains a React 19/Vite 8 JavaScript
  scaffold, React plugin, ESLint configuration, package manifest/lockfile,
  HTML entry and `src/App.jsx`/`main.jsx`. The page displays an honest scaffold
  message. It makes no API requests and requires no backend to render.
- `backend/app/main.py` defines the FastAPI application and `GET /` greeting.
  Runtime pins live in `backend/pyproject.toml`/`uv.lock`;
  `backend/requirements.txt` is the hashed runtime-only export. No
  `/api/v1` endpoints, readiness logic or CORS integration exist yet.
- Planned frontend directories, backend Python packages/scripts/tests,
  `data/raw`, `data/processed`, `artifacts/models` and `artifacts/reports` exist.
  Empty placeholders are tracked while emails, models, dependencies and builds
  remain ignored. The README contains verified preliminary setup/run commands.
- **MSE-102 complete:** `.node-version`, `.python-version`, frontend engines,
  packageManager and backend metadata pin Node 22.23.5/npm 10.9.9, Python 3.12.15
  and uv 0.13.9. `scripts/node.py` installs checksum-verified official Node under
  ignored `.tools/` and runs commands with its own PATH; no system Node or old
  `/tmp` installation is needed. Direct frontend dependencies are exact pins;
  the npm lock includes Recharts/react-is. Backend uv sync installs the frozen
  runtime/scientific stack and the pytest/Ruff/httpx2 development tools.
- `docs/SETUP.md` and the README provide verified install/run/check/update
  commands and platform/offline limits. Nine environment/bootstrap tests cover
  native scientific APIs, both NB dependency classes, synthetic artifact
  roundtrips, API client compatibility and runtime-download failure boundaries.
- **MSE-103 complete:** `backend/app/services/corpus_sources.py` and the
  `backend/scripts/download_corpus.py` CLI acquire the five canonical archives,
  stage bounded official-only downloads, enforce schema/group/URL/label rules,
  pin cached/refetched bytes to recorded hashes, and verify everything offline.
  Complete caches are network-free no-ops. Network, integrity and metadata-write
  failures preserve provenance and clean staging/lock files.
- `data/processed/source_manifest.json` records official source URLs, groups,
  labels, actual UTC acquisition times, SHA-256 and compressed sizes. The five
  local archives total **6,962,803 bytes**. Acquisition initially wrote `null`
  parsing counters; MSE-104 now populates them. Original byte hashes and UTC
  acquisition times are preserved. Archive bytes remain ignored under `data/raw/`.
- **MSE-104 complete:** `mail_parser.py` and `corpus_ingest.py` implement
  bounded streamed extraction, strict paths/member types, private generated
  staging names and MIME subject/body decoding with deterministic NFC/whitespace
  normalization. Alternative MIME selects plain text then safe HTML fallback;
  named/disposition/message attachments and HTML scripts/styles/resources are
  excluded. No URLs are fetched, markup rendered or archive commands executed.
- `backend/scripts/ingest_corpus.py` exposes offline `run`/`verify`. Private
  `data/processed/messages.parsed.jsonl` stays ignored (owner-only permissions).
  Shareable `parsing_report.json` contains only source metadata, versions/limits,
  counts/hashes and rejected hash IDs/reason codes. Manifest parsing counters
  are complete and reconcile. This parser stage precedes deduplication/token
  counts; MSE-105 implements those downstream and MSE-106 adds the split.
- The actual corpus has **6,046 candidates, 5,992 accepted and 54 rejected**
  for malformed MIME; five directories and five `cmds` control files are counted
  separately. Accepted by group: easy_ham 2,500; easy_ham_2 1,400; hard_ham 249;
  spam 473; spam_2 1,370. These are explicitly before deduplication, not cleaned
  prevalence or training-ready counts. Strict MIME structure checks can exclude
  partially readable messages; diagnostics preserve that limitation.
- `docs/DATA_MODEL.md` v1.2 and SETUP document intermediate records, `mime-v1`,
  normalization, charset fallback, limits, count semantics and recovery. Archive
  structure/resource failures abort; individual message failures are counted.
  Ordinary publication exceptions restore prior artifacts, and verification
  detects inconsistent sets after abrupt termination; rerun from pinned inputs.
- **MSE-105 complete:** `corpus_dataset.py` groups exact text hashes with
  equality checked, excludes every row in conflicting-label groups, and retains
  the smallest stable ID from each same-label group. Fixed `text_features.py`
  defines `unicode-word-v1`: lowercase + Unicode `(?u)\b\w\w+\b` unigrams,
  no stop words/accent stripping or learned state. Tests match the pinned
  CountVectorizer analyzer without fitting. Case/punctuation remain significant
  for content deduplication, and nonblank zero-token rows remain valid.
- `backend/scripts/prepare_dataset.py` exposes offline `run`/`verify`. Ignored,
  owner-only `messages.csv` keeps representative provenance/text/character
  counts/warnings and adds token counts; rows sort by ID. MSE-106 joins split
  membership in memory while preserving this CSV's bytes.
  Shared `publish_artifacts` rolls back ordinary publication failures; verifier
  rederives exact CSV/report bytes from verified parser inputs. No upstream
  input, raw archive, acquisition field or SourceArchive count changes.
- Public `deduplication_report.json` pins input/output hashes/sizes, versions,
  tokenizer/configuration and dataset ID, per-source/class counts and complete
  hash-only exclusion/representative mapping. Dataset ID hashes canonical
  retained CSV plus explicit configuration; it is independent of input row order.
- Actual retention: **5,862 / 5,992 parsed rows**, comprising **4,107 ham and
  1,755 spam**. There are **130 duplicate exclusions across 96 groups**, zero
  observed conflicts (whole-group conflict removal verified synthetically).
  Retained per source: easy_ham 2,471; easy_ham_2 1,389; hard_ham 247; spam 454;
  spam_2 1,301. The earlier 54 MIME rejections are separate. Exact-text dedup
  does not remove near duplicates or guarantee independence/modern prevalence.
- DATA_MODEL v1.3, STATISTICAL_METHODS token rules, SETUP/README/architecture
  and PRODUCT evidence reflect the implemented lifecycle.
- **MSE-106 complete:** `corpus_split.py` and `scripts/split_dataset.py`
  implement canonical-ID sorted, label-stratified splitting with test_size=0.2,
  seed 42 and shuffle enabled. Test size rounds up, train is the complement;
  both labels must occur in both subsets. Empty/single/unsupported small or
  imbalanced inputs fail with safe codes; the policy is never silently changed.
- `data/processed/split_manifest.json` pins sorted train/test ID lists and their
  hashes, dataset/split identity, all upstream file hashes, runtime/configuration,
  exact counts and rounding. No message text or member names enter the manifest
  or CLI. Lock/staging/publication guards preserve previous outputs on ordinary
  failures; complete rederivation detects stale/tampered input/membership.
- `corpus_dataset.load_dataset` returns verified typed rows/report;
  `corpus_split.load_split_dataset(root, scope="all")` joins `split` by ID in
  fresh private rows and returns the verified manifest. `train`/`test` scopes
  filter membership. This fulfills the split field without rewriting retained
  CSV or duplicating text. No vocabulary/model is fitted.
- Actual split: **4,689 train (3,285 ham, 1,404 spam)** and **1,173 test
  (822 ham, 351 spam)**. IDs are unique/disjoint, cover all 5,862 retained rows,
  and have no shared exact content hashes. Dataset ID and all upstream bytes,
  original raw hashes and acquisition metadata remain unchanged.
- **Gate 1 complete:** provenance, parsed/retained data and stratified split
  reproduce from the pinned corpus. Exact duplicates cannot span partitions;
  near duplicates/dependence and historical sampling limitations remain.
  T02 is logged with observed synthetic/actual evidence in TEST_PLAN v1.1.
  DATA_MODEL v1.4, methodology/setup/architecture/README and PRODUCT document
  the implemented split/join and remaining boundaries.
- The remaining inventory below records pending work. Prior milestone
  notes describe the state at that milestone; later evidence supersedes them.
  Synthetic environment checks are not measured corpus/model results.

- **MSE-201 implemented:** Descriptive statistics for count metrics. 181 tests passed; Ruff clean. Known [2,4,4,6] mean/median/mode=4, variance=8/3, Q1=3.5/Q3=4.5. Empty/singleton and mode ties verified. Actual all/train/test class sizes, means and variances independently reconciled; all=4,107 ham/1,755 spam. Continuous completion through MSE-606 is authorized and persisted in AGENTS.md.

- **MSE-202 implemented:** Histogram boxplot and document-frequency aggregates. 191 tests passed under Gravitas; Ruff clean. Numeric histograms reconcile with NumPy, constants/empty subsets and linear boxplots verified; repeated words count once per document. Actual histograms and selected counts reconcile for all 9 scope/class combinations.

- **MSE-203 implemented:** Empirical word-document contingency and probabilities. 201 tests passed under Gravitas; Ruff clean. Synthetic 1000-row table gives prior .3, word .25, joint .18, likelihood .6 and posterior .72. Actual free counts independently checked: all spam 811/1755 and ham 577/4107; train 661/1404 and 460/3285; test 150/351 and 117/822. Zero denominators return null and explanatory notes.

- **MSE-204 implemented:** Bernoulli and binomial probability demonstrations. 221 tests passed under Gravitas; Ruff clean. PMF for p=.25 n=10 k=1 is .1877117156982422; p=0/1, complete mass and independent SciPy values verified. Trials/successes are bounded integers, nonfinite probabilities rejected, empty denominators remain undefined and independence assumptions are explicit. Actual corpus formula checks passed for all scopes.

- **MSE-205 implemented:** Pearson chi-square with expected-count suitability checks. 240 tests passed under Gravitas; Ruff clean. Synthetic table gives chi-square 280, df=1 and p=7.50924e-63 with correction disabled. Expected counts below 5 never produce automatic decisions; zero expected counts yield null statistics. Actual free association matches independent SciPy for all/train/test (703.7827464/591.5580088/113.6506405). Independence/causation caveats are explicit.

- **MSE-206 implemented:** Wilson spam-proportion confidence intervals. 264 tests passed under Gravitas; Ruff clean. Known 300/1000 interval matches rounded .2724–.3291; boundaries, empty samples, confidence limits and independent normal quantiles verified. Actual 95 percent interval for 1755/5862 is .2877962371144159–.3112382719988152; train/test intervals independently matched. Historical-sample limitations are explicit.

- **MSE-207 implemented:** Numerical verification evidence and Gate 2 completion. 267 tests passed under Gravitas; Ruff clean. Executable report verifies 13 independent checks across descriptive/Bayes/binomial/Pearson/Wilson examples, with strict relative tolerance for the tiny p-value. Actual aggregate scopes carry dataset/split/input provenance; report reproduces byte for byte. Statistics engine works without model artifacts or UI; Gate 2 complete.

- **MSE-301 implemented:** Shared training-only vocabulary and count features. 274 tests passed under Gravitas; Ruff clean. Actual matrices are 4689x60135 and 1173x60135. All 60135 vocabulary terms come from training records; 12200 held-out-only tokens are excluded. Feature mapping hash f7ba4c18eef3aa09cacedf7f2518f4c97431a56d2f06c7f9c0c08a5af4402937 and matrices reproduce. Held-out text/labels cannot change fitted training features; no model fitting or persistence yet.

- **MSE-302 implemented:** Multinomial Naive Bayes on shared count vectors. 276 tests passed under Gravitas; Ruff clean. alpha=1 feature likelihoods and priors match manual Laplace/softmax calculations; held-out label mutation cannot affect fitted parameters. Actual model fits 4689 training rows with 60135 fixed features and class counts 3285 ham/1404 spam; finite inference verified. Persistence/evaluation remain later tasks.

- **MSE-303 implemented:** Bernoulli Naive Bayes on shared binary presence. 279 tests passed under Gravitas; Ruff clean. Binary conversion handles sparse zeros/invalid counts and preserves original matrices. Manual Bernoulli likelihoods and full scores including absent features match predictions; repetition and held-out labels cannot alter the fit. Actual classifiers share 4689 training IDs and 60135 features with finite inference.

- **MSE-304 implemented:** Trusted model persistence and provenance verification. 298 tests passed under Gravitas; Ruff clean. All three binary hashes and strict metadata are checked before any unpickling; bounded fixed local files reject links, staleness, runtime/split mismatches and corruption. Publication rollback and owner-only permissions verified. Actual cross-process deterministic training/reload preserves original provenance; artifact ID 747bb5f51c2d231140efcc17d1316be68407d07fa9f9a7adcca1b3df2ce01ca3. Models and metadata remain ignored.

- **MSE-305 implemented:** Identical held-out model evaluation with reconciled metrics. 303 tests passed under Gravitas; Ruff clean. Both models use the same 1173 test IDs/hash; sklearn independently matches all confusion counts and accuracy/precision/recall/F1. Actual Multinomial TN814 FP8 FN14 TP337, accuracy .9812446717817562; Bernoulli TN815 FP7 FN70 TP281, accuracy .9343563512361467. Report is byte-repeatable, zero denominators are null with notes, no fitting/tuning occurs in evaluation.

- **MSE-306 implemented:** Transient dual-model inference and faithful log-odds explanations. 314 tests passed under Gravitas; Ruff clean. Per-token contributions plus class prior, omitted-present remainder and Bernoulli absent-feature aggregate reconcile with public model log-probabilities on fixtures and actual models. Repetitions, class-column lookup, unknown tokens, blank/control-only text and 50000-character bounds verified. Predictions do not echo or persist submitted text; model file hashes remain unchanged.

- **MSE-307 implemented:** Measured model card and Gate 3 completion. 314 tests passed under Gravitas; Ruff clean. Model card is generated from measured evaluation and verified against every model metric, dataset/split/test/artifact identity and actual inference. Historical sampling, near duplicates/dependence, calibration, one-split selection and false-positive limitations are explicit. Gate 3 complete without API/UI. Corrected inherited API documentation whitespace and added fail-fast final delivery checks after the earlier orchestration mistake.

- **MSE-401 implemented:** Truthful FastAPI readiness and redacted shared errors. 319 tests passed under Gravitas; Ruff clean. Factory supports isolated roots, typed health and common error schemas. Missing/corrupt artifacts degrade safely; models can be unavailable while dataset remains usable. SHA cache catches same-size/same-time tampering and recovers without restart. Validation/404/500 responses omit request values and paths. Actual healthy dataset/model/evaluation snapshot verified; cached health averaged .033 seconds.

- **MSE-402 implemented:** Typed dataset summary statistics and distribution APIs. 332 tests passed under Gravitas; Ruff clean. A02–A04 responses match pure services for all/train/test; actual totals 5862/4689/1173 and source/class counts reconcile. Histograms sum correctly and document frequencies obey filters. Exclusions are explicitly global before split (184 total, 130 duplicates, 54 parse rejects), not invented per-partition counts. Invalid queries return redacted 422; missing data 503; dataset endpoints work without models.

## Full remaining implementation inventory

**22 implementation tickets are complete; 17 are Not started**. Update statuses as work is
implemented and verified; retain incomplete and blocked tickets in this table.
Dependencies and detailed acceptance criteria are in
[IMPLEMENTATION_PLAN.md](../docs/IMPLEMENTATION_PLAN.md).

| Ticket | Remaining work | Status |
|---|---|---|
| MSE-101 | Initialize React/FastAPI monorepo and project structure | Complete — runtime/build/lint verified |
| MSE-102 | Pin dependencies and document environment setup | Complete — fresh install/locks/tests verified |
| MSE-103 | Obtain canonical official corpus archives and source/checksum manifest | Complete — real downloads/hashes/offline verification |
| MSE-104 | Implement safe extraction and MIME text parsing | Complete — real parsing/counts/hashes verified |
| MSE-105 | Deduplicate, reject label conflicts and derive summary records | Complete — retained uniqueness/counts/tokenizer verified |
| MSE-106 | Verify deterministic stratified 80/20 split, seed 42 | Complete — membership/counts/hashes/Gate 1 verified |
| MSE-201 | Implement descriptive statistics for text length and token count | Complete — acceptance verified |
| MSE-202 | Aggregate histograms, box plots and top-word data | Complete — acceptance verified |
| MSE-203 | Implement 2×2 word contingency and empirical probabilities | Complete — acceptance verified |
| MSE-204 | Implement Bernoulli/binomial calculations with assumptions | Complete — acceptance verified |
| MSE-205 | Implement Pearson chi-square and assumption checks | Complete — acceptance verified |
| MSE-206 | Implement Wilson proportion confidence intervals | Complete — acceptance verified |
| MSE-207 | Verify formula unit tests and record numerical evidence | Complete — acceptance verified |
| MSE-301 | Fit a shared training-only CountVectorizer vocabulary | Complete — acceptance verified |
| MSE-302 | Train Multinomial Naive Bayes with alpha=1.0 | Complete — acceptance verified |
| MSE-303 | Train Bernoulli Naive Bayes with alpha=1.0 | Complete — acceptance verified |
| MSE-304 | Persist trusted artifacts, matching metadata and checksums | Complete — acceptance verified |
| MSE-305 | Evaluate both models on the same untouched holdout | Complete — acceptance verified |
| MSE-306 | Implement faithful token/prior and absent-feature explanations | Complete — acceptance verified |
| MSE-307 | Save evaluation evidence and document model limitations | Complete — acceptance verified |
| MSE-401 | Implement FastAPI health/readiness and shared error envelope | Complete — acceptance verified |
| MSE-402 | Implement dataset summary/statistics/distribution routes | Complete — acceptance verified |
| MSE-403 | Implement probability and statistical inference routes | Not started — next |
| MSE-404 | Implement prediction, evaluation and explanation routes | Not started |
| MSE-405 | Verify loopback binding, CORS, redacted logging and input limits | Not started |
| MSE-406 | Implement and pass FastAPI contract tests | Not started |
| MSE-501 | Build shared React layout, router, API client and request states | Not started |
| MSE-502 | Build Dataset Explorer and labeled charts | Not started |
| MSE-503 | Build Probability Analysis | Not started |
| MSE-504 | Build Statistical Inference | Not started |
| MSE-505 | Build Spam Detector with dual model results | Not started |
| MSE-506 | Build Model Evaluation and confusion matrices | Not started |
| MSE-507 | Verify responsive behavior, keyboard access and error/stale states | Not started |
| MSE-601 | Execute all critical T01–T08 scenarios with evidence | Not started |
| MSE-602 | Verify security, privacy, offline use and measured performance | Not started |
| MSE-603 | Independently verify math, provenance and model integrity | Not started |
| MSE-604 | Complete university report with real screenshots and measurements | Not started |
| MSE-605 | Finalize installation README and classroom demo script | Not started |
| MSE-606 | Freeze v1.0 and record known limitations after release gates pass | Not started |

## Verification and delivery evidence

- **MSE-402 — Typed dataset summary statistics and distribution APIs:** 332 tests passed under Gravitas; Ruff clean. A02–A04 responses match pure services for all/train/test; actual totals 5862/4689/1173 and source/class counts reconcile. Histograms sum correctly and document frequencies obey filters. Exclusions are explicitly global before split (184 total, 130 duplicates, 54 parse rejects), not invented per-partition counts. Invalid queries return redacted 422; missing data 503; dataset endpoints work without models.

- **MSE-401 — Truthful FastAPI readiness and redacted shared errors:** 319 tests passed under Gravitas; Ruff clean. Factory supports isolated roots, typed health and common error schemas. Missing/corrupt artifacts degrade safely; models can be unavailable while dataset remains usable. SHA cache catches same-size/same-time tampering and recovers without restart. Validation/404/500 responses omit request values and paths. Actual healthy dataset/model/evaluation snapshot verified; cached health averaged .033 seconds.

- **MSE-307 — Measured model card and Gate 3 completion:** 314 tests passed under Gravitas; Ruff clean. Model card is generated from measured evaluation and verified against every model metric, dataset/split/test/artifact identity and actual inference. Historical sampling, near duplicates/dependence, calibration, one-split selection and false-positive limitations are explicit. Gate 3 complete without API/UI. Corrected inherited API documentation whitespace and added fail-fast final delivery checks after the earlier orchestration mistake.

- **MSE-306 — Transient dual-model inference and faithful log-odds explanations:** 314 tests passed under Gravitas; Ruff clean. Per-token contributions plus class prior, omitted-present remainder and Bernoulli absent-feature aggregate reconcile with public model log-probabilities on fixtures and actual models. Repetitions, class-column lookup, unknown tokens, blank/control-only text and 50000-character bounds verified. Predictions do not echo or persist submitted text; model file hashes remain unchanged.

- **MSE-305 — Identical held-out model evaluation with reconciled metrics:** 303 tests passed under Gravitas; Ruff clean. Both models use the same 1173 test IDs/hash; sklearn independently matches all confusion counts and accuracy/precision/recall/F1. Actual Multinomial TN814 FP8 FN14 TP337, accuracy .9812446717817562; Bernoulli TN815 FP7 FN70 TP281, accuracy .9343563512361467. Report is byte-repeatable, zero denominators are null with notes, no fitting/tuning occurs in evaluation.

- **MSE-304 — Trusted model persistence and provenance verification:** 298 tests passed under Gravitas; Ruff clean. All three binary hashes and strict metadata are checked before any unpickling; bounded fixed local files reject links, staleness, runtime/split mismatches and corruption. Publication rollback and owner-only permissions verified. Actual cross-process deterministic training/reload preserves original provenance; artifact ID 747bb5f51c2d231140efcc17d1316be68407d07fa9f9a7adcca1b3df2ce01ca3. Models and metadata remain ignored.

- **MSE-303 — Bernoulli Naive Bayes on shared binary presence:** 279 tests passed under Gravitas; Ruff clean. Binary conversion handles sparse zeros/invalid counts and preserves original matrices. Manual Bernoulli likelihoods and full scores including absent features match predictions; repetition and held-out labels cannot alter the fit. Actual classifiers share 4689 training IDs and 60135 features with finite inference.

- **MSE-302 — Multinomial Naive Bayes on shared count vectors:** 276 tests passed under Gravitas; Ruff clean. alpha=1 feature likelihoods and priors match manual Laplace/softmax calculations; held-out label mutation cannot affect fitted parameters. Actual model fits 4689 training rows with 60135 fixed features and class counts 3285 ham/1404 spam; finite inference verified. Persistence/evaluation remain later tasks.

- **MSE-301 — Shared training-only vocabulary and count features:** 274 tests passed under Gravitas; Ruff clean. Actual matrices are 4689x60135 and 1173x60135. All 60135 vocabulary terms come from training records; 12200 held-out-only tokens are excluded. Feature mapping hash f7ba4c18eef3aa09cacedf7f2518f4c97431a56d2f06c7f9c0c08a5af4402937 and matrices reproduce. Held-out text/labels cannot change fitted training features; no model fitting or persistence yet.

- **MSE-207 — Numerical verification evidence and Gate 2 completion:** 267 tests passed under Gravitas; Ruff clean. Executable report verifies 13 independent checks across descriptive/Bayes/binomial/Pearson/Wilson examples, with strict relative tolerance for the tiny p-value. Actual aggregate scopes carry dataset/split/input provenance; report reproduces byte for byte. Statistics engine works without model artifacts or UI; Gate 2 complete.

- **MSE-206 — Wilson spam-proportion confidence intervals:** 264 tests passed under Gravitas; Ruff clean. Known 300/1000 interval matches rounded .2724–.3291; boundaries, empty samples, confidence limits and independent normal quantiles verified. Actual 95 percent interval for 1755/5862 is .2877962371144159–.3112382719988152; train/test intervals independently matched. Historical-sample limitations are explicit.

- **MSE-205 — Pearson chi-square with expected-count suitability checks:** 240 tests passed under Gravitas; Ruff clean. Synthetic table gives chi-square 280, df=1 and p=7.50924e-63 with correction disabled. Expected counts below 5 never produce automatic decisions; zero expected counts yield null statistics. Actual free association matches independent SciPy for all/train/test (703.7827464/591.5580088/113.6506405). Independence/causation caveats are explicit.

- **MSE-204 — Bernoulli and binomial probability demonstrations:** 221 tests passed under Gravitas; Ruff clean. PMF for p=.25 n=10 k=1 is .1877117156982422; p=0/1, complete mass and independent SciPy values verified. Trials/successes are bounded integers, nonfinite probabilities rejected, empty denominators remain undefined and independence assumptions are explicit. Actual corpus formula checks passed for all scopes.

- **MSE-203 — Empirical word-document contingency and probabilities:** 201 tests passed under Gravitas; Ruff clean. Synthetic 1000-row table gives prior .3, word .25, joint .18, likelihood .6 and posterior .72. Actual free counts independently checked: all spam 811/1755 and ham 577/4107; train 661/1404 and 460/3285; test 150/351 and 117/822. Zero denominators return null and explanatory notes.

- **MSE-202 — Histogram boxplot and document-frequency aggregates:** 191 tests passed under Gravitas; Ruff clean. Numeric histograms reconcile with NumPy, constants/empty subsets and linear boxplots verified; repeated words count once per document. Actual histograms and selected counts reconcile for all 9 scope/class combinations.

- **MSE-201 — Descriptive statistics for count metrics:** 181 tests passed; Ruff clean. Known [2,4,4,6] mean/median/mode=4, variance=8/3, Q1=3.5/Q3=4.5. Empty/singleton and mode ties verified. Actual all/train/test class sizes, means and variances independently reconciled; all=4,107 ham/1,755 spam. Continuous completion through MSE-606 is authorized and persisted in AGENTS.md.

- MSE-106: **166 pytest tests passed** (39 new split cases plus 127 existing);
  Ruff passed across backend app/scripts/tests and bootstrap code. Fixtures
  cover known allocation/rounding, canonical input order, unsupported class
  support, duplicate IDs, full ingestion/dedup/conflict/split isolation and repeat
  runs, joined scopes and caller mutation, missing/forged/stale artifacts,
  recomputed forged membership hashes, bounds/locks/symlinks and rollback.
- Actual split ID:
  `e10ea9f8b406c62d14a359dd864ef2a195c8c1960c2747f1feaaea313c148c31`.
  Train membership SHA-256:
  `ebdc9c2d96e190b73037a5291087592ad00ab167309bdea1c6aaae037e038700`;
  test membership SHA-256:
  `64aef20395f55f37509281df5bf20a90846bf0e7b8b1a4842013df44b02a2629`.
  Two actual split runs produced byte-identical manifests. Independent CSV
  reading checked exact coverage/labels/counts/content isolation/rounding and
  matched a direct StratifiedShuffleSplit invocation. All five upstream file
  hashes and original raw checksums are unchanged; dataset identity is preserved.
- MSE-106 final command:
  `python3 .agents/skills/gravitas/scripts/verify.py --cmd 'python3 .gravitas/sessions/MSE-106/verify.py'`.
  It returned **VERDICT: PASS** after full suite/lint, real parse → retain →
  split reproduction, independent checks and staged privacy/ignore/diff checks.
  All upstream hashes stayed unchanged, and the split manifest matched the
  first real run byte for byte. Graphify produced **203 nodes, 337 directed
  edges and 14 communities**; all 39 statuses reconcile (6 complete, 33 not
  started) and MSE-201 retrieves as next. Verify the Git push result before
  claiming delivery. No frontend changes or browser/build checks belong to
  this backend task. Ignored session files are not a full installed Gravitas
  CLI/hook runtime.
- MSE-105: **127 pytest tests passed** (36 new dataset/tokenizer cases plus the
  previous 91); Ruff passed across backend app/scripts/tests and bootstrap code.
  Fixtures cover within/across-group duplicates, full conflicting-label groups,
  deterministic representative/order, Unicode/case/punctuation/zero-token rows,
  empty input, hash collisions, complete exclusion/provenance accounting,
  missing/stale/corrupt inputs and outputs, forged report hashes/config/types,
  privacy, limits/locks/symlinks and rollback with/without previous artifacts.
- Actual retained CSV: **24,182,963 bytes**, SHA-256
  `cfb3aca92056ab548d694e0d501ba3d336202e6c42c237b069d6ad705d990d6f`.
  Dataset ID: `ccd3321b252f22aaa5e6e1e74d96140b46c088a15474e8607c6259b2467c9c7a`.
  Final acceptance confirmed repeated-run byte identity, independently grouped
  parsed text/labels, read CSV, compared token counts with sklearn's unfitted
  analyzer, reconciled every exclusion/count and confirmed unchanged input/raw
  hashes. No private text or member filename is staged. Frontend is unchanged;
  browser/build checks do not apply to this backend-only task.
- MSE-105 final acceptance command:
  `python3 .agents/skills/gravitas/scripts/verify.py --cmd 'python3 .gravitas/sessions/MSE-105/verify.py'`.
  It returned **VERDICT: PASS**, including the actual preparation/verification,
  full suite, independent cross-check and staged privacy/ignore/diff checks.
  Graphify produced **201 nodes, 335 directed edges and 14 communities**;
  all 39 ticket statuses reconcile (5 complete, 34 not started) and MSE-106
  retrieves as next. Local session artifacts remain ignored; no installed
  Gravitas CLI/hook runtime is claimed. Verify Git delivery against the remote.
- MSE-104: **91 pytest tests passed**, including 53 new MIME/archive/ingestion
  cases plus the previous 38. Ruff passes across app, scripts and tests.
  New tests cover encoded/invalid charsets, multipart/related/alternatives,
  attachment suppression, HTML resources/scripts, structural defects, byte/
  header/part/depth/text/expanded/member/output limits, traversal/links/sparse/
  special/duplicate archive members, deterministic IDs, private/public separation,
  verifier tampering and rollback at replacement/validation failures.
- Two actual ingestion runs produced byte-identical private JSONL, report and
  source manifest. Private output: **25,868,309 bytes**, SHA-256
  `7241dcfcf5480609ed1c2c1d8e3e38d86e9394fbc512114b22a7284d4914114d`.
  Independent checks reconcile row IDs, text hashes, per-class/group counts,
  rejection IDs and metadata; archive bytes and original acquisition fields
  remain unchanged. CLI prints aggregates only. No mail text/member name is
  committed; frontend was unchanged, so browser/build checks were not applicable.
- MSE-104 final command:
  `python3 .agents/skills/gravitas/scripts/verify.py --cmd 'python3 .gravitas/sessions/MSE-104/verify.py'`.
  It returned **VERDICT: PASS** after lint/full tests, actual ingestion/verification,
  independent source/output checks, ignore/privacy/diff checks and graph
  freshness/status retrieval. Graphify produced **199 nodes, 331 directed edges
  and 16 communities**; all 39 statuses reconcile (4 complete, 35 not started),
  with MSE-105 retrieved as next. Session files are ignored, not a full installed
  Gravitas hook runtime. Observe the Git push result before claiming delivery.
- MSE-103: **38 pytest tests passed**, covering 29 acquisition regressions plus
  the existing nine environment/bootstrap tests. Ruff passed for backend app,
  scripts and tests. CLI download/verify succeeded for all five actual archives;
  a separate stdlib pass independently recomputed each size and SHA-256.
- Actual cache reuse was exercised with a forbidden-network opener: verification
  and download succeeded offline and left manifest bytes unchanged. Tests cover
  corrupted/missing/refetched bytes, pinned upstream mismatch, invalid metadata,
  duplicate groups, partial network failure, redirects, size/header bounds,
  local path/lock guards and failed manifest-write cleanup.
- Canonical selection was checked against the official corpus index/README:
  20030228 easy_ham/easy_ham_2/hard_ham/spam and corrected 20050311 spam_2.
  Byte hashes establish this acquisition's reproducible inputs. At that milestone,
  parsing/retained message counts were pending, with no release gate
  or model/statistical result claimed by acquisition alone.
- MSE-102: a source-only exported checkout started with no `.tools/`, frontend
  dependencies, backend environment or agent directories. The documented Node
  install, `npm ci`, frozen uv sync, lock check, dependency check, frontend
  lint/build, Ruff and **9 pytest tests** all passed there. **33 development
  packages** installed; the npm lock, uv lock and regenerated requirements
  export remained byte-identical after setup/checks.
- A second new Python environment installed **24 runtime-only packages** with
  `uv pip sync --require-hashes` from the export and imported the scientific/API
  stack successfully without pytest. Recharts imports with pinned React 19.3.1.
  npm engine-strict rejected an isolated wrong-runtime fixture; cached Node
  reuse verified its exact Node/npm versions without another download.
- Seven live HTTP checks against the fresh environments passed, including
  scaffold/API schema and absent domain endpoints. Both listeners were loopback
  only. Chromium captures at 1366×768 and 390×844 rendered correctly; local
  screenshots are ignored under `.impeccable/review/mse102/`.
- Setup verification platform: Linux x86_64. macOS/arm64 archive selection is
  present in the installer but untested; native Windows is unsupported by this
  wrapper. No real corpus/model results or later acceptance gates were claimed.
- MSE-108 verification passed **60 ignored-path cases and 35 trackable-path
  cases**. All **119** previously tracked tooling files remain locally with
  unchanged SHA-256 hashes; no tooling or ignored files remain in the index.
  Shared links and graph checks pass both locally and in an exported checkout
  without tooling directories. Staged/unstaged diff-hygiene checks passed.
  Command: `python3 .agents/skills/gravitas/scripts/verify.py --cmd 'python3 .gravitas/sessions/MSE-108/verify.py'`;
  result: `VERDICT: PASS`. These are configuration/documentation checks; app
  runtime tests were not rerun for that maintenance-only change. MSE-102 was
  the next application ticket at that point.
- MSE-101: frontend `npm run lint` passed with zero warnings; `npm run build`
  succeeded with Vite 8.3.8. Python compilation of `backend/app/` passed.
- A clean frontend `npm ci --no-audit --no-fund` installation succeeded from
  the lockfile, and `npm ls --depth=0` confirmed the declared dependency tree.
  The scoped acceptance command
  `python3 .agents/skills/gravitas/scripts/verify.py --cmd 'python3 .gravitas/sessions/MSE-101/verify.py'`
  returned `VERDICT: PASS` using the working Node runtime on PATH and the live
  local servers. This ignored session validator combines lint/build, Python
  parsing, HTTP, binding, structure/ignore, graph and diff-hygiene checks.
- Seven live HTTP checks passed: API greeting, OpenAPI containing only `/`,
  Vite HTML and transformed React module; future `/api/v1/health`,
  `/api/v1/dataset/summary` and `/api/v1/predict` returned 404. Listener checks
  confirmed Uvicorn at `127.0.0.1:8000` and Vite at `[::1]:5173`.
- Impeccable/Chromium captured and visually verified the React page at
  1366×768 and 390×844. Text rendered and wrapped correctly. Captures are local
  ignored artifacts at `.impeccable/review/mse101/`.
- Structure/ignore checks passed for 14 planned directories, nine sensitive or
  generated paths and six intended trackable paths. At that milestone no unit
  suite existed; runtime/browser smoke checks are the evidence for that ticket,
  not a claim that the statistical acceptance scenarios pass.
- MSE-100 preparation verification passed 218 structural checks; its follow-up
  passed 83 checks. Those counts describe the earlier documentation baseline.
- MSE-107 observed results: Graphify 0.9.112 produced **186 nodes, 315 directed
  edges and 13 communities**. Integrity/freshness checks passed for all 39
  ticket statuses and dependencies, document links, workflow order and legacy
  file cleanup. Real Graphify query/explain results identify MSE-101 as next;
  `path MSE-106 MSE-101` follows four explicit prerequisite edges. Isolated
  regression checks rejected edited, added and removed source documents; an
  unchanged rebuild produced byte-identical JSON, HTML and report artifacts.
- Verification commands (rerun after every final handoff edit):
  `memory/.venv/bin/python memory/graph.py build`, then
  `python3 .agents/skills/gravitas/scripts/verify.py --cmd 'memory/.venv/bin/python memory/graph.py check'`.
  Exercise Graphify `query`, `explain` and directed dependency `path` against
  `memory/graphify-out/graph.json`. Check source freshness, all 39 ticket/status
  records, dependency direction, graph references, removed legacy paths and
  maintained-file diff hygiene. Results belong in the final delivery report.
- Branch `main` tracks `origin/main` at
  `https://github.com/hixam001/mail-sense.git`. Preparation was pushed through
  MSE-105 commit `53576d9`. MSE-106 uses
  `MSE-106: Freeze reproducible stratified corpus split`.
  Observe the new commit and push result in Git. On resume, check `git log -1`,
  `git status -sb` and the upstream branch before claiming delivery.

## Environment notes and recovery

- The distro `node`/`npx` fails with missing `libsimdjson.so.36`. MSE-102 replaces
  the earlier ephemeral workaround with the committed Node installer/wrapper;
  use the README/SETUP commands. No system library or global Node repair was made.
- Authoritative runtime/dependency pins are in the version files, package
  manifest, backend pyproject and locks. Backend dependencies live in ignored
  `backend/.venv/`, separate from Graphify. uv writes its user cache and may need
  authorized cache-write permissions under the agent's restricted sandbox.
- Initial tests exposed a Starlette deprecation for legacy httpx. The pinned
  dev client now uses httpx2, as recommended by the installed Starlette code;
  all nine tests pass without suppressing warnings.
- MSE-104's restricted full-suite run stalled in the existing FastAPI TestClient
  case after 66 cases. Interrupting and rerunning with authorized sandbox
  escalation completed all tests in about one second. Use the necessary uv
  cache/test-client permissions rather than assuming the parser has stalled.
- Impeccable could not autodetect the cached Chromium browser. Visual checks
  worked with `IMPECCABLE_BROWSER` pointing to
  `~/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome`. That path is
  workstation-specific; inspect available browsers before reusing it.
- Gravitas skill files and Python verification wrapper exist. No `gravitas`
  CLI was found on PATH; do not claim a full runtime or hook-enforced task
  contract is installed. Use the shipped verification runner with an explicit
  appropriate command when automatic validator discovery is unavailable.
- Graphify 0.9.112 is installed in ignored `memory/.venv/` using Python 3.12.
  Recreate it from `memory/requirements.txt` when absent. No global Graphify
  hooks, external model APIs or cloud-memory service are required for this
  graph. Extraction covers explicit document structure and ticket relationships;
  it is not an exhaustive semantic understanding of every sentence.
- GitHub access failed within the restricted network sandbox and succeeded with
  authorized network escalation. Request the actual needed sandbox permission
  when required; do not repeatedly retry unchanged failed commands.
- The first HTTPS push failed with `could not read Username`: Git has no
  configured credential helper. `gh auth status --hostname github.com` confirmed
  an active `hixam001` login in the keyring, with repository access. Use that
  existing login without changing global settings:
  `git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push -u origin main`.
  Verify the remote commit after pushing. Do not print tokens or create another
  account/login merely to repair the missing helper.
- No app process is running and no live-preview configuration exists.
- Future landing/showcase build-path preference remains unset. Current app
  screens use code-first. No marketing surface is in the approved v1 scope.

## Resume/update checklist

After each implementation: update completed work and affected ticket statuses,
record exact commands/results and unresolved issues, name one actionable next
ticket, and keep the remaining inventory complete. Validate the final edits,
commit with that ticket ID and push without additional contributor credits.
If checks or a push fail, record the failure and recovery action instead of
marking the work verified or delivered.
