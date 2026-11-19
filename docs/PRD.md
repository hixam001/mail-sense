# MailSense — Product Requirements Document (PRD)

**Version:** 1.0 (approved baseline)  
**Date:** 2026-11-19  
**Project:** MailSense — Statistical Analysis and Probabilistic Email Spam Detection  
**Audience:** University evaluators, student developers, and project reviewers  
**Status:** Requirements approved; implementation not started

## 1. Problem statement

Students often encounter probability and statistics as isolated formulas without observing how estimates, distributions, inference, and uncertainty can support a practical decision. Typical spam-filter demonstrations emphasize machine-learning accuracy while hiding the mathematical reasoning. MailSense addresses that gap with a local, interactive application that analyzes the historical Apache SpamAssassin Public Corpus and shows how empirical probabilities and statistical tests relate to two Naive Bayes email classifiers.

MailSense is an **educational analytical tool**, not a production email security solution. The user will inspect data, ask probability questions, test associations, paste an email, and compare Multinomial and Bernoulli Naive Bayes outputs.

## 2. Goals and SMART objectives

| ID | Objective | Measurable acceptance target | Verification |
|---|---|---|---|
| G1 | Make probability visible | Show prior, joint, conditional and Bayes posterior probabilities with counts and denominators for a chosen word | Worked-case walkthrough |
| G2 | Teach descriptive statistics | Present mean, median, mode, quartiles, variance, standard deviation and at least three chart types for email-length/word-count summaries | UI/API test |
| G3 | Demonstrate inference | Return one interpretable chi-square independence test and a proportion confidence interval, showing assumptions and limitations | Known-table numerical test |
| G4 | Compare probabilistic classifiers fairly | Train and evaluate both Naive Bayes models using the same deterministic 80/20 stratified split, documenting accuracy, precision, recall, F1 and confusion matrices | Reproducible training run |
| G5 | Deliver a self-contained demonstration | Run the app on a single computer with a React frontend and FastAPI backend, no accounts and no external inference API | Offline demo checklist |

Goals are completion criteria, **not claims of achieved results**. No minimum accuracy figure is promised before measurement.

## 3. Product success metrics

| Metric | Definition | Target |
|---|---|---|
| Core workflow completion | Dataset → statistics → probability → inference → both predictions → comparison | 100% of steps demonstrable |
| Mathematical verification | Preselected numerical worked examples matching independent calculations within floating-point tolerance | All mandatory examples pass |
| Evaluation integrity | Test messages excluded from vocabulary fitting/training and split reproducible | 100% of validation checks pass |
| Interface reliability | Critical flows function for success, missing-model, empty-input and backend-offline cases | All acceptance tests pass |
| Privacy and locality | No email submission to external services; backend bound locally | Confirmed by configuration and demo |

## 4. Target personas

### Persona A — Statistics student
- **Profile:** Undergraduate student (approximately 18–25), introductory probability/statistics coursework; beginner-to-intermediate programming experience.
- **Pain points:** Difficult to connect Bayes' theorem, conditional frequencies and p-values to real outcomes.
- **Goal:** Explore a worked dataset, change a selected word, verify each formula and explain results in class.
- **Technology comfort:** Comfortable using a web browser; not expected to run Python notebooks.

### Persona B — Instructor or examiner
- **Profile:** University instructor/teaching assistant reviewing a practical course project; varied programming familiarity.
- **Pain points:** Black-box classification demos do not prove understanding of statistical methods or fair testing.
- **Goal:** Check underlying counts, assumptions, repeated calculations, classification metrics and limitations quickly.
- **Technology comfort:** Browser use and basic interpretation of statistical results; optional familiarity with source code.

## 5. Features, user stories and acceptance criteria

### P0 — Required for version 1.0

#### F1. Corpus exploration and descriptive analytics
**Story:** As a student, I want to explore spam and ham characteristics so that I can describe the dataset before building a model.

Acceptance criteria:
1. Corpus summary shows total retained messages, class counts, class proportions and source groups.
2. Length and word-count statistics include mean, median, mode, quartiles, variance and standard deviation, labeled by unit and subset.
3. Histograms, box plots and top-word frequency views are accessible, with empty and error states.
4. Sources, exclusions, invalid records and duplicate counts are disclosed in the preprocessing report.

**Success metric:** A reviewer can reproduce at least three displayed summary statistics from supplied example values.

