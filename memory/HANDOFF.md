# MailSense project handoff

Last updated: 2026-11-19 (Asia/Karachi).
Completed preparation: **MSE-100 — Delivery workflow** and **MSE-107 — Graphify memory consolidation**.
Completed maintenance: **MSE-108 — Ignore local agent tooling and generated/private files**.
Latest implementation: **MSE-103 — Canonical official corpus acquisition and provenance verified**.
Next implementation ticket: **MSE-104**.

## Read this at every task start

Read [AGENTS.md](../AGENTS.md), [memory guide](README.md),
[PRODUCT.md](../PRODUCT.md) and this handoff before selecting or resuming work.
Confirm progress against files and Git history. The
[implementation plan](../docs/IMPLEMENTATION_PLAN.md) owns dependencies and ticket
acceptance criteria; this handoff owns the live status of every ticket.
[SRS.md](../docs/SRS.md) remains the locked technical baseline.

## Next task

**MSE-104: Implement safe archive extraction and MIME text parsing.**

1. Analyze the complete ticket with Gravitas; read FR-02/03, the data schema,
   planned ingestion flow and parser/security fixtures. Verify the local source
   manifest before using archives; setup/acquisition commands are in `docs/SETUP.md`.
2. Implement bounded archive handling that rejects absolute/traversal paths,
   symlinks/unsafe members and escapes before writing. Keep raw/extracted email
   content local and ignored; never execute attachments or message content.
3. Decode MIME subject/body, prefer one plain-text alternative, and safely derive
   text from HTML when needed without rendering scripts or fetching resources.
   Only subject/body text is a model feature; source labels come from group metadata.
4. Record parse/exclusion counts and errors without logging message bodies.
   Populate SourceArchive integer counters and `processing_status: "complete"`
   only after parsing; preserve recorded archive provenance. Deduplication and
   final retained counts belong to MSE-105; split assignment belongs to MSE-106.
5. Test valid/malformed encodings, multipart alternatives, HTML, attachments,
   unsafe archive paths and failure recovery. Update handoff/graph, verify,
   then commit and push with MSE-104.

Acceptance: plain-text/HTML/subject decoding works, attachments are ignored,
unsafe extraction is prevented, and parse failures/exclusions are counted.
No archives have been extracted or email messages parsed by MSE-103.

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
  local archives total **6,962,803 bytes**. All parsing counters are `null` with
  `processing_status: "not_started"`; Data Model v1.1 documents that lifecycle.
  Archive bytes remain ignored under `data/raw/`. No extraction has run.
- Safe parsing/ingestion, domain statistical/model services, five UI modules and their
  unit/contract suites remain unimplemented. All six release gates remain open.
  Synthetic environment checks are not measured corpus/model results.

## Full remaining implementation inventory

MSE-101–103 are complete; the other **36 tickets are Not started**. Update statuses as work is
implemented and verified; retain incomplete and blocked tickets in this table.
Dependencies and detailed acceptance criteria are in
[IMPLEMENTATION_PLAN.md](../docs/IMPLEMENTATION_PLAN.md).

| Ticket | Remaining work | Status |
|---|---|---|
| MSE-101 | Initialize React/FastAPI monorepo and project structure | Complete — runtime/build/lint verified |
| MSE-102 | Pin dependencies and document environment setup | Complete — fresh install/locks/tests verified |
| MSE-103 | Obtain canonical official corpus archives and source/checksum manifest | Complete — real downloads/hashes/offline verification |
| MSE-104 | Implement safe extraction and MIME text parsing | Not started — next |
| MSE-105 | Deduplicate, reject label conflicts and derive summary records | Not started |
| MSE-106 | Verify deterministic stratified 80/20 split, seed 42 | Not started |
| MSE-201 | Implement descriptive statistics for text length and token count | Not started |
| MSE-202 | Aggregate histograms, box plots and top-word data | Not started |
| MSE-203 | Implement 2×2 word contingency and empirical probabilities | Not started |
| MSE-204 | Implement Bernoulli/binomial calculations with assumptions | Not started |
| MSE-205 | Implement Pearson chi-square and assumption checks | Not started |
| MSE-206 | Implement Wilson proportion confidence intervals | Not started |
| MSE-207 | Verify formula unit tests and record numerical evidence | Not started |
| MSE-301 | Fit a shared training-only CountVectorizer vocabulary | Not started |
| MSE-302 | Train Multinomial Naive Bayes with alpha=1.0 | Not started |
| MSE-303 | Train Bernoulli Naive Bayes with alpha=1.0 | Not started |
| MSE-304 | Persist trusted artifacts, matching metadata and checksums | Not started |
| MSE-305 | Evaluate both models on the same untouched holdout | Not started |
| MSE-306 | Implement faithful token/prior and absent-feature explanations | Not started |
| MSE-307 | Save evaluation evidence and document model limitations | Not started |
| MSE-401 | Implement FastAPI health/readiness and shared error envelope | Not started |
| MSE-402 | Implement dataset summary/statistics/distribution routes | Not started |
| MSE-403 | Implement probability and statistical inference routes | Not started |
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
  Byte hashes establish this acquisition's reproducible inputs. Parsing and
  cleaned/retained message counts are explicitly pending, with no release gate
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
  MSE-102 commit `6079922`. MSE-103 uses
  `MSE-103: Acquire canonical corpus archives and pin provenance`.
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
