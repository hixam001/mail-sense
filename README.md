# MailSense

**Version:** 1.0 · **Requirements locked:** November 19, 2026  
**Status:** 17/39 implementation tasks verified. Latest: MSE-304 — Trusted model persistence and provenance verification. Next: MSE-305. See [handoff](memory/HANDOFF.md) for current functionality and evidence.

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
| `docs/SETUP.md` | Pinned setup, run/check commands, corpus acquisition/parsing/verification, locks and recovery |
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

## Run the local scaffolds

Prerequisites: Python 3.12+ for bootstrap, **uv 0.13.9**, and initial network
access. From the repository root, install the pinned Node 22.23.5/npm 10.9.9 and
Python 3.12.15 application environments:

```bash
python3 scripts/node.py install
python3 scripts/node.py npm --prefix frontend ci
uv sync --project backend --frozen
```

The Node helper installs a checksum-verified official binary under ignored
`.tools/` and works without the system Node or an old `/tmp` installation.
See [the setup guide](docs/SETUP.md) for prerequisites and platform scope.

Start the frontend:

```bash
python3 scripts/node.py npm --prefix frontend run dev
```

In another terminal, start the backend:

```bash
uv run --project backend --frozen python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Open `http://localhost:5173/` for the frontend, `http://127.0.0.1:8000/` for the API greeting or
`http://127.0.0.1:8000/openapi.json` for its schema. These scaffolds run
independently. The `/api/v1` contract, readiness checks and
model endpoints are scheduled in later tickets.

### Scaffold checks

From the repository root:

```bash
python3 scripts/node.py npm --prefix frontend run lint
python3 scripts/node.py npm --prefix frontend run build
uv run --project backend --frozen ruff check --config backend/pyproject.toml backend/app backend/tests backend/scripts scripts
uv run --project backend --frozen pytest -c backend/pyproject.toml backend/tests scripts/tests
```

Frontend and backend locks are committed. Runtime downloads, `node_modules/`,
build output and Python virtual environments are ignored. Environment,
bootstrap, acquisition and parsing tests use synthetic fixtures; they do not establish correctness
of the unimplemented domain services or empirical model performance. See
[the setup guide](docs/SETUP.md) for lock maintenance and
[the handoff](memory/HANDOFF.md) for observed evidence.

## Corpus acquisition

From the repository root, after backend setup:

```bash
uv run --directory backend --frozen python -m scripts.download_corpus download
uv run --directory backend --frozen python -m scripts.download_corpus verify
```

