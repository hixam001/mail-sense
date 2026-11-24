# Presentation and platform handbook

## Project presentation

- [Editable PowerPoint](learning/MailSense_Project_Presentation.pptx)
- [PDF handout](learning/MailSense_Project_Presentation.pdf)
- [Presenter notes](learning/presenter_notes.md)

The 30-slide widescreen presentation covers the product, architecture, actual
dataset, every module, probability/statistics, both models, measured evaluation,
the paper's paired analysis, demo, testing/privacy, runtime measurements,
limitations, references and API/setup appendices. Five author fields and the
instructor field stay blank, following the research-paper preference.

Speaker notes include explanation, demo guidance, caveats and source locations.
The cost chart, tables and diagrams are editable native PowerPoint objects.
Three source UI captures are embedded unchanged and cropped through presentation
layout; they contain only aggregates and the labeled synthetic example.

All displayed metrics reconcile with the existing evaluation and paper reports.
The deck cites recorded release/paper evidence; preparing it did not rerun the
application's tests or produce new performance measurements. All 30 slides were
rendered and visually reviewed. The verifier checks the PDF text/bounds, notes,
native chart values, references, screenshot bytes and source identities.

## Complete platform guide

- [Complete guide: PDF](learning/MailSense_Complete_Guide.pdf)
- [Editable Word guide](learning/MailSense_Complete_Guide.docx)
- [Searchable guide](learning/MailSense_Complete_Guide.md)

The checked handbook has **58 pages and 55 chapters**, with a blank five-author
cover, two contents pages, clickable chapter navigation and PDF bookmarks.
It covers prerequisites, exact preparation/start/stop commands, every control on
all six screens, worked statistical examples, model explanations, fair evaluation
and the research extension. The technical reference explains the frontend/backend
source map, every API route, artifacts, privacy/offline boundaries, tests,
performance, maintenance, troubleshooting, demo, glossary, exercises and viva.

Appendices retain all 42 delivery tickets, CLI entry points and **296 dependency
entries**: backend lock 35, frontend lock 213, publication environment 17 and graph
environment 31. These are environment-specific entries, including development,
optional and platform packages. They are not 296 distinct runtime libraries.
The complete [CSV](learning/dependency_inventory.csv) and
[JSON](learning/dependency_inventory.json) preserve versions and source paths;
the [OpenAPI snapshot](learning/api_schema.json) supplies complete response schemas.

Six new production screenshots show real readiness/results and only public
aggregates or the authored meeting example. Native Word cropping preserves the
original PNG bytes. The capture used Chromium 158.0.8127.42 at 1366 × 900.
It checks visible results; the handbook dates historical release/paper evidence
separately and does not claim fresh full-suite or performance runs. All 58 final
pages were visually reviewed, with detailed checks of dense tables, commands and
references. The [guide receipt](../artifacts/reports/platform_guide.json) pins
checked outputs and their data sources.

## Rebuild the presentation

Use a separate ignored environment, from the repository root:

```bash
uv venv --python 3.12.15 .tools/learning-venv
uv pip install --python .tools/learning-venv/bin/python -r docs/learning/requirements.txt
.tools/learning-venv/bin/python docs/learning/build_slides.py
libreoffice -env:UserInstallation=file:///tmp/mailsense-deck-lo-608 --headless --convert-to pdf --outdir docs/learning docs/learning/MailSense_Project_Presentation.pptx
.tools/learning-venv/bin/python docs/learning/verify_slides.py --record
```

Omit `--record` to compare against the saved
[verification receipt](../artifacts/reports/presentation.json). The editable
[slide source](learning/slides.json), [builder](learning/build_slides.py) and
[verifier](learning/verify_slides.py) are included. LibreOffice is used only for
local export. App dependencies, models and the frozen v1.0.0 tag are unchanged.

## Rebuild the handbook

Use the same isolated publication environment above. The saved screenshots and
snapshots are inputs; rebuilding documents alone does not start the app.

```bash
.tools/learning-venv/bin/python docs/learning/build_guide.py
libreoffice -env:UserInstallation=file:///tmp/mailsense-guide-lo-609 --headless --convert-to pdf --outdir docs/learning docs/learning/MailSense_Complete_Guide.docx
.tools/learning-venv/bin/python docs/learning/verify_guide.py --record
.tools/learning-venv/bin/python docs/learning/verify_guide.py
```

The [structured source](learning/guide.json), [builder](learning/build_guide.py),
[page map](learning/guide_navigation.json) and [verifier](learning/verify_guide.py)
are included. The validator independently compares all native text with the PDF,
contents/bookmark targets and page bounds; reconciles metrics, counts, bootstrap
intervals and timings; compares inventories with actual locks/environments and the
schema with the backend; and checks references, screenshot bytes and receipt hashes.
Prepare the backend and graph environments before running that full reconciliation.
Omit `--record` to verify an existing receipt. After editing, correct any overflow
and update the page map to the observed export before recording new evidence.
Other Word/font installations can repaginate; the supplied PDF is the checked copy.

Optional screenshot refresh, after data/models and the production build are ready:

```bash
python3 docs/learning/capture_screens.py
```

Install the pinned Playwright test browser as described in [setup](SETUP.md), or
pass `--browser /absolute/path/to/trusted-chromium`. The runner owns/cleans only
servers it starts and refuses a development server when production is expected.
Rebuild and verify the guide after replacing screenshots. Review changed
dependency/API snapshots and related handbook text intentionally; do not edit
receipt hashes to conceal drift.
