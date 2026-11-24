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
rendered and visually reviewed. The original publication check covered PDF text/bounds, notes,
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

## Editing and historical production tools

Edit the supplied PPTX in PowerPoint or LibreOffice Impress, and the DOCX in
Word or LibreOffice Writer. Export a new PDF after changing the editable file;
fonts or layout changes can alter pagination. The supplied PDFs are the checked
exports from the original deliveries.

MSE-610 removed the one-off document builders, screenshot capture wrappers,
publication verifiers and their two dependency manifests. They are not needed to
run MailSense or use these documents. The application preparation, research
analysis, browser/release checks and Graphify tools remain available through
[setup](SETUP.md), [paper reproduction](PAPER.md) and the [memory guide](../memory/README.md).

The original tooling remains available in the
[pre-cleanup Git revision](https://github.com/hixam001/mail-sense/tree/941aec0ebe4426264edc21bc09d10dd598285806/docs).
Structured [slides](learning/slides.json), [guide content](learning/guide.json),
[page map](learning/guide_navigation.json), figures, screenshots and dependency/API
snapshots are retained as records of how the delivered documents were prepared.
They describe the original 42-ticket delivery. The searchable Markdown guide has
an explicit cleanup note; its PDF/DOCX remain the original 58-page export.

The [presentation receipt](../artifacts/reports/presentation.json) and
[guide receipt](../artifacts/reports/platform_guide.json) record original validation
at that revision. Their hashes are historical, including inputs removed by
MSE-610 and the original Markdown guide. They have not been rewritten to imply a
new document validation. Retrieve the pinned Git revision to inspect those exact
inputs. Document-production dependency entries are historical supporting tools,
not prerequisites for the application.