#### F2. Probability laboratory
**Story:** As a student, I want to examine a word's relationship with spam so that I can apply probability formulas to real counts.

Acceptance criteria:
1. A selected normalized word produces a 2×2 spam/ham × present/absent table.
2. Prior, joint, conditional, likelihood and Bayes posterior values are presented with denominators.
3. Zero-count and missing-vocabulary cases are handled with explicit messages; raw frequency-based and smoothed model values are not conflated.
4. Bernoulli and binomial examples explain their independence/trial assumptions.

**Success metric:** A manual worked example matches output within an explicitly documented numerical tolerance.

#### F3. Statistical inference
**Story:** As an examiner, I want to inspect a word association test and confidence interval so that I can assess the statistical argument.

Acceptance criteria:
1. The independence test reports hypotheses, observed/expected tables, statistic, degrees of freedom and p-value.
2. A clear warning appears when chi-square expected-count assumptions are unsuitable.
3. The spam proportion confidence interval reports method, confidence level, estimate and bounds.
4. The interface explains that statistical significance does not establish causation.

**Success metric:** Numerical output matches a known reference contingency-table calculation.

#### F4. Dual Naive Bayes spam detector
**Story:** As a student, I want to paste email text and compare two classifiers so that I can understand different probability assumptions.

Acceptance criteria:
1. A nonempty subject/body text input returns both Multinomial and Bernoulli predictions.
2. Each prediction includes a model-estimated spam probability and a short, faithful explanation of influential terms.
3. An invalid, overlong or whitespace-only input is rejected without a false success state.
4. Inputs do not leave the local computer or persist as a message history.

**Success metric:** Both trained models return valid class labels and probabilities in the range [0, 1].

#### F5. Model evaluation and comparison
**Story:** As an examiner, I want a reproducible, side-by-side comparison so that I can judge effectiveness beyond accuracy.

Acceptance criteria:
1. Both classifiers are evaluated against **the same untouched test split**.
2. Confusion matrices show TP, FP, TN and FN under the declared positive class `spam`.
3. Accuracy, precision, recall, F1 and spam false-positive rate are shown for each model.
4. UI explains class imbalance, probability calibration limitations and the age of the dataset.

**Success metric:** Metrics are reproducible from persisted predictions and ground-truth labels.

### P1 — Important implementation quality (included)

#### F6. Usable educational interface
**Story:** As a student, I want readable charts, navigation and explanations so that I can complete the demonstration without interpreting raw API output.

Acceptance criteria:
1. Dashboard navigation exposes all five major analytical modules.
2. All API-dependent screens provide loading, empty, success and error states.
3. Charts label axes, units, population/subset and class clearly.
4. Interface supports normal laptop widths and keyboard access to primary controls.

**Success metric:** Demo walkthrough can be completed without direct API calls.

### P2 — Future possibilities, explicitly excluded from v1.0
- Modern dataset benchmarking, multi-model hyperparameter search, model calibration tools.
- Downloadable PDF reporting, background training queues, user-defined dataset uploads.
- Email-provider integrations and hosted multi-user deployments.

## 6. Explicitly out of scope

1. Email accounts, authentication, password reset or user roles.
2. Reading, sending, forwarding or deleting actual inbox messages.
3. Production spam blocking or real-time mail-server integration.
4. Network reputation lookups, DNSBL, URL fetching or remote APIs.
5. Cloud hosting or multi-user synchronization.
6. Relational database, user activity history or persistent predictions.
7. Neural networks, transformers or generative AI models.
8. Training by user-facing API during normal demo operation.
9. Guaranteed classification accuracy or calibrated probability claims.
10. General-purpose arbitrary dataset import in the v1.0 UI.

## 7. User scenarios

### Scenario S1 — Explore whether a word is associated with spam
1. Student opens `http://localhost:5173` and chooses **Dataset Explorer**.
2. React requests dataset metadata and displays class counts, word-count distributions and valid subset labels.
3. Student opens **Probability Analysis**, enters `free`, and receives a document-presence contingency table.
4. App shows empirical probabilities, including `P(spam | free)`, with formula substitutions.
5. Student moves to **Statistical Inference** and runs a chi-square test on the same 2×2 table.
6. The interface interprets the result, flags insufficient expected counts, if applicable, and warns that association is not causation.

**Expected:** Student can articulate a probability and statistical inference conclusion.  
**Edge/error:** Blank or unrecognized word yields validation/no-observations feedback; disconnected backend yields retry state, not invented output.