The five canonical archives total **6,962,803 compressed bytes**. Their source
URLs, groups, labels, UTC acquisition times, sizes and SHA-256 values are recorded
in [source_manifest.json](data/processed/source_manifest.json). Raw downloads stay
under ignored `data/raw/`; verification and complete-cache reuse work offline.
The completed parsing run populates integer counters. See
[the setup guide](docs/SETUP.md#acquire-the-corpus) for selection and recovery.

## Parse the corpus

After acquisition, from the repository root:

```bash
uv run --directory backend --frozen python -m scripts.ingest_corpus run
uv run --directory backend --frozen python -m scripts.ingest_corpus verify
```

The measured run accepted **5,992 / 6,046 candidates**, rejected **54** for
malformed MIME structure, and ignored five archive control files. These are
**pre-deduplication counts**. The private intermediate stays in ignored
`data/processed/messages.parsed.jsonl`; the shareable
[parsing report](data/processed/parsing_report.json) records hashes, counts and
reason codes. Both runs produced byte-identical outputs. See
[setup and recovery](docs/SETUP.md#parse-the-corpus) and the
[parsing contract](docs/DATA_MODEL.md#implemented-parsing-contract-mime-v1).

## Prepare retained records

After parsing, from the repository root:

```bash
uv run --directory backend --frozen python -m scripts.prepare_dataset run
uv run --directory backend --frozen python -m scripts.prepare_dataset verify
```

The measured result is **5,862 retained records: 4,107 ham and 1,755 spam**.
From 5,992 parsed rows, 130 same-label duplicates were excluded across 96 groups;
no conflicting-label groups were observed. Conflicting groups are excluded in
full when present, as verified by synthetic fixtures. The ignored, owner-only
`data/processed/messages.csv` includes fixed token counts and preserved
provenance. The public [deduplication report](data/processed/deduplication_report.json)
records counts, versions, hashes and every excluded ID/reason. Split membership
is stored separately. See [setup](docs/SETUP.md#prepare-retained-records).

## Create the split

After retained-record preparation, from the repository root:

```bash
uv run --directory backend --frozen python -m scripts.split_dataset run
uv run --directory backend --frozen python -m scripts.split_dataset verify
```

The reproducible stratified 80/20 split uses seed 42:

| Partition | Ham | Spam | Total |
|---|---:|---:|---:|
| Train | 3,285 | 1,404 | 4,689 |
| Test | 822 | 351 | 1,173 |

The public [split manifest](data/processed/split_manifest.json) records sorted
IDs, class counts, configuration and hashes. Its ID join adds `split` to private
records in memory while preserving the retained CSV. No vocabulary or model is
fitted. See [split setup and recovery](docs/SETUP.md#create-the-split).

## Verify statistical methods

```bash
uv run --directory backend --frozen python -m scripts.verify_statistics run
uv run --directory backend --frozen python -m scripts.verify_statistics verify
```

The [verification report](artifacts/reports/statistics_verification.json) separates
synthetic worked examples from measured corpus aggregates and pins their inputs.
Thirteen numerical checks and the regression suite verify Gate 2 without models
or UI. Descriptive, distribution, empirical probability, binomial, Pearson and
Wilson services are implemented; the API and analytical screens follow later.

## Train local models

```bash
uv run --directory backend --frozen python -m scripts.train_models run
uv run --directory backend --frozen python -m scripts.train_models verify
```

The shared vocabulary and both alpha=1 Naive Bayes models fit the frozen training
partition. Private artifacts stay ignored under `artifacts/models/`; metadata
and checksums tie them to the dataset, split, feature mapping and runtime.
Only project-created artifacts are loaded. Held-out evaluation follows separately.

## Implementation sequence

The requirements and acceptance gates are documented in `docs/`. Delivery follows
this sequence; the handoff records current ticket status:

1. `MSE-101` (complete): Create frontend (`frontend/`) and backend (`backend/`) skeletons.
2. `MSE-102` (complete): Pin runtimes/dependencies and verify reproducible setup.
3. `MSE-103` (complete): Acquire canonical archives and verify their provenance/checksums.
4. `MSE-104` (complete): Safely extract and parse MIME to private canonical text with verified counts.
5. `MSE-105` (complete): Deduplicate, reject label conflicts and derive retained summary records.
6. `MSE-106` (complete): Create a deterministic stratified split with verified disjoint IDs.
7. `MSE-201–207` (complete): Implement and verify statistics independently from ML.
8. `MSE-301–307` (next): Fit/evaluate both Naive Bayes models.
9. `MSE-401–406`: Implement versioned FastAPI contract.
10. `MSE-501–507`: Build five frontend modules with real API results.
11. `MSE-601–606`: Run tests, collect evidence, finalize university report/demo.

The available commands run the scaffolds and acquire, parse, deduplicate, split and verify the corpus.
Later tasks add statistics, training and analytical workflows.

## Authoritative change policy

`docs/SRS.md` is the locked technical baseline. Document intentional changes to dataset, stack, models, deployment, or scope as a new approved version and update API/data/flow/test documents together. Examples and scores in docs are **synthetic teaching fixtures unless explicitly labeled actual measured data**.

## Repository hygiene

Agent installations and local tooling state (`.agent/`, `.agents/`, `.codex/`,
`.gravitas/`, `.impeccable/`) are ignored and must be installed/configured locally
on a fresh clone. Previously tracked tooling has been untracked; local copies
are retained. `AGENTS.md`, `memory/`, application source and lockfiles stay in Git.

The ignore rules also cover credentials, environments, dependency directories,
caches, builds, test output, raw corpus messages, processed message files and
trained models. Source/split manifests and evaluation reports remain trackable,
along with the empty data/model directory placeholders. Do not force-add local
tooling or sensitive data.

## Sources and responsible data use

- Official corpus index: <https://spamassassin.apache.org/old/publiccorpus/>
- Official corpus README: <https://spamassassin.apache.org/old/publiccorpus/readme.html>

The upstream corpus README cautions against sending the supplied messages into a live mail system and states that original message text rights remain with the original senders. Keep source emails local and exclude them from a public repo. Never present the historical corpus's class prevalence as a modern general-population estimate.
