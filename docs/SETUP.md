# Local development setup

## Supported baseline

The setup recipe is verified on Linux x86_64. The local Node installer also
selects official Linux arm64 and macOS x64/arm64 archives; those platforms have
not been exercised here. Native Windows is not supported by this wrapper.

Prerequisites: Git, a Python 3.12+ interpreter to run the Node installer, network
access for initial downloads, and **uv 0.13.9**. Install that uv version using
the [official installation instructions](https://docs.astral.sh/uv/getting-started/installation/).
The backend configuration rejects a different uv version.

| Tool | Exact version | Authority |
|---|---|---|
| Node | 22.23.5 | Root `.node-version` and frontend engines |
| npm | 10.9.9 | `frontend/package.json` packageManager and engines |
| Python | 3.12.15 | Root `.python-version` and backend requires-python |
| uv | 0.13.9 | `backend/pyproject.toml` required-version |

All commands below run from the repository root. They do not require activation
of a virtual environment or a working system Node. Graphify's separate
`memory/.venv/` is not an application dependency environment.

## Install

```bash
uv --version
python3 scripts/node.py install
python3 scripts/node.py node --version
python3 scripts/node.py npm --version
python3 scripts/node.py npm --prefix frontend ci
uv sync --project backend --frozen
```

The Node helper downloads an official release into ignored `.tools/`, verifies
its SHA-256 against a committed checksum before extraction, checks the bundled
Node/npm versions, and scopes PATH to that installation when launching commands.
It reuses an existing matching installation; it does not modify system packages
or depend on an earlier `/tmp` download. Review checksums against the
[official release manifest](https://nodejs.org/dist/v22.23.5/SHASUMS256.txt) when
changing versions.

`npm ci` enforces `frontend/package-lock.json`; direct dependencies are exact
pins and `.npmrc` enforces the runtime engines. `uv sync --frozen` installs the
existing `backend/uv.lock` into ignored `backend/.venv/`, including development
checks, without resolving new versions. uv can download the exact Python if it
is not installed. Use `uv sync --project backend --frozen --no-dev` only when
development checks are not needed; the normal sync restores them.

## Run

In one terminal:

```bash
python3 scripts/node.py npm --prefix frontend run dev
```

Open `http://localhost:5173/`. The page is the independent React scaffold.
Vite stays on loopback and fails if that port is occupied.

In a second terminal:

```bash
uv run --project backend --frozen python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

The greeting is at `http://127.0.0.1:8000/`; its schema is at
`http://127.0.0.1:8000/openapi.json`. These are scaffold endpoints. Corpus
readiness, `/api/v1` analytics and prediction endpoints are not implemented yet.
Stop each server with Ctrl+C.

## Verify

```bash
python3 scripts/node.py npm --prefix frontend run lint
python3 scripts/node.py npm --prefix frontend run build
uv lock --project backend --check
uv pip check --python backend/.venv/bin/python
uv run --project backend --frozen ruff check --config backend/pyproject.toml backend/app backend/tests backend/scripts scripts
uv run --project backend --frozen pytest -c backend/pyproject.toml backend/tests scripts/tests
```

The environment/bootstrap tests check the pinned Python runtime, native-library numerical
compatibility, both Naive Bayes classes and trusted synthetic artifact roundtrips,
FastAPI test-client compatibility, and the Node installer's checksum/path/error
boundaries. They use synthetic data and temporary files, not the SpamAssassin
corpus. They do not complete the statistical algorithms, classifiers or release
acceptance scenarios in the project backlog. Corpus-acquisition regression tests
also cover manifest integrity, cache reuse, missing/corrupted archives, transport
limits and failure cleanup using synthetic byte streams.

The installed application stack includes NumPy, Pandas, SciPy, scikit-learn and
joblib, plus Recharts and a React-matched `react-is`. Matplotlib remains optional
for later static report work and is not installed by this baseline.

## Acquire the corpus

After installing the backend environment, from the repository root:

```bash
uv run --directory backend --frozen python -m scripts.download_corpus download
uv run --directory backend --frozen python -m scripts.download_corpus verify
```

`--directory backend` runs this preparation command in the backend project.
The downloader uses only the fixed official Apache HTTPS URLs, refuses redirects,
limits each archive to 32 MiB and stages downloads under ignored `data/raw/`.
It publishes `data/processed/source_manifest.json` with actual byte sizes,
SHA-256 values and UTC acquisition timestamps. No emails are extracted or parsed.

The selected archives, confirmed against the
[official index](https://spamassassin.apache.org/old/publiccorpus/) and
[corpus README](https://spamassassin.apache.org/old/publiccorpus/readme.html), are:

| Group | Archive | Label |
|---|---|---|
| easy_ham | `20030228_easy_ham.tar.bz2` | ham |
| easy_ham_2 | `20030228_easy_ham_2.tar.bz2` | ham |
| hard_ham | `20030228_hard_ham.tar.bz2` | ham |
| spam | `20030228_spam.tar.bz2` | spam |
| spam_2 | `20050311_spam_2.tar.bz2` | spam |

The March 2005 spam_2 revision corrects a misclassified message. Older snapshots
are not additional independent groups. Checksums are computed from downloaded
bytes and pin subsequent verification/refetches to that acquisition.

`verify` is offline. A complete matching cache makes `download` a network-free
no-op that preserves the manifest. Missing files are downloaded and must match
the existing pinned checksum/size; their acquisition timestamps are refreshed.
Review resulting timestamp changes before committing metadata from a new machine.
Corrupted local files, unmanifested existing archives and changed upstream bytes
fail without silently replacing provenance. Move a damaged/unmanifested local
archive aside before retrying; investigate an upstream checksum change explicitly.
If an interrupted process leaves `data/raw/.acquisition.lock`, confirm no other
acquisition process is active before removing that stale local lock.

The acquisition stage records `processing_status: "not_started"` and `null`
parsing counters. MSE-104 owns safe extraction and MIME parsing; MSE-105 owns
deduplication/retained counts. The measured acquisition total is **6,962,803
compressed bytes** across five archives, with no claim of a cleaned email count.
Commit the manifest and code; raw archives and temporary download files stay
ignored. Preserve the corpus README's restrictions on live-mail use and original
message rights; do not send corpus messages through a live mail system.

## Locks and intentional updates

Frontend direct pins live in `frontend/package.json`; transitive versions and
integrity hashes live in `frontend/package-lock.json`. After an intentional pin
change, regenerate with:

```bash
python3 scripts/node.py npm --prefix frontend install
```

Backend direct pins and the dev group live in `backend/pyproject.toml`;
`backend/uv.lock` is the transitive lock. `backend/requirements.txt` is a
generated, hashed, runtime-only export for pip-compatible consumers. Do not edit
that export by hand. After an intentional dependency change:

```bash
uv lock --project backend
uv sync --project backend --frozen
uv export --project backend --frozen --no-dev --format requirements.txt --output-file backend/requirements.txt
```

For an isolated runtime-only environment, that export can be installed with
`uv pip sync --require-hashes --python <environment-python> backend/requirements.txt`.
The target environment must use Python 3.12.15. Regular development uses frozen
uv sync so its dev tools are installed too.

Changing Node requires updating `.node-version`, the frontend engines,
packageManager if npm changes, and the official archive checksums in
`scripts/node.py`. Changing Python requires updating `.python-version` and
backend requires-python together. Rerun all affected setup/runtime checks and
commit the pins and locks together. Routine installs must not change lockfiles.

## Offline use and recovery

Initial runtime/package/corpus downloads need network access. The two local
scaffolds, current tests and corpus verification run offline after preparation.
Full analytical use still requires parsed data and model artifacts from later
tasks. Acquisition/environment setup supplies no cleaned dataset, trained model,
empirical score or statistical workflow.

If a runtime download fails verification, the helper exits before extracting
or executing it. If a cached Node installation is damaged, remove that release's
folder under `.tools/` and rerun install. Do not change system libraries to make
the distro Node work for this project. For port conflicts, stop the conflicting
local process; keep the documented loopback bindings and ports.

Commit source, pins, locks and shared memory. Keep `.tools/`, virtual
environments, dependency directories, builds, raw mail, model files and all
local agent/tooling directories ignored as specified in `.gitignore`.
