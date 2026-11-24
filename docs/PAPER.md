# Conference paper: MailSense

The post-release MSE-607 deliverable is an **eight-page paper**: one title page
and seven pages of two-column content, including references.

- [PDF for submission](paper/MailSense_Research_Paper.pdf)
- [Editable DOCX](paper/MailSense_Research_Paper.docx)

The cover reserves **five blank author entries** and a **blank instructor**.
Affiliations and a submission-date field are omitted as requested. Fill the
editable copy before producing a personalized submission PDF.

## Research contribution

This paper extends the frozen v1.0 application with secondary statistical
analysis. It keeps both models, thresholds, vocabulary and test membership fixed.
It does not claim a new independent holdout or a new training algorithm.

- Paired correctness: 1,092 both correct, 59 Multinomial-only, four Bernoulli-only
  and 18 both wrong. Exact McNemar p = 1.3821257506541063e−13.
- Ten thousand class-stratified paired bootstrap samples, seed 20261122:
  accuracy difference 4.69 percentage points, 95% interval [3.50, 5.97];
  recall difference 15.95 points, interval [12.25, 19.94]; FPR difference
  0.12 points, interval [−0.36, 0.73]. All differences are Multinomial−Bernoulli.
- Wilson intervals with explicit denominators; word `free` association
  OR = 5.2559, interval [4.6214, 5.9775], and phi = .34649.
- A conditional error-cost sensitivity calculation, with an observed break-even
  false-positive cost of 56 missed-spam units. It is not an operating-policy
  recommendation or an estimate of user costs.

All intervals/tests use stated working assumptions about message independence.
Historical selection, near duplicates, threads and the inspected holdout limit
generalization. The paper explains why a small p-value, high accuracy or extreme
model probability cannot establish modern email-security performance.

## Source and reproduction

After the normal [application setup](SETUP.md), with local corpus/models ready:

```bash
uv run --directory backend --frozen python -m scripts.analyze_paper run
uv run --directory backend --frozen python -m scripts.analyze_paper verify
```

The [aggregate analysis](../artifacts/reports/paper_statistics.json) contains
paired cells, bootstrap protocol, rate intervals, word effects, cost sensitivity
and exact input identities. The script verifies frozen evaluation counts and
leaves private data/model bytes unchanged. Original email text and per-message
predictions are not published.

The editable DOCX can be updated in Word or LibreOffice Writer and exported to
PDF. Other Word/font installations may paginate differently; the supplied PDF
is the checked eight-page submission artifact.

MSE-610 removed the one-off paper builder, document verifier and isolated
publication dependency manifest. The statistical analysis commands above remain
supported. The original document tooling is archived in the
[pre-cleanup revision](https://github.com/hixam001/mail-sense/tree/941aec0ebe4426264edc21bc09d10dd598285806/docs/paper).

[Manuscript source](paper/manuscript.json), [references](paper/references.json)
and standalone PNG/SVG figures under `docs/paper/figures/` accompany the editable
files. Plots were generated from the actual analysis, not decorative or generative
images. The [document receipt](../artifacts/reports/paper_document.json) retains
its original delivery hashes, including the archived tooling; it is historical
evidence rather than a new check of the cleaned repository.

## Observed checks

Five substantive editing passes covered structure/new contribution, statistical
precision, natural phrasing, citations and final copy/layout. All eight rendered
pages were visually inspected. The title and both figures were corrected for
line-height clipping; final bounds, column layout and figure sizes pass the
document verifier. Ten references, five tables, two scientific figures, blank
identity fields and numerical consistency are checked in the
[document receipt](../artifacts/reports/paper_document.json).

The complete backend/bootstrap/memory suite passes **418 tests**, including five
new known-answer analysis tests; Ruff passes. The frontend and application
runtime were unchanged, so frontend/browser reruns were not applicable to this
paper task. The v1.0.0 release evidence retains its original 413-test snapshot.

The manuscript is original prose with cited sources and no unmarked copied
passages. An institutional similarity score has **not** been measured; the
assignment's 15% threshold must be checked using the institution's service.
Editing does not establish a plagiarism percentage or detector outcome.
