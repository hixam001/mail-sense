# MailSense

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Approved baseline: React with Vite for the frontend; Python with FastAPI for the
backend; NumPy, Pandas and SciPy for analysis; scikit-learn for both classifiers;
Recharts for browser charts, with optional Matplotlib for static report figures.
Storage uses local CSV/JSON/joblib artifacts, with no database.

## Users

- Undergraduate probability and statistics students who use a browser to explore
  data, verify formulas and explain results during coursework or a presentation.
- Instructors and examiners who need to inspect counts, mathematical assumptions,
  reproducibility and fair model comparisons without navigating raw API output.
- Student developers prepare the corpus and models through local CLI scripts
  before the demonstration. These audiences do not imply accounts or app roles.

## Product Purpose

MailSense — Statistical Analysis and Probabilistic Email Spam Detection — connects
probability and statistics to a practical email classification demonstration.
Students explore a historical corpus, inspect empirical probabilities and
statistical tests, then compare Multinomial and Bernoulli Naive Bayes predictions.

Success means a complete, mathematically verifiable local walkthrough from dataset
exploration through both predictions and held-out evaluation. Implementation,
accuracy, performance and acceptance tests remain unverified until measured.

## Positioning

The approved educational emphasis is probability and statistics first. Counts,
denominators, formulas, assumptions and limitations accompany results, while two
classifiers illustrate different probabilistic models on the same data. MailSense
is an academic analytical tool; production email security is outside its scope.

## Operating Context

A single computer runs the frontend on localhost and FastAPI on loopback. The app
works offline after dependencies, the corpus and trained artifacts are prepared.
Ingestion and training happen through developer CLI scripts, outside normal UI use.

The dashboard reports backend, dataset and model readiness. Five modules support
the core demonstration:

1. Dataset Explorer (`/dataset`): corpus provenance, retained class counts,
   descriptive statistics, histograms, box plots and word frequencies.
2. Probability Analysis (`/probability`): selected-word contingency counts,
   empirical probability formulas, and Bernoulli/binomial demonstrations.
3. Statistical Inference (`/statistics`): Pearson chi-square association testing
   and a Wilson spam-proportion confidence interval.
4. Spam Detector (`/detect`): pasted subject/body text, both predictions,
   model-estimated spam probabilities, agreement and faithful explanations.
5. Model Evaluation (`/evaluation`): shared split metadata, confusion matrices,
   accuracy, precision, recall, F1 and false-positive rate.

The dashboard route is `/`. Selected words and dataset scopes can carry between
related analyses; pasted email content must not appear in URLs or persistent
history. Normal laptop use and a classroom demonstration are the primary context.

## Capabilities and Constraints

- Use the official historical Apache SpamAssassin Public Corpus, selecting one
  canonical archive per group and recording provenance, exclusions and duplicates.
- Deduplicate before a stratified 80/20 train/test split with seed 42. Both models
  use a shared training-fitted vocabulary, identical untouched test IDs and initial
  Laplace smoothing `alpha=1.0`. The positive class is `spam`; `ham` is legitimate mail.
- Show counts, denominators, units and the selected `all`, `train` or `test` scope.
  Keep empirical frequencies distinct from smoothed model probabilities. A word
  with zero document frequency has an undefined empirical posterior, not 0% spam.
- Use Pearson chi-square without Yates correction, default significance `.05`,
  with expected-count checks and no automatic significance conclusion when the
  approximation is unsuitable. Use a two-sided Wilson interval, default 95%.
- Predictions accept nonempty pasted subject/body text up to 50,000 characters.
  Explain relevant class priors and token contributions, including Bernoulli
  absent-feature effects. Show disagreements transparently.
- Provide loading, empty, invalid-input, missing-artifact and backend-error states
  with actionable recovery. Dataset analytics can remain usable without models.
- Keep email processing local. Do not persist or log pasted email bodies, execute
  message HTML or attachments, or fetch message-linked remote resources.
- Exclude accounts, live inbox integration, mail sending, cloud hosting, external
  inference, arbitrary dataset uploads, runtime retraining, neural models and
  prediction history from version 1.0.
- Performance targets are warmed-up prediction p95 of at most 3 seconds and
  typical cached summaries within 5 seconds on documented demo hardware. These
  are acceptance targets, not achieved claims.

`docs/SRS.md` is the authoritative locked technical baseline. Scope, dataset,
stack, model or deployment changes require a recorded approved version change
and coordinated updates to the related contracts and tests.

## Brand Commitments

The approved product name is **MailSense**, with the descriptive title
**Statistical Analysis and Probabilistic Email Spam Detection**. Explanations must
be understandable to students and precise enough for academic verification.
The supplied documentation establishes no visual identity or binding aesthetic.

## Evidence on Hand

The README and documentation describe approved requirements and planned behavior:

- [README](README.md): locked decisions and documentation index.
- [PRD](docs/PRD.md), [SRD](docs/SRD.md) and [SRS](docs/SRS.md): users, purpose,
  scope and acceptance requirements.
- [Application flow](docs/APP_FLOW.md): routes, workflows and recovery states.
- [Architecture](docs/ARCHITECTURE.md), [API contract](docs/API_CONTRACT.md) and
  [data model](docs/DATA_MODEL.md): planned implementation boundaries and artifacts.
- [Statistical methods](docs/STATISTICAL_METHODS.md),
  [test plan](docs/TEST_PLAN.md) and
  [implementation plan](docs/IMPLEMENTATION_PLAN.md): mathematical definitions,
  synthetic fixtures, release gates and development sequence.

Source code for the local React/Vite and FastAPI hello-world scaffolds is
available in `frontend/` and `backend/`; the handoff records their runtime and
build verification. Local CLI services now acquire and parse the pinned corpus,
deduplicate exact text, exclude label conflicts and derive summary records.
The measured retained dataset has 5,862 records (4,107 ham, 1,755 spam); raw and
processed mail remain private and ignored. The verified seed-42 stratified split
has 4,689 training and 1,173 test records, joined by ID without changing retained
text. Pure statistics services and their numerical verification report now cover
descriptive summaries, distributions, probabilities, binomial demonstrations,
Pearson tests and Wilson intervals. Both Naive Bayes models now train on the shared frozen training features and
reload from verified private artifacts. Held-out evaluation, API integration
and product UI remain pending.
Documentation examples are synthetic
teaching fixtures unless explicitly identified as measured results. Model
scores and timings must be established during implementation. No accuracy or
calibration guarantee is approved. Historical corpus prevalence must not be
presented as a modern general-population estimate. Original corpus messages
must remain local and be excluded from public source distribution.

## Product Principles

1. Make the mathematical reasoning inspectable through counts, formulas and assumptions.
2. Preserve reproducibility and evaluation integrity across both classifiers.
3. Distinguish empirical evidence, synthetic examples, estimates and uncertainty.
4. Keep the demonstration local and pasted email text transient.
5. Make readiness and failures truthful, with a clear next action.

## Accessibility & Inclusion

Primary navigation and forms must support keyboard use. Provide legible chart
labels, visible validation, interpretable contrast, and text or other non-color
cues for spam/ham and status distinctions. Label chart axes, units, class and
dataset scope. Explain statistical terminology and assumptions without requiring
notebook or programming familiarity. No specific accessibility conformance level
is established in the approved requirements.
