# MailSense

**Version:** 1.0 · **Requirements locked:** November 19, 2026  
**Status:** MSE-101 complete: independent React/Vite and FastAPI scaffolds run locally. Dataset preparation, statistical analysis, classifiers and the analytical interface remain unimplemented. No corpus or trained models are included.

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

## Run the local scaffolds

Use a working Node installation matching `frontend/package.json` (Node 22.13+
within the 22.x line is supported), Python 3.12 and `uv`. Full dependency and
runtime pinning is the next task, MSE-102. Workstation-specific Node recovery
notes are in [the handoff](memory/HANDOFF.md).

In one terminal, from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173/`. The page identifies itself as the React scaffold
and explains that analysis and detection are not implemented yet. Vite binds
to localhost and fails if port 5173 is occupied.

In another terminal, from the repository root:

```bash
uv venv --python 3.12 backend/.venv
uv pip install --python backend/.venv/bin/python -r backend/requirements.txt
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` for the API greeting or
`http://127.0.0.1:8000/openapi.json` for its schema. These scaffolds run
independently. The `/api/v1` contract, readiness checks, corpus ingestion and
model endpoints are scheduled in later tickets.

### Scaffold checks

From `frontend/`:

```bash
npm run lint
npm run build
```

The frontend lockfile is committed; `node_modules/`, build output and Python
virtual environments are ignored. `backend/tests/` is a placeholder, with no
unit test suite yet. The scaffold has been checked through live HTTP requests
and browser rendering; these checks do not establish statistical correctness
or model performance. See [the handoff](memory/HANDOFF.md) for observed evidence.

## Implementation sequence

The requirements and acceptance gates are documented in `docs/`. Delivery follows
this sequence; the handoff records current ticket status:

1. `MSE-101` (complete): Create frontend (`frontend/`) and backend (`backend/`) skeletons.
2. `MSE-102–106` (next): Pin dependencies, then implement corpus ingestion, content deduplication and deterministic split.
3. `MSE-201–207`: Implement and verify statistics independently from ML.
4. `MSE-301–307`: Fit/evaluate both Naive Bayes models.
5. `MSE-401–406`: Implement versioned FastAPI contract.
6. `MSE-501–507`: Build five frontend modules with real API results.
7. `MSE-601–606`: Run tests, collect evidence, finalize university report/demo.

The commands above run the scaffolds only. Later tasks will add and verify
actual corpus preparation, model training and analytical workflows.

## Authoritative change policy

`docs/SRS.md` is the locked technical baseline. Document intentional changes to dataset, stack, models, deployment, or scope as a new approved version and update API/data/flow/test documents together. Examples and scores in docs are **synthetic teaching fixtures unless explicitly labeled actual measured data**.

## Sources and responsible data use

- Official corpus index: <https://spamassassin.apache.org/old/publiccorpus/>
- Official corpus README: <https://spamassassin.apache.org/old/publiccorpus/readme.html>

The upstream corpus README cautions against sending the supplied messages into a live mail system and states that original message text rights remain with the original senders. Keep source emails local and exclude them from a public repo. Never present the historical corpus's class prevalence as a modern general-population estimate.