### Scenario S2 — Compare classifier predictions
1. Student opens **Spam Detector** and pastes subject/body text.
2. UI validates length, submits once to `/api/v1/predict`, and shows progress.
3. Backend loads pre-trained models, transforms input using training-fitted vocabulary, and computes both predictions.
4. UI displays prediction labels, estimated spam probabilities, comparison/agreement, and feature explanations.
5. Student opens **Model Evaluation** to interpret expected failure types and class imbalance.

**Expected:** Both classifications are shown with limitations.  
**Edge/error:** Input of only spaces or above limit is rejected; missing artifacts produce model-unavailable error with a setup instruction.

### Scenario S3 — Instructor verifies scientific integrity
1. Instructor opens **Dataset Explorer** and checks number of included/excluded messages and split manifest.
2. Instructor checks **Statistical Inference** output against a worked 2×2 example.
3. Instructor opens **Model Evaluation** and verifies both models share split ID and positive label `spam`.
4. Instructor checks confusion matrix arithmetic against precision, recall and F1.
5. Instructor reruns offline after installing dependencies and artifacts from the project package.

**Expected:** Work is reproducible, with no training/test leakage or hidden data source.  
**Edge/error:** Missing dataset/model files are reported as explicit readiness blockers rather than fictitious results.

## 8. Non-functional requirements

- **Performance:** After setup and artifact load, 95% of single-email prediction requests on the demo laptop should finish in ≤ 3 seconds; dashboard requests should usually finish in ≤ 5 seconds. Measure and report actual hardware/timing; this is a target, not a guarantee.
- **Security/privacy:** Bind backend to loopback, allow CORS only from local frontend origin, reject huge inputs, do not execute HTML/scripts or load external resources from messages, and avoid logging email bodies.
- **Accessibility/usability:** Legible chart labels, keyboard-accessible forms, visible validation, text alternatives for color distinctions, sensible error messages.
- **Reliability:** Deterministic split/seed and saved model artifacts; malformed corpus records logged and skipped with counts.
- **Offline operation:** No external network requirement once corpus and dependencies are installed.
- **Maintainability:** Separate frontend, API routes, mathematical services, parsing, training and persistence modules; core mathematical functions unit-tested.

## 9. Dependencies and constraints

- **Locked stack:** React + Vite; FastAPI; Python; Pandas/NumPy/SciPy/scikit-learn; local file storage; Matplotlib for static report figures and Recharts for browser charts.
- **Corpus:** Apache SpamAssassin Public Corpus; download once from `https://spamassassin.apache.org/old/publiccorpus/` and document exact archives. Raw archives have overlapping dated revisions—select one canonical recent snapshot per collection, not every revision concatenated.
- **Rights/privacy:** The original corpus notice states message content copyright remains with its senders; do not casually redistribute extracted messages in a public repository. The corpus must not be sent into a live email system.
- **Data limitation:** Historical early-2000s messages are not representative of all modern mail. The test set is a held-out subset from that historical corpus.
- **Team assumption:** Small student team / single-machine demo; no production SLOs.

## 10. Milestones and timeline

Calendar dates for coding cannot be finalized until the repo and team schedule exist. The following **relative work-package targets** are approved planning estimates, not committed deadlines.

| Milestone | Estimated duration | Deliverable |
|---|---:|---|
| M1: Data foundation | 2–3 working days | Corpus manifest, parser, deduplicated dataset, split |
| M2: Statistics engine | 3–5 working days | Probability, descriptive statistics, inference, unit tests |
| M3: Models | 2–4 working days | Both trained models, metrics, explanations |
| M4: Frontend | 4–6 working days | Five interactive modules and dashboard |
| M5: Integration/QA | 2–3 working days | Stable local end-to-end demonstration |
| M6: Report/delivery | 2–3 working days | Final report, README, acceptance checklist |

**Minimum demonstrable milestone:** Dataset → probability → chi-square → paste text → both predictions → comparison.  
**Version 1.0 acceptance:** All P0 and P1 criteria, test plan checks and documented limitations pass.

## 11. Project state and change control

This PRD documents the approved scope, not implemented functionality. Changes to the approved dataset, architecture, two-model comparison, local-only deployment or core educational modules require a recorded version change. See `SRS.md` for testable technical requirements and `IMPLEMENTATION_PLAN.md` for execution sequence.
