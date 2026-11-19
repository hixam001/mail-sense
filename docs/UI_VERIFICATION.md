# Interface verification — Gate 5

MSE-507 verified the production preview with Chromium 151.0.7922.34 on Linux
x86_64. All six routes passed at 1366×900 and 390×844; these are emulated
viewports. Public aggregate and labeled synthetic-input screenshots were
inspected. The maintained [result](../artifacts/reports/ui_verification.json)
records browser, timestamp, dataset/split identities and computed contrast.

The committed [browser suite](../frontend/tests/browser.mjs) checks direct
navigation, scoped real totals, evaluation parity, fixed source labels, mobile
active navigation and resize, keyboard skip/form/submit/focus, delayed word and
prediction requests, duplicate submission, transient text, empty responses,
network failure/retry and unknown routes. All observed requests stayed on
loopback. It found no page exceptions. Computed visible text contrast covered
1,490 samples across the twelve route/viewport combinations; the lowest sampled
ratio was 5.31:1. This is a focused UI check, not a full accessibility audit.

Eight frontend unit tests and 397 backend/bootstrap tests pass. ESLint, Ruff
and the production build pass. The production UI uses the same explicitly
allowed port 5173 as development. Initial JavaScript is about 233 kB uncompressed;
the Dataset/Recharts chunk loads separately at about 421 kB. No remote assets
or fonts are loaded by the application.

## Reproduce

Install the pinned application dependencies and prepare the corpus/models first,
as described in [SETUP.md](SETUP.md). Install the browser once if needed:

```bash
python3 scripts/node.py node frontend/node_modules/playwright-core/cli.js install chromium
python3 scripts/browser_check.py --production
```

Alternatively pass `--browser /absolute/path/to/trusted/chromium` to use an
existing executable. The observed run used that option with Chromium 151.
The runner builds the UI, starts missing loopback servers, runs the checks and
stops only servers it started. Stop a development UI before a production check;
both deliberately use port 5173. Omit `--production` to check Vite development.
Screenshots and detailed run output go to ignored `frontend/test-results/ui/`.

Firefox, Safari, physical touch devices and assistive-technology sessions have
not been exercised. English UI, local operation and the approved canonical
corpus remain the supported scope. Release-critical scenarios and performance
are tracked separately in [TEST_PLAN.md](TEST_PLAN.md).
