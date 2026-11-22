"""Build the editable conference paper and data-derived publication figures."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = json.loads((ROOT / "artifacts/reports/paper_statistics.json").read_text())
MANUSCRIPT = json.loads((HERE / "manuscript.json").read_text())
REFERENCES = json.loads((HERE / "references.json").read_text())
COLUMN = Mm(84.5)
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Liberation Serif"],
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def figures():
    folder = HERE / "figures"
    folder.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(3.30, 2.52))
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")

    def box(x, y, w, h, text):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.012",
                facecolor="white",
                edgecolor="#253b50",
                linewidth=0.9,
            )
        )
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.8)

    def arrow(a, b):
        ax.annotate(
            "", xy=b, xytext=a, arrowprops={"arrowstyle": "->", "color": "#253b50", "lw": 0.95}
        )

    box(0.23, 0.83, 0.54, 0.13, "Retained corpus\n5,862 messages")
    box(0.02, 0.57, 0.43, 0.14, "Train: 4,689\nVocabulary fitted here")
    box(0.57, 0.57, 0.41, 0.14, "Test: 1,173\nIDs fixed and disjoint")
    box(0.02, 0.31, 0.43, 0.13, "Frozen Multinomial\nand Bernoulli models")
    box(0.57, 0.31, 0.41, 0.13, "Matched predictions\nSame test messages")
    box(0.18, 0.04, 0.64, 0.14, "Paired errors, exact test\nand stratified bootstrap")
    arrow((0.38, 0.82), (0.23, 0.72))
    arrow((0.65, 0.82), (0.77, 0.72))
    arrow((0.235, 0.56), (0.235, 0.45))
    arrow((0.775, 0.56), (0.775, 0.45))
    arrow((0.46, 0.375), (0.56, 0.375))
    arrow((0.77, 0.30), (0.55, 0.19))
    fig.tight_layout(pad=0.2)
    fig.savefig(folder / "pipeline.png", dpi=450, metadata={"Software": ""})
    fig.savefig(folder / "pipeline.svg", metadata={"Creator": "", "Date": None})
    plt.close(fig)
    fig, axes = plt.subplots(3, 1, figsize=(3.30, 2.62))
    for ax, key, label, limits in zip(
        axes,
        ("accuracy", "recall", "false_positive_rate"),
        ("Accuracy", "Spam recall", "False-positive rate"),
        ((0, 8), (0, 25), (-1, 1)),
        strict=True,
    ):
        value = DATA["paired"]["bootstrap"]["differences"][key]
        estimate, lo, hi = (100 * value[k] for k in ("estimate", "lower", "upper"))
        ax.axvline(0, color=".5", lw=0.8, ls="--")
        ax.errorbar(
            estimate,
            0,
            xerr=[[estimate - lo], [hi - estimate]],
            fmt="o",
            markersize=4,
            color="#213f5b",
            capsize=3,
            elinewidth=1,
        )
        ax.set(xlim=limits, ylim=(-0.6, 0.6), yticks=[])
        ax.set_title(label, loc="left", fontsize=9, pad=1)
        ax.set_xlabel("Difference (percentage points)", fontsize=8.4, labelpad=1)
        ax.tick_params(axis="x", labelsize=8, pad=1)
        ax.spines["left"].set_visible(False)
        ax.text(
            0.99,
            0.82,
            f"{estimate:.2f} [{lo:.2f}, {hi:.2f}]",
            transform=ax.transAxes,
            ha="right",
            fontsize=8,
        )
    fig.tight_layout(pad=0.35, h_pad=0.85)
    fig.savefig(folder / "differences.png", dpi=450, metadata={"Software": ""})
    fig.savefig(folder / "differences.svg", metadata={"Creator": "", "Date": None})
    plt.close(fig)
    for name in ("pipeline.svg", "differences.svg"):
        path = folder / name
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def font(run, size=None, bold=None):
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Times New Roman")
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    return run


def hyperlink(paragraph, label, target, size=8.7):
    tag = OxmlElement("w:hyperlink")
    tag.set(
        qn("r:id"), paragraph.part.relate_to(target, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    )
    run = OxmlElement("w:r")
    props = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), "Times New Roman")
    props.append(fonts)
    length = OxmlElement("w:sz")
    length.set(qn("w:val"), str(round(size * 2)))
    props.append(length)
    run.append(props)
    text = OxmlElement("w:t")
    text.text = label
    run.append(text)
    tag.append(run)
    paragraph._p.append(tag)


def configure(section, columns=1):
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(18)
    section.bottom_margin = Mm(18)
    section.left_margin = Mm(17)
    section.right_margin = Mm(17)
    section.header_distance = Mm(8)
    section.footer_distance = Mm(8)
    cols = section._sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        section._sectPr.append(cols)
    cols.set(qn("w:num"), str(columns))
    cols.set(qn("w:space"), "397")
    cols.set(qn("w:equalWidth"), "1")


def styles(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10.5)
    pf = normal.paragraph_format
    pf.space_after = Pt(4)
    pf.line_spacing = Pt(12)
    pf.first_line_indent = Pt(0)
    pf.widow_control = True
    for name, size in [
        ("Paper Heading", 10.5),
        ("Paper Subheading", 10.5),
        ("Caption", 9),
        ("Equation", 9.8),
    ]:
        style = doc.styles.add_style(name, 1) if name not in doc.styles else doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(size)
        style.paragraph_format.first_line_indent = Pt(0)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.line_spacing = Pt(size + 1.5)
    doc.styles["Paper Heading"].font.bold = True
    doc.styles["Paper Heading"].paragraph_format.space_before = Pt(5)
    doc.styles["Paper Heading"].paragraph_format.keep_with_next = True
    doc.styles["Paper Subheading"].font.italic = True
    doc.styles["Paper Subheading"].paragraph_format.space_before = Pt(4)
    doc.styles["Paper Subheading"].paragraph_format.keep_with_next = True
    doc.styles["Caption"].paragraph_format.space_after = Pt(7)
    doc.styles["Caption"].font.bold = False
    doc.styles["Caption"].font.italic = False
    doc.styles["Equation"].paragraph_format.space_after = Pt(3)
    doc.styles["Equation"].paragraph_format.line_spacing = Pt(11.5)


def plain(doc, text, style=None):
    p = doc.add_paragraph(style=style)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if style is None:
        p.paragraph_format.first_line_indent = Mm(3.1)
    font(p.add_run(text))
    return p


def math_paragraph(doc, text):
    p = doc.add_paragraph(style="Equation")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    math = OxmlElement("m:oMath")

    def mr(text):
        r = OxmlElement("m:r")
        rpr = OxmlElement("w:rPr")
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), "19")
        rpr.append(sz)
        r.append(rpr)
        t = OxmlElement("m:t")
        t.text = text
        r.append(t)
        return r

    indices = {
        "θcj": ("θ", "cj"),
        "πc": ("π", "c"),
        "Tcj": ("T", "cj"),
        "Tck": ("T", "ck"),
        "xj": ("x", "j"),
        "qcj": ("q", "cj"),
        "Dcj": ("D", "cj"),
        "Nc": ("N", "c"),
        "bj": ("b", "j"),
        "scoreM": ("score", "M"),
        "scoreB": ("score", "B"),
        "Σj": ("Σ", "j"),
        "Σk": ("Σ", "k"),
    }
    for token in re.split("(" + "|".join(indices) + ")", text):
        if not token:
            continue
        if token in indices:
            base, sub = indices[token]
            node = OxmlElement("m:sSub")
            e = OxmlElement("m:e")
            e.append(mr(base))
            node.append(e)
            s = OxmlElement("m:sub")
            s.append(mr(sub))
            node.append(s)
            math.append(node)
        else:
            math.append(mr(token))
    p._p.append(math)


def data_table(doc, name):
    rates = DATA["models"]
    paired = DATA["paired"]["overall"]

    def rate(model, key):
        value = rates[model][key]
        return f"{100 * value['estimate']:.2f}%\n[{100 * value['lower']:.2f}, {100 * value['upper']:.2f}]"

    definitions = {
        "accounting": (
            "TABLE I. Corpus preparation and split counts",
            ["Stage", "Records"],
            [
                ["Candidate messages", "6,046"],
                ["Parsed / MIME rejected", "5,992 / 54"],
                ["Duplicate exclusions", "130"],
                ["Retained ham / spam", "4,107 / 1,755"],
                ["Training ham / spam", "3,285 / 1,404"],
                ["Test ham / spam", "822 / 351"],
            ],
        ),
        "word": (
            "TABLE II. Word “free”, all-record scope",
            ["Class", "Present", "Absent", "Total"],
            [
                ["Spam", "811", "944", "1,755"],
                ["Ham", "577", "3,530", "4,107"],
                ["Total", "1,388", "4,474", "5,862"],
            ],
        ),
        "metrics": (
            "TABLE III. Test rates and Wilson 95% intervals",
            ["Measure", "Multinomial", "Bernoulli"],
            [
                [label, rate("multinomial", key), rate("bernoulli", key)]
                for label, key in [
                    ("Accuracy", "accuracy"),
                    ("Precision", "precision"),
                    ("Recall", "recall"),
                    ("FPR", "false_positive_rate"),
                ]
            ],
        ),
        "paired": (
            "TABLE IV. Paired correctness on 1,173 emails",
            ["", "M correct", "M wrong"],
            [
                ["B correct", str(paired["both_correct"]), str(paired["bernoulli_only"])],
                ["B wrong", str(paired["multinomial_only"]), str(paired["both_wrong"])],
            ],
        ),
        "differences": (
            "TABLE V. Paired differences in percentage points",
            ["Measure", "Difference", "95% interval"],
            [
                [
                    label,
                    f"{100 * DATA['paired']['bootstrap']['differences'][key]['estimate']:.2f}",
                    f"[{100 * DATA['paired']['bootstrap']['differences'][key]['lower']:.2f}, {100 * DATA['paired']['bootstrap']['differences'][key]['upper']:.2f}]",
                ]
                for label, key in [
                    ("Accuracy", "accuracy"),
                    ("Recall", "recall"),
                    ("FPR", "false_positive_rate"),
                ]
            ],
        ),
    }
    caption, columns, rows = definitions[name]
    p = plain(doc, caption, "Caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    table = doc.add_table(rows=1, cols=len(columns))
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    weights = (
        [0.45, 0.55]
        if len(columns) == 2
        else ([0.28, 0.36, 0.36] if len(columns) == 3 else [0.28, 0.24, 0.24, 0.24])
    )
    for col, weight in zip(table.columns, weights, strict=True):
        col.width = int(COLUMN * weight)
    for i, label in enumerate(columns):
        table.rows[0].cells[i].text = label
    for row in rows:
        cells = table.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = text
    for ri, row in enumerate(table.rows):
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        if ri == 0:
            repeat = OxmlElement("w:tblHeader")
            row._tr.get_or_add_trPr().append(repeat)
        for i, cell in enumerate(row.cells):
            cell.width = int(COLUMN * weights[i])
            tcPr = cell._tc.get_or_add_tcPr()
            margins = OxmlElement("w:tcMar")
            for edge, value in [("top", 45), ("bottom", 45), ("left", 45), ("right", 45)]:
                node = OxmlElement("w:" + edge)
                node.set(qn("w:w"), str(value))
                node.set(qn("w:type"), "dxa")
                margins.append(node)
            tcPr.append(margins)
            borders = OxmlElement("w:tcBorders")
            if ri in (0, len(table.rows) - 1):
                for edge in ["top", "bottom"] if ri == 0 else ["bottom"]:
                    border = OxmlElement("w:" + edge)
                    border.set(qn("w:val"), "single")
                    border.set(qn("w:sz"), "4")
                    border.set(qn("w:color"), "555555")
                    borders.append(border)
            tcPr.append(borders)
            for par in cell.paragraphs:
                par.paragraph_format.first_line_indent = Pt(0)
                par.paragraph_format.space_after = Pt(0)
                par.paragraph_format.line_spacing = Pt(10.5)
                par.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
                for run in par.runs:
                    font(run, 9, ri == 0)
    after = doc.add_paragraph()
    after.paragraph_format.space_after = Pt(3)
    after.paragraph_format.line_spacing = Pt(2)
    after.paragraph_format.first_line_indent = Pt(0)
    font(after.add_run(""), 2)


def block(doc, b):
    kind = b["type"]
    text = b.get("text", "")
    if kind == "heading":
        p = plain(doc, text, "Paper Heading")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif kind == "subheading":
        plain(doc, text, "Paper Subheading")
    elif kind == "equation":
        math_paragraph(doc, text)
    elif kind == "table":
        data_table(doc, b["name"])
    elif kind == "figure":
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.left_indent = Pt(0)
        p.paragraph_format.right_indent = Pt(0)
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.line_spacing = 1.0
        p.add_run().add_picture(str(HERE / "figures" / f"{b['name']}.png"), width=Mm(78))
        plain(doc, b["caption"], "Caption")
    elif kind == "paper_title":
        p = plain(doc, text)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_after = Pt(9)
        p.paragraph_format.line_spacing = Pt(14.5)
        for run in p.runs:
            font(run, 13, True)
    elif kind in ("abstract", "keywords"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Pt(0)
        font(p.add_run("Abstract. " if kind == "abstract" else "Keywords: "), 9.8, True)
        font(p.add_run(text), 9.8)
    elif kind == "references":
        for reference in REFERENCES:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.left_indent = Mm(5)
            p.paragraph_format.first_line_indent = Mm(-5)
            p.paragraph_format.line_spacing = Pt(10)
            p.paragraph_format.space_after = Pt(5)
            font(p.add_run(f"[{reference['id']}] {reference['text']} "), 8.8)
            hyperlink(p, "Online source", reference["url"], 8.8)
    else:
        plain(doc, text)


def build():
    figures()
    doc = Document()
    styles(doc)
    configure(doc.sections[0])
    settings = doc.settings.element
    lang = OxmlElement("w:themeFontLang")
    lang.set(qn("w:val"), "en-US")
    settings.append(lang)
    cp = doc.core_properties
    cp.title = MANUSCRIPT["title"]
    cp.subject = "Paired statistical analysis of email classification"
    cp.author = ""
    cp.last_modified_by = ""
    cp.comments = ""
    cp.keywords = "Naive Bayes, statistics, probability, paired bootstrap"
    cp.created = datetime.now(UTC)
    cp.modified = cp.created
    cover = doc.sections[0]
    cover.different_first_page_header_footer = True
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(76)
    p.paragraph_format.first_line_indent = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run("CONFERENCE-STYLE RESEARCH PAPER"), 11)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(17)
    p.paragraph_format.space_after = Pt(28)
    p.paragraph_format.line_spacing = Pt(27)
    font(p.add_run(MANUSCRIPT["title"]), 23, True)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    font(p.add_run("Probability and Statistics"), 12)
    for index in range(1, 6):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_before = Pt(12)
        font(p.add_run(f"Author {index}:  ____________________________________"), 11)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(28)
    font(p.add_run("Instructor:  ____________________________________"), 11)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(34)
    font(p.add_run("Code, data provenance and reproduction instructions"), 9.5)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    hyperlink(p, "github.com/hixam001/mail-sense", "https://github.com/hixam001/mail-sense", 10)
    body = doc.add_section(WD_SECTION_START.NEW_PAGE)
    configure(body, 2)
    body.different_first_page_header_footer = False
    body.header.is_linked_to_previous = False
    body.footer.is_linked_to_previous = False
    hp = body.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hp.paragraph_format.first_line_indent = Pt(0)
    font(hp.add_run("MailSense | Paired Error Analysis and Probabilistic Evidence"), 8)
    fp = body.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.paragraph_format.first_line_indent = Pt(0)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    fp._p.append(fld)
    for index, page in enumerate(MANUSCRIPT["pages"]):
        for col in ("left", "right"):
            for item in page[col]:
                block(doc, item)
            if col == "left":
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(0)
                p.add_run().add_break(WD_BREAK.COLUMN)
        if index < len(MANUSCRIPT["pages"]) - 1:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            p.add_run().add_break(WD_BREAK.PAGE)
    out = HERE / "MailSense_Research_Paper.docx"
    doc.save(out)
    print(out)


if __name__ == "__main__":
    build()
