"""Build the complete handbook from its reviewed structured source."""

import json
import math
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NAVY = "18374A"
TEAL = "146B73"
WIDTH = 174
TOC_ROWS = 28


def element(tag, **attrs):
    item = OxmlElement(tag)
    for key, value in attrs.items():
        item.set(qn(key) if ":" in key else key, str(value))
    return item


def hyperlink(paragraph, label, *, anchor=None, url=None, size=9):
    link = element("w:hyperlink")
    if anchor:
        link.set(qn("w:anchor"), anchor)
    if url:
        rid = paragraph.part.relate_to(
            url,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
            is_external=True,
        )
        link.set(qn("r:id"), rid)
    prop = element("w:rPr")
    prop.append(element("w:color", **{"w:val": TEAL}))
    prop.append(element("w:sz", **{"w:val": int(2 * size)}))
    run = element("w:r")
    run.append(prop)
    txt = element("w:t")
    txt.text = label
    run.append(txt)
    link.append(run)
    paragraph._p.append(link)


def setup():
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.top_margin = section.bottom_margin = Mm(18)
    section.left_margin = section.right_margin = Mm(18)
    section.header_distance = section.footer_distance = Mm(8)
    normal = doc.styles["Normal"]
    normal.font.name = "Liberation Sans"
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor.from_string(NAVY)
    normal.paragraph_format.line_spacing = 1.10
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.first_line_indent = Mm(0)
    for name, size, color in (("Heading 1", 20, NAVY), ("Heading 2", 12, TEAL)):
        style = doc.styles[name]
        style.font.name = "Liberation Sans"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.line_spacing = 1.04
        style.paragraph_format.space_before = Pt(8)
        style.paragraph_format.space_after = Pt(8)
        style.paragraph_format.keep_with_next = True
    for name in ("List Bullet", "List Number"):
        doc.styles[name].font.name = "Liberation Sans"
        doc.styles[name].font.size = Pt(10.5)
        doc.styles[name].paragraph_format.space_after = Pt(5)
    header = section.header.paragraphs[0]
    header.text = "MAILSENSE  /  COMPLETE PLATFORM GUIDE"
    header.runs[0].font.size = Pt(8)
    header.runs[0].font.color.rgb = RGBColor.from_string(TEAL)
    footer = section.footer.paragraphs[0]
    footer.text = "Tutorial · statistical methods · technical reference"
    footer.runs[0].font.size = Pt(8)
    footer.add_run("\t")
    footer.paragraph_format.tab_stops.add_tab_stop(Mm(WIDTH - 8))
    footer._p.append(element("w:fldSimple", **{"w:instr": "PAGE"}))
    doc.core_properties.title = "MailSense Complete Platform Guide"
    doc.core_properties.subject = "User tutorial and project reference"
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    doc.core_properties.keywords = "MailSense, probability, statistics, tutorial"
    return doc


