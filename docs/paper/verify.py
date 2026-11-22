"""Check the rendered paper, editable layout and its numerical provenance."""

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from zipfile import ZipFile

import pymupdf
from docx import Document
from lxml import etree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    manuscript = json.loads((HERE / "manuscript.json").read_text())
    references = json.loads((HERE / "references.json").read_text())
    stats = json.loads((ROOT / "artifacts/reports/paper_statistics.json").read_text())
    source = json.loads((ROOT / "artifacts/reports/evaluation.json").read_text())
    docx = HERE / "MailSense_Research_Paper.docx"
    pdf = HERE / "MailSense_Research_Paper.pdf"
    assert manuscript["authors"] == 5 and manuscript["instructor_blank"]
    assert not manuscript["submission_date"] and not manuscript["affiliations"]
    paragraphs = [b.get("text", "") for p in manuscript["pages"] for col in p.values() for b in col]
    text = "\n".join(paragraphs)
    assert "—" not in text
    assert (
        {int(n) for n in re.findall(r"\[(\d+)\]", text)}
        == {r["id"] for r in references}
        == set(range(1, 11))
    )
    assert len({r["url"] for r in references}) == 10
    assert all(r["url"].startswith("https://") for r in references)
    assert stats["private_artifacts_unchanged"] and stats["result"] == "pass"
    assert stats["test_ids_sha256"] == source["test_ids_sha256"]
    assert stats["artifact_id"] == source["artifact_id"]
    paired = stats["paired"]
    total = paired["overall"]
    n = stats["test_count"]
    assert sum(total.values()) == n == 1173
    b, c = total["multinomial_only"], total["bernoulli_only"]
    expected_p = min(1.0, 2 * sum(math.comb(b + c, k) for k in range(min(b, c) + 1)) / 2 ** (b + c))
    assert math.isclose(expected_p, paired["exact_mcnemar_p"], rel_tol=1e-13)
    assert (b - c) / n == paired["bootstrap"]["differences"]["accuracy"]["estimate"]
    for actual, correct in [("ham", "tn"), ("spam", "tp")]:
        cells = paired["by_actual_class"][actual]
        assert (
            cells["both_correct"] + cells["multinomial_only"]
            == source["models"]["multinomial"]["confusion_matrix"][correct]
        )
        assert (
            cells["both_correct"] + cells["bernoulli_only"]
            == source["models"]["bernoulli"]["confusion_matrix"][correct]
        )
    m, bn = [source["models"][name]["confusion_matrix"] for name in ("multinomial", "bernoulli")]
    assert (bn["fn"] - m["fn"]) / (m["fp"] - bn["fp"]) == stats["cost_sensitivity"][
        "observed_break_even_false_positive_cost"
    ]
    for ratio, values in stats["cost_sensitivity"]["examples"].items():
        assert values["multinomial"] == m["fp"] * int(ratio) + m["fn"]
        assert values["bernoulli"] == bn["fp"] * int(ratio) + bn["fn"]
    document = Document(docx)
    assert len(document.tables) == 5
    for row, (key, label) in zip(
        document.tables[2].rows[1:],
        [
            ("accuracy", "Accuracy"),
            ("precision", "Precision"),
            ("recall", "Recall"),
            ("false_positive_rate", "FPR"),
        ],
        strict=True,
    ):
        assert row.cells[0].text == label
        for column, name in enumerate(("multinomial", "bernoulli"), 1):
            value = stats["models"][name][key]
            assert (
                row.cells[column].text
                == f"{value['estimate'] * 100:.2f}%\n[{value['lower'] * 100:.2f}, {value['upper'] * 100:.2f}]"
            )
    for row, key in zip(
        document.tables[4].rows[1:], ("accuracy", "recall", "false_positive_rate"), strict=True
    ):
        value = paired["bootstrap"]["differences"][key]
        assert row.cells[1].text == f"{100 * value['estimate']:.2f}"
        assert row.cells[2].text == f"[{100 * value['lower']:.2f}, {100 * value['upper']:.2f}]"
    with ZipFile(docx) as archive:
        embedded = sorted(
            hashlib.sha256(archive.read(name)).hexdigest()
            for name in archive.namelist()
            if name.startswith("word/media/") and name.endswith(".png")
        )
        assert embedded == sorted(sha(path) for path in (HERE / "figures").glob("*.png"))
        xml = etree.fromstring(archive.read("word/document.xml"))
        sections = xml.findall(".//w:sectPr", NS)
        assert len(sections) == 2
        assert sections[0].find("w:cols", NS).get("{" + NS["w"] + "}num") == "1"
        assert sections[1].find("w:cols", NS).get("{" + NS["w"] + "}num") == "2"
        drawings = xml.findall(".//w:drawing", NS)
        assert len(drawings) == 2
        for drawing in drawings:
            parent = drawing.xpath("ancestor::w:p", namespaces=NS)[0]
            spacing = parent.find("w:pPr/w:spacing", NS)
            assert spacing is not None and spacing.get("{" + NS["w"] + "}lineRule") == "auto", (
                "Inline figure clipped by exact line spacing"
            )
        core = etree.fromstring(archive.read("docProps/core.xml"))
        for element in core:
            if etree.QName(element).localname in ("creator", "lastModifiedBy"):
                assert not element.text
        assert not xml.findall(".//w:ins", NS) and not xml.findall(".//w:del", NS)
    rendered = pymupdf.open(pdf)
    assert len(rendered) == 8
    cover = rendered[0].get_text()
    assert all(f"Author {i}:" in cover for i in range(1, 6)) and "Instructor:" in cover
    assert "Submission" not in cover and "Affiliation" not in cover
    observations = []
    image_pages = []
    for index, page in enumerate(rendered):
        words = page.get_text("words")
        assert not any("\ufffd" in w[4] for w in words)
        assert all(
            w[0] >= 42
            and w[2] <= page.rect.width - 42
            and w[1] >= 15
            and w[3] <= page.rect.height - 15
            for w in words
        )
        if index:
            body = [w for w in words if 48 <= w[1] < 790]
            left = [w for w in body if w[2] < page.rect.width / 2]
            right = [w for w in body if w[0] > page.rect.width / 2]
            assert len(left) > 100 and len(right) > 100, "Missing two-column body"
        images = []
        for item in page.get_images():
            for rect in page.get_image_rects(item[0]):
                assert rect.width > 220 and rect.height > 165
                assert (
                    rect.x0 >= 42
                    and rect.x1 <= page.rect.width - 42
                    and rect.y0 >= 48
                    and rect.y1 < 790
                )
                if index + 1 == 4:
                    assert rect.x0 >= 307 and rect.x1 <= 548
                else:
                    assert rect.x0 >= 48 and rect.x1 <= 288
                images.append([round(v, 2) for v in rect])
        if images:
            image_pages.append(index + 1)
        observations.append({"page": index + 1, "words": len(words), "figure_rectangles": images})
    assert image_pages == [4, 7]
    assert "REFERENCES" in rendered[7].get_text() and "[10]" in rendered[7].get_text()
    assert sum(len(page.get_links()) for page in rendered) >= 11
    report = {
        "task": "MSE-607",
        "result": "pass",
        "pages": 8,
        "cover_pages": 1,
        "two_column_pages": 7,
        "blank_author_fields": 5,
        "instructor_blank": True,
        "submission_date_field": False,
        "references": 10,
        "tables": 5,
        "scientific_figures": 2,
        "application_baseline": "v1.0.0",
        "python_tests_after_extension": 418,
        "originality": "Original manuscript with citations; similarity percentage not measured by an institutional checker.",
        "scope": "Secondary exploratory analysis; models, thresholds and private artifacts unchanged.",
        "page_observations": observations,
        "files": {
            str(p.relative_to(ROOT)): sha(p)
            for p in (
                docx,
                pdf,
                HERE / "manuscript.json",
                HERE / "references.json",
                HERE / "build.py",
                HERE / "verify.py",
                HERE / "requirements.txt",
                ROOT / "artifacts/reports/paper_statistics.json",
                *sorted((HERE / "figures").glob("*")),
            )
        },
        "rendering": "LibreOffice PDF export; A4; Times New Roman with Linux-compatible serif fallback",
    }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    result = verify()
    if args.record:
        (ROOT / "artifacts/reports/paper_document.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )
    else:
        assert json.loads((ROOT / "artifacts/reports/paper_document.json").read_text()) == result
    print(
        "Eight rendered pages, two columns, five blank authors, references, figures and independent numerical reconciliation: PASS"
    )
