"""Check presentation editability, source data, speaker notes and rendered layout."""

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from zipfile import ZipFile

import pymupdf
from pptx import Presentation

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text).replace("−", "-")).lower()


def check():
    source = json.loads((HERE / "slides.json").read_text())
    deck = HERE / "MailSense_Project_Presentation.pptx"
    pdf = HERE / "MailSense_Project_Presentation.pdf"
    prs = Presentation(deck)
    render = pymupdf.open(pdf)
    evaluation = json.loads((ROOT / "artifacts/reports/evaluation.json").read_text())
    paper = json.loads((ROOT / "artifacts/reports/paper_statistics.json").read_text())
    references = json.loads((ROOT / "docs/paper/references.json").read_text())
    assert len(source["slides"]) == len(prs.slides) == len(render) == 30
    assert abs(prs.slide_width / prs.slide_height - 16 / 9) < 0.001
    assert not prs.core_properties.author and not prs.core_properties.last_modified_by
    observations = []
    images = []
    charts = []
    for number, (slide, page, item) in enumerate(
        zip(prs.slides, render, source["slides"], strict=True), 1
    ):
        assert len(slide.notes_slide.notes_text_frame.text.split()) > 40
        assert all((ROOT / path).is_file() for path in item["sources"])
        words = page.get_text("words")
        pdf_text = compact(page.get_text())
        assert all(
            w[0] >= 15
            and w[2] <= page.rect.width - 15
            and w[1] >= 8
            and w[3] <= page.rect.height - 8
            for w in words
        ), number
        assert "\ufffd" not in page.get_text()
        for shape in slide.shapes:
            assert (
                shape.left >= 0
                and shape.top >= 0
                and shape.left + shape.width <= prs.slide_width + 100
                and shape.top + shape.height <= prs.slide_height + 100
            ), number
            if shape.has_text_frame and shape.text.strip():
                assert compact(shape.text) in pdf_text, (number, shape.text)
            if shape.has_chart:
                charts.append((number, shape.chart))
            if shape.shape_type == 13:
                images.append(number)
        observations.append(
            {
                "slide": number,
                "visible_words": len(words),
                "speaker_note_words": len(slide.notes_slide.notes_text_frame.text.split()),
            }
        )
    assert images == [7, 11, 14] and [x[0] for x in charts] == [21]
    cover = compact(render[0].get_text())
    assert all(f"author{i}:" in cover for i in range(1, 6)) and "instructor:" in cover
    table = next(s.table for s in prs.slides[15].shapes if s.has_table)
    for ri, key in enumerate(("accuracy", "precision", "recall", "f1", "false_positive_rate"), 1):
        for ci, model in enumerate(("multinomial", "bernoulli"), 1):
            assert table.cell(ri, ci).text == f"{100 * evaluation['models'][model][key]:.2f}%"
    paired_text = compact(render[17].get_text())
    for value in paper["paired"]["overall"].values():
        assert compact(f"{value:,}") in paired_text
    interval_text = compact(render[18].get_text())
    for value in paper["paired"]["bootstrap"]["differences"].values():
        for field in ("estimate", "lower", "upper"):
            assert f"{100 * value[field]:.2f}" in interval_text
    chart = charts[0][1]
    for series, model in zip(chart.series, ("multinomial", "bernoulli"), strict=True):
        matrix = evaluation["models"][model]["confusion_matrix"]
        assert list(series.values) == [
            matrix["fp"] * cost + matrix["fn"] for cost in (0, 10, 56, 100)
        ]
    x_values = [
        float(n.text)
        for n in chart._chartSpace.xpath(".//c:ser/c:xVal/c:numRef/c:numCache/c:pt/c:v")
    ]
    assert x_values == [0, 10, 56, 100, 0, 10, 56, 100]
    urls = set()
    for shape in prs.slides[27].shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                for run in p.runs:
                    if run.hyperlink.address:
                        urls.add(run.hyperlink.address)
    assert urls == {r["url"] for r in references}
    originals = {
        sha(ROOT / "docs/report/figures" / name)
        for name in ("dataset.png", "statistics.png", "detect.png")
    }
    with ZipFile(deck) as z:
        embedded = {
            hashlib.sha256(z.read(n)).hexdigest()
            for n in z.namelist()
            if n.startswith("ppt/media/")
        }
    assert embedded == originals
    files = [
        deck,
        pdf,
        HERE / "slides.json",
        HERE / "build_slides.py",
        HERE / "verify_slides.py",
        HERE / "presenter_notes.md",
        HERE / "requirements.txt",
    ]
    return {
        "task": "MSE-608",
        "result": "pass",
        "slides": 30,
        "speaker_notes": 30,
        "editable_native_chart": 1,
        "safe_source_screenshots": 3,
        "primary_references": 10,
        "widescreen": "16:9",
        "blank_authors": 5,
        "instructor_blank": True,
        "application_changes": False,
        "application_evidence": "Recorded release/paper checks reused; app tests not rerun for this publication task.",
        "source_reports": {
            str(p): sha(ROOT / p)
            for p in (
                "artifacts/reports/evaluation.json",
                "artifacts/reports/paper_statistics.json",
                "artifacts/reports/runtime_smoke.json",
            )
        },
        "files": {str(p.relative_to(ROOT)): sha(p) for p in files},
        "observations": observations,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    result = check()
    path = ROOT / "artifacts/reports/presentation.json"
    if args.record:
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    else:
        assert json.loads(path.read_text()) == result
    print("30-slide PPTX/PDF, notes, editable data, source screenshots and rendered bounds: PASS")