def table(doc, block, chapter):
    columns, rows = block["columns"], block["rows"]
    fractions = block.get("widths")
    if not fractions:
        if columns[0] == "Package":
            fractions = [0.58, 0.18, 0.24]
        elif len(columns) == 2:
            fractions = [0.40, 0.60] if chapter != 24 else [0.49, 0.51]
        elif len(columns) == 4 and columns[0] == "Metric":
            fractions = [0.17, 0.37, 0.23, 0.23]
        else:
            fractions = [1 / len(columns)] * len(columns)
    t = doc.add_table(rows=1, cols=len(columns))
    t.autofit = False
    for col, fraction in zip(t.columns, fractions, strict=True):
        col.width = Mm(WIDTH * fraction)
    t._tbl.tblPr.append(element("w:tblLayout", **{"w:type": "fixed"}))
    for ri, values in enumerate([columns, *rows]):
        row = t.rows[0] if ri == 0 else t.add_row()
        row._tr.get_or_add_trPr().append(element("w:cantSplit"))
        if ri == 0:
            row._tr.get_or_add_trPr().append(element("w:tblHeader"))
        for cell, value, fraction in zip(row.cells, values, fractions, strict=True):
            cell.width = Mm(WIDTH * fraction)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            props = cell._tc.get_or_add_tcPr()
            props.append(
                element(
                    "w:shd",
                    **{
                        "w:fill": NAVY
                        if ri == 0
                        else ("EEF4F6" if ri % 2 else "FFFFFF")
                    },
                )
            )
            margins = element("w:tcMar")
            for edge, amount in (
                ("top", 65),
                ("bottom", 65),
                ("left", 85),
                ("right", 85),
            ):
                margins.append(element("w:" + edge, **{"w:w": amount, "w:type": "dxa"}))
            props.append(margins)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.03
            run = p.add_run(str(value))
            run.font.size = Pt(9.1 if columns[0] == "Package" else 10)
            run.font.bold = ri == 0
            if ri == 0:
                run.font.color.rgb = RGBColor(255, 255, 255)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def image(doc, block):
    source = ROOT / block["path"]
    height = block.get("height_mm", 88)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(2)
    pic = p.add_run().add_picture(str(source), width=Mm(WIDTH), height=Mm(height))
    with Image.open(source) as raw:
        w, h = raw.size
    left, top = block.get("crop_left", 0.17), block.get("crop_top", 0)
    visible = w * (1 - left) * height / WIDTH / h
    top = min(top, max(0, 1 - visible))
    bottom = max(0, 1 - top - visible)
    fill = pic._inline.graphic.graphicData.pic.blipFill
    fill.insert(
        1,
        element(
            "a:srcRect",
            l=round(left * 100000),
            t=round(top * 100000),
            b=round(bottom * 100000),
        ),
    )
    pic._inline.docPr.set("descr", block["caption"])
    p = doc.add_paragraph(block["caption"])
    p.paragraph_format.space_after = Pt(7)
    for run in p.runs:
        run.italic = True
        run.font.size = Pt(9)


def build():
    source = json.loads((HERE / "guide.json").read_text())
    pages = source["pages"]
    navpath = HERE / "guide_navigation.json"
    navigation = json.loads(navpath.read_text()) if navpath.exists() else {}
    toc_pages = math.ceil(len(pages) / TOC_ROWS)
    doc = setup()
    p = doc.add_paragraph("MAILSENSE")
    p.paragraph_format.space_before = Mm(18)
    p.runs[0].font.size = Pt(16)
    p.runs[0].bold = True
    p.runs[0].font.color.rgb = RGBColor.from_string(TEAL)
    p = doc.add_paragraph("Complete\nPlatform Guide")
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Mm(10)
    p.runs[0].font.size = Pt(35)
    p.runs[0].bold = True
    doc.add_paragraph(source["subtitle"])
    doc.add_paragraph(
        "Installation · six screen tutorials · worked mathematics\nArchitecture · APIs · testing · research · complete inventories"
    )
    p = doc.add_paragraph(
        "Project: Statistical Analysis and Probabilistic Email Spam Detection"
    )
    p.paragraph_format.space_after = Mm(10)
    for number in range(1, 6):
        p = doc.add_paragraph(
            f"Author {number}:  ______________________________________"
        )
        p.paragraph_format.space_after = Mm(4)
    doc.add_paragraph("Instructor:  _____________________________________")
    doc.add_paragraph(
        "Companion to the conference paper and 30-slide project presentation."
    )
    hyperlink(
        doc.add_paragraph(),
        "github.com/hixam001/mail-sense",
        url="https://github.com/hixam001/mail-sense",
        size=10,
    )
    for start in range(0, len(pages), TOC_ROWS):
        contents_heading = doc.add_heading(
            "Contents" + (" · continued" if start else ""), level=1
        )
        contents_heading.paragraph_format.page_break_before = True
        doc.add_paragraph(
            "Select a chapter title to jump to it. Page numbers refer to this PDF export."
        )
        for i, page in enumerate(pages[start : start + TOC_ROWS], start):
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(5)
            p.paragraph_format.line_spacing = 1.02
            p.paragraph_format.tab_stops.add_tab_stop(Mm(164))
            hyperlink(p, f"{page['id']}  {page['title']}", anchor=page["id"], size=9.5)
            p.add_run(
                "\t" + str(navigation.get(page["id"], i + toc_pages + 2))
            ).font.size = Pt(9.5)
    for page in pages:
        heading = doc.add_heading(f"{page['id']}  {page['title']}", level=1)
        heading.paragraph_format.page_break_before = True
        heading._p.insert(
            0,
            element(
                "w:bookmarkStart", **{"w:id": int(page["id"][1:]), "w:name": page["id"]}
            ),
        )
        heading._p.append(element("w:bookmarkEnd", **{"w:id": int(page["id"][1:])}))
        for block in page["blocks"]:
            kind = block["type"]
            if kind == "paragraph":
                doc.add_paragraph(block["text"])
            elif kind == "subheading":
                doc.add_heading(block["text"], level=2)
            elif kind == "table":
                table(doc, block, int(page["id"][1:]))
            elif kind in ("steps", "bullets"):
                for number, item in enumerate(block["items"], 1):
                    # Explicit numbers restart each tutorial and survive Markdown export.
                    doc.add_paragraph(
                        (f"{number}. " if kind == "steps" else "• ") + item
                    )
            elif kind == "image":
                image(doc, block)
            elif kind == "reference":
                doc.add_paragraph(block["text"])
                hyperlink(doc.add_paragraph(), block["url"], url=block["url"], size=8.5)
            elif kind in ("code", "equation"):
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = 1.05
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(7)
                p._p.get_or_add_pPr().append(element("w:shd", **{"w:fill": "EEF4F6"}))
                run = p.add_run(block["text"])
                run.font.name = (
                    "Liberation Mono" if kind == "code" else "Liberation Sans"
                )
                run.font.size = Pt(8.4 if kind == "code" else 10)
            else:
                raise ValueError(kind)
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(7)
        p.add_run("Sources: ").font.size = Pt(8)
        for index, path in enumerate(page["sources"]):
            if index:
                p.add_run(" · ").font.size = Pt(8)
            hyperlink(
                p,
                path,
                url="https://github.com/hixam001/mail-sense/"
                + ("tree" if (ROOT / path).is_dir() else "blob")
                + "/main/"
                + path,
                size=8,
            )
    doc.save(HERE / "MailSense_Complete_Guide.docx")
    markdown(source)
    print(f"Built editable handbook and searchable source: {len(pages)} chapters")


