# MailSense v1.0.0

Frozen local academic application · 19 November 2026

All **39 implementation tickets** and **Gates 1–6** are complete. Frontend,
backend and API versions agree at **1.0.0**. The release is identified by Git tag
`v1.0.0`; inspect its commit and remote ref in Git for delivery confirmation.
There are no remaining v1 implementation tickets or known blocker/high-severity
defects within the executed scope. Future work requires a new assigned ticket.

## Release checklist and acceptance mapping

| Gate | Checked outcome | Evidence |
|---|---|---|
| 1 | Five canonical archives; safe parsing; exclusions and disjoint seed42 split reproduce | [Source manifest](../data/processed/source_manifest.json), [reproducibility](REPRODUCIBILITY.md) |
| 2 | Descriptive, Bayes, distribution, Pearson and Wilson calculations reconcile independently | [Numerical report](../artifacts/reports/statistics_verification.json), [hand calculations](REPRODUCIBILITY.md) |
| 3 | Both saved models match fixed training-only refits and identical held-out evaluation | [Model card](MODEL_CARD.md), [independent report](../artifacts/reports/reproducibility.json) |
| 4 | Twelve API routes, safe validation/readiness/errors and local boundaries verified | [API contract](API_CONTRACT.md), [T01–T08](../artifacts/reports/acceptance.json) |
| 5 | All five modules and overview work at desktop/mobile sizes, including keyboard and recovery | [UI checks](UI_VERIFICATION.md), [release aggregate](../artifacts/reports/release.json) |
| 6 | Academic report, inspected figures, fresh install, demo, final checks and version freeze complete | [University report](UNIVERSITY_REPORT.md), [fresh install](../artifacts/reports/fresh_install.json), [demo](DEMO.md) |

- [x] AC-01: Source-only installation and full readiness verified separately.
- [x] AC-02: Actual counts follow pinned sources, MIME exclusions and duplicates.
- [x] AC-03: Descriptive, empirical/Bayes and distribution hand examples agree.
- [x] AC-04: Pearson and Wilson match independent reference arithmetic.
- [x] AC-05: Shared training-only vocabulary and identical test membership.
- [x] AC-06: Both transient predictions and full log-odds decompositions work.
- [x] AC-07: Every confusion-derived metric reconciles.
- [x] AC-08: Loading, empty, invalid, missing-model and actual backend recovery pass.
- [x] AC-09: All workflows pass with no external OS network routes.
- [x] AC-10: Report explains methods, measured results, disagreement and limitations.
- [x] Final **413 Python tests**, **8 frontend tests**, Ruff, ESLint, frozen-lock
  checks, dependency compatibility, production build and browser checks pass.
- [x] Advisory lookup: zero reported npm/Python advisories and zero skipped packages
  at the recorded timestamp; this is not proof against unknown vulnerabilities.
- [x] Handoff lists every ticket complete; graph has no invented next-task edge
  and rejects premature completion while any task remains unfinished.

The [release aggregate](../artifacts/reports/release.json) pins the relevant
reports and version files. Evidence reports retain their originating ticket IDs;
their actual timestamps distinguish reruns. Git records the final source commit
without a self-referential hash in that JSON.

## Known limitations

- The corpus is historical and curated. Class proportions and Wilson intervals
  do not establish current population prevalence. Strict parsing excludes some
  partly readable MIME; exact deduplication leaves near duplicates and threads.
- A single fixed holdout does not establish uncertainty across splits, temporal
  generalization, language parity or adversarial robustness. No tuning used this
  holdout. Spam probabilities are uncalibrated and can be overconfident.
- Pearson tests assume independent observations; exploratory word selection has
  no multiple-testing correction. Association is not causation and is different
  from Naive Bayes' conditional feature-independence assumption.
- This tool has no live mailbox, accounts, sending, quarantine, arbitrary uploads,
  external inference or hosted deployment. Phishing, attachments and malware are
  not evaluated. Only trusted local project-created joblib files are supported;
  checksums are not authenticity signatures.
- Linux x86_64 and Chromium 143/151 are observed. macOS/arm64 installer selections
  are untested; native Windows is unsupported by the Node wrapper. Safari,
  Firefox, physical touch devices and assistive-technology sessions are unmeasured.
  Contrast/keyboard checks are focused verification, not a formal accessibility audit.
- Timings use warmed sequential requests and a 100-character synthetic input.
  Cold startup, maximum-input latency, concurrent load and other machines are not
  benchmarked; RAM was not measured. Maximum input validation is tested separately.
- Initial downloads need network access. The Linux OS-level offline checker
  requires user/network namespace support and iproute2; normal offline app use
  needs neither. Graphify's optional HTML viewer uses a CDN, separate from the
  fully local MailSense UI and local memory generation/CLI retrieval.
- New acquisition/training times legitimately change provenance identities even
  when scientific outputs reproduce. The fresh rehearsal used separate checkout
  environments/data with permitted external caches, rather than an empty machine.

## Recorded implementation choices

The approved data, stack, two classifiers, α=1, seed42 and local-only scope remain
unchanged. The test-plan proposal used Vitest/React Testing Library; implemented
frontend helper tests use Node's built-in runner plus Playwright production flows.
CDN-dependent Swagger/Redoc pages are disabled; local OpenAPI JSON remains
available. Architecture documentation names the actual modules. Academic delivery
is Markdown with five original production screenshots and shareable numerical
reports; no institution, student identity or examiner approval is fabricated.

The earlier offline check covered browser/API denial boundaries. Final release
adds an isolated OS network namespace, so OS-level offline behavior is now
verified with [kernel-level evidence](../artifacts/reports/offline_namespace.json).
No unmet required v1 feature is deferred as a future enhancement.

## Reproduce release checks

Install and prepare using [SETUP](SETUP.md), install the optional test browser,
then run from the repository root with existing app servers stopped:

```bash
python3 scripts/release_check.py
uv run --directory backend --frozen python -m scripts.verify_science verify
python3 scripts/browser_check.py --production
python3 scripts/offline_check.py
python3 scripts/dependency_check.py
```

The first four run locally after preparation; advisory lookup requires internet.
The separate namespace runner owns its child network and leaves the parent
network unchanged. Source emails, private text, models, generated environments,
test output and agent tooling remain ignored and absent from the release commit.
