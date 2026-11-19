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
uv run --project backend --frozen ruff check --config backend/pyproject.toml backend/app backend/tests scripts
uv run --project backend --frozen pytest -c backend/pyproject.toml backend/tests scripts/tests
```

The nine current tests check the pinned Python runtime, native-library numerical
compatibility, both Naive Bayes classes and trusted synthetic artifact roundtrips,
FastAPI test-client compatibility, and the Node installer's checksum/path/error
boundaries. They use synthetic data and temporary files, not the SpamAssassin
corpus. They do not complete the statistical algorithms, classifiers or release
acceptance scenarios in the project backlog.

The installed application stack includes NumPy, Pandas, SciPy, scikit-learn and
joblib, plus Recharts and a React-matched `react-is`. Matplotlib remains optional
for later static report work and is not installed by this baseline.

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

Initial runtime/package downloads need network access. After setup, the two
local scaffolds and current tests run without external inference or corpus
access. Full offline analytical use additionally requires the corpus and model
artifacts from later tasks. No dataset, trained model, empirical score or
statistical workflow is provided by environment setup.

If a runtime download fails verification, the helper exits before extracting
or executing it. If a cached Node installation is damaged, remove that release's
folder under `.tools/` and rerun install. Do not change system libraries to make
the distro Node work for this project. For port conflicts, stop the conflicting
local process; keep the documented loopback bindings and ports.

Commit source, pins, locks and shared memory. Keep `.tools/`, virtual
environments, dependency directories, builds, raw mail, model files and all
local agent/tooling directories ignored as specified in `.gitignore`.
