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

MSE-609 follows immediately: a full tutorial and project reference handbook in
editable DOCX, PDF and searchable source. The handoff records its progress.

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