def markdown(source):
    import os

    lines = [
        "# " + source["title"],
        "",
        source["subtitle"],
        "",
        "Five author fields and the instructor field are reserved blank in the DOCX/PDF.",
        "",
        "## Contents",
        "",
    ]
    for page in source["pages"]:
        lines.append(f"- [{page['id']} · {page['title']}](#{page['id'].lower()})")
    for page in source["pages"]:
        lines.extend(
            [
                "",
                f'<a id="{page["id"].lower()}"></a>',
                "",
                f"## {page['id']} · {page['title']}",
                "",
            ]
        )
        for b in page["blocks"]:
            kind = b["type"]
            if kind == "paragraph":
                lines.append(b["text"])
            elif kind == "subheading":
                lines.append("### " + b["text"])
            elif kind in ("code", "equation"):
                lines.extend(
                    [
                        "```"
                        + (
                            "bash"
                            if kind == "code" and not b["text"].startswith("{")
                            else "text"
                        ),
                        b["text"],
                        "```",
                    ]
                )
            elif kind in ("steps", "bullets"):
                lines.extend(
                    (f"{i}. " if kind == "steps" else "- ") + item
                    for i, item in enumerate(b["items"], 1)
                )
            elif kind == "image":
                rel = Path(os.path.relpath(ROOT / b["path"], HERE)).as_posix()
                lines.extend([f"![{b['caption']}]({rel})", "", b["caption"]])
            elif kind == "reference":
                lines.append(f"{b['text']} [Primary source]({b['url']})")
            elif kind == "table":
                for row in [b["columns"], ["---"] * len(b["columns"]), *b["rows"]]:
                    lines.append(
                        "| "
                        + " | ".join(str(c).replace("|", "\\|") for c in row)
                        + " |"
                    )
            lines.append("")
        links = [
            f"[{p}]({Path(os.path.relpath(ROOT / p, HERE)).as_posix()})"
            for p in page["sources"]
        ]
        lines.extend(["Sources: " + ", ".join(links), ""])
    (HERE / "MailSense_Complete_Guide.md").write_text("\n".join(lines).rstrip() + "\n")


if __name__ == "__main__":
    build()
