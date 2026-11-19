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
MIME/ingestion tests use real synthetic tar/bzip2 archives to cover safe paths,
member types, decoding, attachment exclusion, resource limits, repeatability,
artifact verification, redacted diagnostics and publication rollback.

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
preparation process is active before removing that stale local lock. Acquisition
and parsing share this lock.

The acquisition stage records `processing_status: "not_started"` and `null`
parsing counters before ingestion. MSE-104 implements safe extraction and MIME parsing; MSE-105 owns
deduplication/retained counts. The measured acquisition total is **6,962,803
compressed bytes** across five archives, with no claim of a cleaned email count.
Commit the manifest and code; raw archives and temporary download files stay
ignored. Preserve the corpus README's restrictions on live-mail use and original
message rights; do not send corpus messages through a live mail system.

## Parse the corpus

After acquisition, from the repository root:

```bash
uv run --directory backend --frozen python -m scripts.ingest_corpus run
uv run --directory backend --frozen python -m scripts.ingest_corpus verify
```

Both commands run offline. Ingestion verifies pinned archives before and after
reading them. It streams decompressed tar members, rejects unsafe paths,
duplicates, links, sparse/special files and wrong corpus groups, and writes
candidate bytes only under generated names in a private `data/raw/.ingest-*`
staging directory. It never applies archive permissions/owners, executes the
`cmds` control files or renders/fetches MIME resources. The root `cmds` in each
group is ignored and reported separately from candidate mail.

The parser decodes subject/body only, prefers plain text over its HTML
alternative, strips HTML safely and ignores attachments. The detailed
[normalization and diagnostics contract](DATA_MODEL.md#implemented-parsing-contract-mime-v1)
defines `mime-v1`; this stage does not tokenize, deduplicate or assign a split.

| Bound | Default |
|---|---|
| Expanded bytes per archive, including padding/trailer | 128 MiB |
| Members per archive | 20,000 |
| Raw bytes per message | 2 MiB |
| Headers per MIME part | 64 KiB at top level; 65,536 decoded header characters per part |
| MIME parts / maximum nesting depth (root = 0) | 128 / 20 |
| Decoded leaf text and final normalized model text | 1,000,000 characters each |
| Private JSONL output | 512 MiB |

An unsafe archive or archive/output limit aborts publication. Malformed MIME,
empty text or exceeded message limits reject that candidate with a reason code.
The strict MIME structural policy may discard partially readable historical
messages. Accepted messages with decoding fallbacks/nonfatal defects carry
warning codes; no raw message text or member name appears in command output.

Current measured results before deduplication:

| Group | Candidates | Accepted | Rejected |
|---|---:|---:|---:|
| easy_ham | 2,500 | 2,500 | 0 |
| easy_ham_2 | 1,400 | 1,400 | 0 |
| hard_ham | 250 | 249 | 1 |
| spam | 500 | 473 | 27 |
| spam_2 | 1,396 | 1,370 | 26 |
| Total | 6,046 | 5,992 | 54 |

All 54 rejections have `malformed_mime` reason codes. Five directories and
five control files are excluded from candidates. Outputs are private ignored
`data/processed/messages.parsed.jsonl`, shareable `parsing_report.json` (hashes,
versions, limits, counters and hashed rejection IDs) and updated integer parsing
counters in `source_manifest.json`. No final retained/class prevalence is claimed.
Two real runs produced byte-identical outputs; archive hashes and acquisition
timestamps remained unchanged. Keep Python 3.12.15 and `mime-v1` to reproduce them.

New outputs are staged and previous outputs backed up during publication.
Ordinary exceptions restore the previous set; verification detects inconsistent
files after abrupt termination. On interruption, confirm no preparation process
is running, remove only the stale `.acquisition.lock`/`.ingest-*` state, and
rerun ingestion from the verified archives. Do not edit counts/hashes to make
verification pass. A clone has the public report but no private text: acquire
the pinned archives and run ingestion before parsed verification can succeed.

## Prepare retained records

After parsing, from the repository root:

```bash
uv run --directory backend --frozen python -m scripts.prepare_dataset run
uv run --directory backend --frozen python -m scripts.prepare_dataset verify
```

Both commands run offline. `corpus_dataset.py` verifies the parsed corpus,
checks text equality within each content-hash group, excludes whole groups
with conflicting labels, and retains the smallest stable message ID from each
same-label group. Retained rows sort by ID. Token counts use the fixed
`unicode-word-v1` rule: lowercase Unicode word runs of at least two characters,
including digits/underscores; no stop words, accent stripping or fitted state.
Case/punctuation remain significant for exact-content deduplication. See the
[retained data contract](DATA_MODEL.md#implemented-retained-dataset-exact-text-v1)
and [canonical tokenizer](STATISTICAL_METHODS.md#canonical-tokenization-unicode-word-v1).

Observed counts for the pinned corpus:

| Group | Parsed input | Retained | Duplicate exclusions | Conflict exclusions |
|---|---:|---:|---:|---:|
| easy_ham | 2,500 | 2,471 | 29 | 0 |
| easy_ham_2 | 1,400 | 1,389 | 11 | 0 |
| hard_ham | 249 | 247 | 2 | 0 |
| spam | 473 | 454 | 19 | 0 |
| spam_2 | 1,370 | 1,301 | 69 | 0 |
| Total | 5,992 | 5,862 | 130 | 0 |

The 5,862 retained records comprise **4,107 ham and 1,755 spam**. There are
96 duplicate groups and no observed conflicting-label groups. Tests cover
conflicts separately. Input = retained + duplicate exclusions + conflict
exclusions; conflict rows are not also counted as duplicates. The earlier
54 parse rejections remain separate. These counts describe this historical
dataset and exact-text policy, not modern email prevalence or model accuracy.

Private `data/processed/messages.csv` is ignored and owner-only. It preserves
the representative's provenance, text, content hash, character count and parse
warnings and adds `token_count`; it has no `split` column yet. Standard CSV
quoting preserves embedded model-text newlines; warning cells contain JSON
arrays. A CSV reader needs a field limit of 1,000,000 characters for this schema.
The CSV output limit is 512 MiB. Empty parsed input yields a header-only CSV
and zero counts; nonblank text with no tokens is retained with token count zero.

The shareable `deduplication_report.json` pins parser/runtime/tokenizer/dedup
versions, source-manifest/parsing-report/private-input hashes and sizes, output
hash/size, dataset ID, per-class/source counts and every excluded hash ID with
reason/representative mapping. No message text, member names or addresses enter
the report or CLI output. The dataset ID depends on canonical retained CSV and
configuration; input serialization is pinned separately. Raw archives,
acquisition metadata, parser outputs and SourceArchive counters are unchanged.

Publication stages both outputs in private `data/raw/.dataset-*`, shares the
preparation lock and restores the previous set on ordinary exceptions.
Verification rederives the full retained dataset/report from verified inputs,
so changing the CSV and its reported checksum together still fails. If inputs
change, rerun downstream preparation in order. After abrupt termination, check
no preparation process is active, remove stale lock/staging state, rerun from
verified parsed inputs and verify again. Do not manually repair hashes/counts.
A clone must acquire, parse and prepare locally to recreate private files.
MSE-106 will assign the stratified 80/20 split; no vocabulary or model is fitted
by any current corpus preparation command.

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
scaffolds, current tests and corpus parsing/verification run offline after preparation.
Full analytical use still requires split metadata and model artifacts from later
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
