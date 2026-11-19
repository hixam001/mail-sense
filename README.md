# MailSense — Project Documentation Pack

**Version:** 1.0 · **Requirements locked:** November 19, 2026  
**Status:** Documentation and agent workflow prepared; application implementation has not started. No application source code, dataset files or trained models are included.

> **MailSense — Statistical Analysis and Probabilistic Email Spam Detection** is a university probability-and-statistics application with two Naive Bayes classifiers. React + Vite frontend, Python + FastAPI backend, Apache SpamAssassin Public Corpus, and local deployment are the approved baseline.

## Documentation index

For ongoing development, read [AGENTS.md](AGENTS.md),
[memory/README.md](memory/README.md) and [memory/HANDOFF.md](memory/HANDOFF.md)
first. The handoff records completed work, the full remaining backlog,
verification evidence and the exact next task. [PRODUCT.md](PRODUCT.md) captures
the confirmed product context for design work. The memory directory also contains
a queryable Graphify graph and its interactive visualization.

| File | What it contains |
|---|---|
| `docs/PRD.md` | Product problem, users, goals, scoped features, scenarios and success metrics |
| `docs/SRD.md` | Short, authoritative summary of the approved build scope |
| `docs/SRS.md` | Locked functional/non-functional requirements and acceptance gates |
| `docs/API_CONTRACT.md` | FastAPI endpoints, parameter rules, sample JSON, response/errors |
| `docs/DATA_MODEL.md` | Local CSV/JSON/joblib artifact records and consistency rules; no database |
| `docs/APP_FLOW.md` | Screen inventory, navigation, user journeys, error and edge cases |
| `docs/ARCHITECTURE.md` | Module boundaries, processing/training/inference flows, repository layout |
| `docs/STATISTICAL_METHODS.md` | Formulas, manual examples, inference assumptions, both NB models and metrics |
| `docs/TEST_PLAN.md` | Critical/edge-case tests, numerical fixtures and demo acceptance checklist |
| `docs/IMPLEMENTATION_PLAN.md` | Phased development, dependencies, Jira-style MSE tickets and release gates |

## Locked decisions

- **Name:** MailSense
- **Primary academic focus:** Probability and statistics; machine learning is the applied demonstration.
- **Dataset:** Official historical Apache SpamAssassin Public Corpus. Select one canonical archive per group and record provenance; do not add outdated revisions as new messages.
- **Frontend:** React with Vite.
- **Backend:** Python with FastAPI.
- **Analysis:** NumPy, Pandas, SciPy; Recharts and optional Matplotlib for reports.
- **Classifiers:** Multinomial and Bernoulli Naive Bayes via scikit-learn, both mandatory.
- **Baseline evaluation:** Deduplicate first; stratified 80/20 train/test, random seed 42, `alpha=1.0`, shared training-fitted vocabulary and identical held-out test IDs.
- **Storage:** Local files only; no relational database.
- **Deployment:** Localhost-only; offline after dependencies and corpus are prepared; no authentication or real email integration.

## Next implementation steps

The requirements are present in `docs/`. Retain this documentation index until implementation adds actual installation/run commands. Follow:

1. `MSE-101`: Create frontend (`frontend/`) and backend (`backend/`) skeletons.
2. `MSE-102–106`: Establish local dependencies, safe corpus ingestion, content deduplication and deterministic split.
3. `MSE-201–207`: Implement and verify statistics independently from ML.
4. `MSE-301–307`: Fit/evaluate both Naive Bayes models.
5. `MSE-401–406`: Implement versioned FastAPI contract.
6. `MSE-501–507`: Build five frontend modules with real API results.
7. `MSE-601–606`: Run tests, collect evidence, finalize university report/demo.

**No commands for running MailSense are provided yet because no implementation exists.** Avoid copying fictitious setup steps into the final README.

## Authoritative change policy

`docs/SRS.md` is the locked technical baseline. Document intentional changes to dataset, stack, models, deployment, or scope as a new approved version and update API/data/flow/test documents together. Examples and scores in docs are **synthetic teaching fixtures unless explicitly labeled actual measured data**.

## Sources and responsible data use

- Official corpus index: <https://spamassassin.apache.org/old/publiccorpus/>
- Official corpus README: <https://spamassassin.apache.org/old/publiccorpus/readme.html>

The upstream corpus README cautions against sending the supplied messages into a live mail system and states that original message text rights remain with the original senders. Keep source emails local and exclude them from a public repo. Never present the historical corpus's class prevalence as a modern general-population estimate.
