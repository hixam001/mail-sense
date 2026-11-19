# MailSense project handoff

Last updated: 2026-11-19 (Asia/Karachi).
Completed preparation: **MSE-100 — Delivery workflow** and **MSE-107 — Graphify memory consolidation**.
Next implementation ticket: **MSE-101**.

## Read this at every task start

Read [AGENTS.md](../AGENTS.md), [memory guide](README.md),
[PRODUCT.md](../PRODUCT.md) and this handoff before selecting or resuming work.
Confirm progress against files and Git history. The
[implementation plan](../docs/IMPLEMENTATION_PLAN.md) owns dependencies and ticket
acceptance criteria; this handoff owns the live status of every ticket.
[SRS.md](../docs/SRS.md) remains the locked technical baseline.

## Next task

**MSE-101: Initialize the React/FastAPI monorepo and project structure.**

1. Analyze the complete ticket with Gravitas; record the plan, scoped changes and
   acceptance-to-verification map before editing.
2. Scaffold `frontend/` with React/Vite and `backend/` with Python/FastAPI, plus
   the planned data/artifact structure. Preserve the documentation and tooling.
3. Respect loopback-only operation and the existing sensitive-data ignore rules.
   Do not add accounts, a database, hosted deployment or fake empirical results.
4. Establish actual run/check commands from the scaffold. Verify the React
   hello-world page and FastAPI hello-world endpoint separately; confirm ignore
   rules exclude raw emails and model artifacts.
5. Record evidence and remaining work here, rerun final checks, then commit and
   push using `MSE-101: Initialize React and FastAPI project structure`.

Acceptance: both hello-world applications work separately and the monorepo
structure/ignore rules satisfy MSE-101. Dependency pinning and full setup notes
belong to MSE-102. Scaffold preparation alone does not complete either ticket.

## Established and completed preparation

- The README and ten specification documents are present. They establish the
  product, scope, API/data contracts, workflows, architecture, mathematical
  methods, acceptance tests and all 39 implementation tickets.
- `PRODUCT.md` records the confirmed web platform, users, approved stack, five
  modules, educational purpose, local operation and evidence limitations.
- Project skills are installed under `.agents/skills/`: `gravitas`, `impeccable`
  and `security-audit`. Their presence is tooling setup, not app functionality.
- Impeccable installed its local engine and `.codex/hooks.json`. Product context
  initialization is complete. There is no visual implementation or `DESIGN.md`.
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
  retaining shared memory, installed skills and design context.
- MSE-100 and MSE-107 cover documentation/tooling preparation only. They do not complete
  any MSE-101–606 feature ticket or any product acceptance gate.

## Implemented application functionality

**None yet.** No frontend, backend, dependency manifests, corpus, preprocessing,
statistical services, trained models, API routes or application tests exist at
this handoff. All six implementation release gates remain open. Synthetic
examples in the documentation are not measured corpus/model results.

## Full remaining implementation inventory

All tickets below are **Not started**. Update individual statuses as work is
implemented and verified; retain incomplete and blocked tickets in this table.
Dependencies and detailed acceptance criteria are in
[IMPLEMENTATION_PLAN.md](../docs/IMPLEMENTATION_PLAN.md).

| Ticket | Remaining work | Status |
|---|---|---|
| MSE-101 | Initialize React/FastAPI monorepo and project structure | Not started — next |
| MSE-102 | Pin dependencies and document environment setup | Not started |
| MSE-103 | Obtain canonical official corpus archives and source/checksum manifest | Not started |
| MSE-104 | Implement safe extraction and MIME text parsing | Not started |
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

- Application tests, lint, builds and runtime checks: **not run; no application
  implementation or test suite exists**. No claim of working MailSense software.
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
  `https://github.com/hixam001/mail-sense.git`. MSE-100 was pushed successfully
  through `c910136`; MSE-107 uses `MSE-107: Consolidate project memory with Graphify`.
  Observe the new commit and push result in Git. On resume, check `git log -1`,
  `git status -sb` and the upstream branch before claiming delivery.

## Environment notes and recovery

- The system `node`/`npx` failed during skill installation with missing
  `libsimdjson.so.36`. A checksum-verified official Node v22.23.5 runtime was
  unpacked under `/tmp/mail-sense-impeccable-node/`; its `node-bin-path` file
  identifies the temporary `bin` directory. It enabled Impeccable installation.
  `/tmp` is ephemeral: confirm availability and recheck Node before MSE-101.
  No permanent system Node repair has been performed.
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
