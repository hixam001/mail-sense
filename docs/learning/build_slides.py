"""Create the editable project presentation from measured local reports."""

import json
import re
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTENT = json.loads((HERE / "slides.json").read_text())
E = json.loads((ROOT / "artifacts/reports/evaluation.json").read_text())
R = json.loads((ROOT / "artifacts/reports/paper_statistics.json").read_text())
REFS = json.loads((ROOT / "docs/paper/references.json").read_text())
NAVY = "17365D"
TEAL = "14786E"
ORANGE = "B95328"
INK = "172D45"
MUTED = "4F6379"
PALE = "EDF3F8"
WHITE = "FFFFFF"
LINE = "CFDCE8"
FONT = "Liberation Sans"


def readable(value):
    value = re.sub(
        r"\b(approximately|localhost|Node|npm|Python|uv|Stratified|seed|ham|spam|all|Same|same|on|below|Created|Slide|to|Wilson|vs|Absent|present|stratified)(?=\d)",
        r"\1 ",
        value,
    )
    value = re.sub(r"(?<=\d)(s|minutes|seconds|KiB)\b", r" \1", value)
    return value


def rgb(value):
    return RGBColor.from_string(value)


def box(slide, x, y, w, h, fill=WHITE, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s._element.spPr.append(OxmlElement("a:effectLst"))
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(0.6)
    else:
        s.line.fill.background()
    return s


def text(slide, x, y, w, h, value, size=22, color=INK, bold=False, align=PP_ALIGN.LEFT):
    value = readable(value)
    s = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = s.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(value.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = align
        p.font.name = FONT
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = rgb(color)
        p.space_after = Pt(5)
        p.line_spacing = 1.08
    return s


def bullets(slide, items, x=0.7, y=1.8, w=11.9, h=4.6, size=24, color=INK):
    s = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = s.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "•  " + item
        p.font.name = FONT
        p.font.size = Pt(size)
        p.font.color.rgb = rgb(color)
        p.line_spacing = 1.12
        p.space_after = Pt(16)
    return s


def table(slide, x, y, w, h, columns, rows, widths=None, size=19):
    t = slide.shapes.add_table(
        len(rows) + 1, len(columns), Inches(x), Inches(y), Inches(w), Inches(h)
    ).table
    if widths:
        for c, fraction in zip(t.columns, widths, strict=True):
            c.width = Inches(w * fraction)
    for ri, row in enumerate([columns, *rows]):
        for ci, value in enumerate(row):
            cell = t.cell(ri, ci)
            cell.text = readable(str(value))
            cell.margin_left = Inches(0.1)
            cell.margin_right = Inches(0.07)
            cell.margin_top = Inches(0.07)
            cell.margin_bottom = Inches(0.05)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(NAVY if ri == 0 else (WHITE if ri % 2 else PALE))
            for p in cell.text_frame.paragraphs:
                p.font.name = FONT
                p.font.size = Pt(size)
                p.font.bold = ri == 0
                p.font.color.rgb = rgb(WHITE if ri == 0 else INK)
                p.alignment = PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.CENTER
    return t


def line(slide, x, y, w, h, color=LINE, width=1.0):
    s = slide.shapes.add_connector(1, Inches(x), Inches(y), Inches(x + w), Inches(y + h))
    s._element.spPr.append(OxmlElement("a:effectLst"))
    s.line.color.rgb = rgb(color)
    s.line.width = Pt(width)
    return s


def shot(slide, name, x, y, w, h, crop):
    p = slide.shapes.add_picture(
        str(ROOT / "docs/report/figures" / name),
        Inches(x),
        Inches(y),
        width=Inches(w),
        height=Inches(h),
    )
    left, top, bottom, right = crop
    p.crop_left = left
    p.crop_top = top
    p.crop_bottom = bottom
    p.crop_right = right
    return p


def panel(slide, x, y, w, h, title, body, accent=NAVY):
    box(slide, x, y, w, h, WHITE, LINE)
    box(slide, x, y, 0.055, h, accent)
    text(slide, x + 0.22, y + 0.2, w - 0.42, 0.6, title, 23, accent, True)
    text(slide, x + 0.22, y + 1, w - 0.42, h - 1.14, body, 22)


def base(prs, index, item):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    dark = item["layout"] in ("cover", "closing")
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(NAVY if dark else PALE)
    if not dark:
        text(s, 0.65, 0.28, 12, 0.25, item["kicker"], 11, MUTED, True)
        text(s, 0.65, 0.76, 12.1, 0.73, item["title"], 32, INK, True)
        line(s, 0.65, 1.52, 12, 0, LINE, 0.8)
    source = "Evidence: " + "; ".join(Path(p).name for p in item["sources"][:2])
    text(s, 0.65, 7.10, 11.85, 0.22, source, 9.5, "B9CDE2" if dark else MUTED)
    text(
        s,
        12.35,
        7.07,
        0.34,
        0.25,
        f"{index:02}",
        10,
        "B9CDE2" if dark else MUTED,
        align=PP_ALIGN.RIGHT,
    )
    notes = (
        item["notes"]
        + "\n\nProject sources:\n"
        + "\n".join(
            "https://github.com/hixam001/mail-sense/blob/main/" + p for p in item["sources"]
        )
    )
    if item["layout"] == "references":
        notes += "\n\n" + "\n".join(f"[{r['id']}] {r['text']} {r['url']}" for r in REFS)
    s.notes_slide.notes_text_frame.text = notes
    return s


def draw(prs, index, item):
    s = base(prs, index, item)
    layout = item["layout"]
    body = item["body"]
    if layout == "cover":
        text(s, 0.7, 0.75, 11.9, 0.4, "PROBABILITY IN PRACTICE", 15, "B9CDE2", True)
        text(s, 0.68, 1.43, 12, 1.0, "MailSense", 60, WHITE, True)
        text(s, 0.73, 2.6, 11.8, 0.72, item["kicker"], 22, "D7E5F3", True)
        text(s, 0.73, 3.65, 11.8, 1.05, "\n".join(body), 25, WHITE)
        for i in range(5):
            text(s, 0.73 + i * 2.48, 5.50, 2.30, 0.5, f"Author {i + 1}: __________", 15, WHITE)
        text(s, 0.73, 6.28, 8, 0.4, "Instructor: __________________________", 17, WHITE)
    elif layout == "statement":
        text(
            s,
            0.78,
            1.94,
            11.7,
            1.25,
            "What does a “better” spam classifier actually mean?",
            36,
            NAVY,
            True,
        )
        bullets(s, body, 0.83, 3.35, 11.3, 2.8, 27)
    elif layout == "modules":
        for i, value in enumerate(body):
            x = 0.7 + (i % 2) * 6.08
            y = 1.83 + (i // 2) * 1.45
            a, b = value.split(": ", 1)
            box(s, x, y, 5.91, 1.23, WHITE, LINE)
            text(s, x + 0.20, y + 0.17, 5.5, 0.36, a, 23, NAVY, True)
            text(s, x + 0.20, y + 0.65, 5.5, 0.4, b, 19)
    elif layout == "architecture":
        for i, (title, desc) in enumerate(
            zip(
                body,
                [
                    "Browser · localhost:5173",
                    "Local API ·127.0.0.1:8000",
                    "Prepared through CLI; read during use",
                ],
                strict=True,
            )
        ):
            y = 1.9 + i * 1.42
            box(s, 0.85, y, 8.15, 1.0, WHITE, LINE)
            text(s, 1.12, y + 0.14, 7.6, 0.35, title, 25, NAVY, True)
            text(s, 1.12, y + 0.59, 7.6, 0.28, desc, 17, MUTED)
            if i < 2:
                text(s, 4.5, y + 1.01, 0.5, 0.38, "↓", 22, TEAL, True)
        text(s, 9.48, 2.0, 3.0, 0.4, "ONE COMPUTER", 17, TEAL, True)
        text(
            s,
            9.48,
            2.7,
            3,
            2.95,
            "No database\nNo accounts\nNo mail service\nNo external inference",
            22,
        )
    elif layout == "accounting":
        stages = [("6,046", "candidates"), ("5,992", "parsed"), ("5,862", "retained")]
        for i, (number, label) in enumerate(stages):
            x = 0.8 + i * 4.18
            box(s, x, 2.05, 3.75, 2.18, WHITE, LINE)
            text(s, x + 0.15, 2.43, 3.45, 0.8, number, 48, NAVY, True, PP_ALIGN.CENTER)
            text(s, x + 0.15, 3.41, 3.45, 0.45, label, 24, MUTED, align=PP_ALIGN.CENTER)
        text(
            s,
            0.92,
            4.65,
            11.8,
            0.55,
            "−54 malformed MIME             −130 exact duplicates",
            23,
            ORANGE,
        )
        text(
            s,
            0.92,
            5.62,
            11.8,
            0.58,
            "4,107 ham +1,755 spam · five canonical Apache archives",
            25,
            TEAL,
            True,
        )
    elif layout == "experiment":
        table(
            s,
            0.85,
            1.95,
            7.7,
            2.20,
            ["Partition", "Ham", "Spam", "Total"],
            [["Train", "3,285", "1,404", "4,689"], ["Test", "822", "351", "1,173"]],
            [0.32, 0.22, 0.22, 0.24],
            22,
        )
        text(s, 9.05, 2.08, 3.35, 0.75, "60,135", 43, NAVY, True)
        text(s, 9.05, 2.92, 3.35, 0.7, "training features", 22)
        text(s, 9.05, 4.05, 3.35, 0.6, "12,200", 34, ORANGE, True)
        text(s, 9.05, 4.72, 3.35, 0.95, "held-out-only tokens excluded", 20)
        bullets(s, body, 0.96, 4.7, 7.2, 1.8, 19)
    elif layout == "screen":
        bullets(s, body, 0.72, 1.94, 4.25, 3.9, 22)
        shot(s, item["image"], 5.3, 1.88, 7.30, 4.80, item["crop"])
    elif layout == "descriptive":
        table(
            s,
            0.8,
            1.95,
            8.3,
            2.7,
            ["All-scope tokens/email", "Ham", "Spam"],
            [
                ["Mean", "278.097", "341.346"],
                ["Median", "152", "167"],
                ["Sample SD", "677.646", "724.547"],
            ],
            [0.48, 0.26, 0.26],
            20,
        )
        text(s, 9.55, 2.0, 2.9, 0.45, "SEPARATE FIXTURE", 14, TEAL, True)
        text(s, 9.55, 2.77, 2.9, 2.9, "[2,4,4,6]\nMean=4\nVariance=8/3\nQ1=3.5\nQ3=4.5", 24)
        text(
            s,
            0.9,
            5.35,
            8.1,
            1.05,
            "n−1 variance · interpolated quartiles\nMin/max whiskers · long right tails",
            22,
            MUTED,
        )
    elif layout == "word":
        table(
            s,
            0.82,
            1.95,
            11.7,
            2.6,
            ["Class", "Word present", "Word absent", "Total"],
            [
                ["Spam", "811", "944", "1,755"],
                ["Ham", "577", "3,530", "4,107"],
                ["Total", "1,388", "4,474", "5,862"],
            ],
            [0.25, 0.25, 0.25, 0.25],
            22,
        )
        text(s, 0.9, 5.05, 11.5, 0.72, "P(spam | free) =811 /1,388 =58.43%", 34, TEAL, True)
        text(
            s, 0.9, 6.1, 11.5, 0.45, "Document presence counts each word once per email.", 20, MUTED
        )
    elif layout == "distributions":
        panel(
            s,
            0.78,
            1.92,
            5.75,
            3.86,
            "Bernoulli",
            "Absent0 · present1\n\nMean=p\nVariance=p(1−p)",
            TEAL,
        )
        panel(
            s,
            6.80,
            1.92,
            5.75,
            3.86,
            "Binomial",
            "P(K=k)=C(n,k)p^k(1−p)^(n−k)\n\nExactly k in n trials\nIndependent, constant-p model",
        )
        text(
            s,
            0.91,
            6.1,
            11.5,
            0.55,
            "Synthetic p=.25,n=10,k=1 →18.77% · actual free p gives≈20.81%",
            19,
            MUTED,
        )
    elif layout == "inference":
        panel(
            s,
            0.8,
            1.95,
            5.78,
            3.95,
            "Word / class association",
            "χ²=703.783 · df=1\np≈4.4991e-155\n\nEvery expected cell≥5\nNo Yates correction",
        )
        panel(
            s,
            6.82,
            1.95,
            5.72,
            3.95,
            "Spam-proportion interval",
            "1,755 /5,862 =29.94%\n\nWilson95%\n28.78% to31.12%",
            TEAL,
        )
        text(
            s,
            0.91,
            6.18,
            11.5,
            0.45,
            "Association is not causation. Historical selection is not modern prevalence.",
            20,
            MUTED,
        )
    elif layout == "models":
        panel(
            s,
            0.8,
            1.94,
            5.77,
            4.55,
            "Multinomial",
            "Input: token counts\n\nRepeated words repeat evidence\n\nClass prior +count-weighted\nlog likelihood",
        )
        panel(
            s,
            6.82,
            1.94,
            5.73,
            4.55,
            "Bernoulli",
            "Input: binary presence\n\nAbsence contributes too\n\nClass prior +present terms\n+all absent-feature terms",
            TEAL,
        )
    elif layout == "explanations":
        names = [
            "Class\nprior",
            "Top present\nterms",
            "Other present\nremainder",
            "Absent-feature\naggregate",
        ]
        for i, name in enumerate(names):
            x = 0.82 + i * 3.12
            box(s, x, 2.24, 2.78, 1.42, WHITE, LINE)
            text(s, x + 0.13, 2.48, 2.52, 0.9, name, 22, NAVY, True, PP_ALIGN.CENTER)
            if i < 3:
                text(s, x + 2.84, 2.59, 0.35, 0.5, "+", 24, TEAL, True)
        text(s, 0.95, 4.22, 11.4, 0.75, "= full signed log posterior odds", 34, TEAL, True)
        text(
            s,
            0.95,
            5.45,
            11.4,
            0.8,
            "Not probability percentages or causal effects.\nBernoulli includes every absent fitted feature.",
            23,
        )
    elif layout == "metrics":
        rows = []
        for key, label in [
            ("accuracy", "Accuracy"),
            ("precision", "Precision"),
            ("recall", "Recall"),
            ("f1", "F1"),
            ("false_positive_rate", "FPR"),
        ]:
            rows.append(
                [
                    label,
                    *[f"{E['models'][m][key] * 100:.2f}%" for m in ("multinomial", "bernoulli")],
                ]
            )
        table(
            s,
            0.85,
            1.9,
            11.65,
            3.98,
            ["Metric", "Multinomial", "Bernoulli"],
            rows,
            [0.40, 0.30, 0.30],
            24,
        )
        text(
            s,
            0.95,
            6.15,
            11.2,
            0.45,
            "Same1,173 held-out emails · different denominators for each measure",
            21,
            MUTED,
        )
    elif layout == "matrices":
        for j, (name, label) in enumerate(
            [("multinomial", "Multinomial"), ("bernoulli", "Bernoulli")]
        ):
            x = 0.82 + j * 6.11
            m = E["models"][name]["confusion_matrix"]
            text(s, x, 1.91, 5.6, 0.48, label, 26, NAVY, True)
            table(
                s,
                x,
                2.66,
                5.55,
                2.55,
                ["Actual ↓ /predicted →", "Ham", "Spam"],
                [
                    ["Ham", f"{m['tn']} TN", f"{m['fp']} FP"],
                    ["Spam", f"{m['fn']} FN", f"{m['tp']} TP"],
                ],
                [0.48, 0.26, 0.26],
                19,
            )
            text(
                s, x, 5.51, 5.55, 0.85, f"{m['fp']} false alarms\n{m['fn']} missed spam", 24, ORANGE
            )
    elif layout == "paired":
        table(
            s,
            0.85,
            1.95,
            7.45,
            2.65,
            ["", "M correct", "M wrong"],
            [["B correct", "1,092", "4"], ["B wrong", "59", "18"]],
            [0.36, 0.32, 0.32],
            24,
        )
        text(s, 8.95, 2.05, 3.5, 0.8, "59 vs4", 44, NAVY, True)
        text(s, 8.95, 3.15, 3.5, 1.25, "on63 discordant\nmessage pairs", 23)
        text(s, 0.95, 5.25, 11.3, 0.85, "Exact McNemar p≈1.3821e-13", 32, TEAL, True)
        text(
            s,
            0.95,
            6.2,
            11.3,
            0.4,
            "Exploratory secondary analysis; no new fitting or independent holdout.",
            19,
            MUTED,
        )
    elif layout == "intervals":
        for i, (key, label, lo, hi) in enumerate(
            [
                ("accuracy", "Accuracy", 0, 8),
                ("recall", "Spam recall", 0, 25),
                ("false_positive_rate", "False-positive rate", -1, 1),
            ]
        ):
            y = 2.12 + i * 1.36
            d = R["paired"]["bootstrap"]["differences"][key]
            est, l, u = (100 * d[k] for k in ("estimate", "lower", "upper"))
            text(s, 0.86, y, 3, 0.5, label, 23, NAVY, True)
            left, right = 4.05, 10.3

            def xpos(v):
                return left + (v - lo) / (hi - lo) * (right - left)

            line(s, left, y + 0.55, right - left, 0, LINE, 1.1)
            line(s, xpos(0), y + 0.14, 0, 0.8, MUTED, 0.9)
            line(s, xpos(l), y + 0.55, xpos(u) - xpos(l), 0, TEAL, 3)
            line(s, xpos(l), y + 0.41, 0, 0.28, TEAL, 1.5)
            line(s, xpos(u), y + 0.41, 0, 0.28, TEAL, 1.5)
            dot = s.shapes.add_shape(
                MSO_SHAPE.OVAL,
                Inches(xpos(est) - 0.065),
                Inches(y + 0.485),
                Inches(0.13),
                Inches(0.13),
            )
            dot.fill.solid()
            dot.fill.fore_color.rgb = rgb(NAVY)
            dot.line.fill.background()
            text(s, 10.65, y + 0.2, 1.9, 0.72, f"{est:.2f}\n[{l:.2f},{u:.2f}]", 19)
            text(
                s,
                left,
                y + 0.87,
                6.6,
                0.25,
                f"{lo:g} to{hi:g} percentage points · each row has its own scale",
                12,
                MUTED,
            )
        text(
            s,
            0.93,
            6.47,
            11.4,
            0.4,
            "Paired, class-stratified95% intervals; FPR includes zero.",
            20,
            MUTED,
        )
    elif layout == "effects":
        text(s, 0.9, 2.0, 5.7, 0.45, "ODDS RATIO", 16, MUTED, True)
        text(s, 0.87, 2.7, 5.7, 1.0, "5.26", 65, NAVY, True)
        text(s, 0.95, 4.0, 5.6, 0.8, "95% interval [4.62,5.98]\nφ=.346", 25, TEAL)
        panel(
            s,
            7,
            1.98,
            5.55,
            3.95,
            "Empirical posterior",
            "Word present:58.43%\n\nWord absent:21.10%\n\nAn odds ratio is not a\nprobability ratio.",
        )
        text(
            s,
            0.95,
            6.2,
            11.4,
            0.4,
            "Known teaching token · all-record scope · association, not causation",
            20,
            MUTED,
        )
    elif layout == "cost":
        data = XyChartData()
        for name, m in [
            ("Multinomial", E["models"]["multinomial"]["confusion_matrix"]),
            ("Bernoulli", E["models"]["bernoulli"]["confusion_matrix"]),
        ]:
            ser = data.add_series(name)
            for cost in (0, 10, 56, 100):
                ser.add_data_point(cost, m["fp"] * cost + m["fn"])
        chart = s.shapes.add_chart(
            XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS,
            Inches(0.8),
            Inches(1.9),
            Inches(8.0),
            Inches(4.75),
            data,
        ).chart
        chart.has_legend = True
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(14)
        for axis in (chart.category_axis, chart.value_axis):
            axis.tick_labels.font.size = Pt(13)
            axis.has_title = True
        chart.category_axis.axis_title.text_frame.text = (
            "λ: false-positive cost (missed-spam units)"
        )
        chart.value_axis.axis_title.text_frame.text = "Observed total loss (cost units)"
        for series, color in zip(chart.series, (NAVY, TEAL), strict=True):
            series.format.line.color.rgb = rgb(color)
            series.format.line.width = Pt(2.3)
        text(
            s,
            9.20,
            2.15,
            3.2,
            2.95,
            "L(M) =8λ+14\nL(B) =7λ+70\n\nTie at λ=56\nLoss=462",
            25,
            NAVY,
            True,
        )
        text(s, 9.2, 5.50, 3.2, 0.8, "A sensitivity check,\nnot an operating policy.", 19, MUTED)
    elif layout == "demo":
        actions = [
            "Ready",
            "Explore data",
            "Count free",
            "Distributions",
            "Test /interval",
            "Predict /explain",
            "Read errors",
            "Validate /recover",
        ]
        for i, label in enumerate(actions):
            x = 0.85 + (i % 4) * 3.1
            y = 2.1 + (i // 4) * 1.95
            box(s, x, y, 2.85, 1.55, WHITE, LINE)
            text(s, x + 0.15, y + 0.15, 2.5, 0.42, f"{i + 1:02}", 23, TEAL, True)
            text(s, x + 0.15, y + 0.78, 2.5, 0.6, label, 22, NAVY, True)
        text(
            s,
            0.95,
            6.42,
            11.4,
            0.35,
            "Use labeled synthetic text; stop only processes you own.",
            20,
            MUTED,
        )
    elif layout == "tests":
        for i, (number, label) in enumerate(
            [
                ("413", "release Python tests"),
                ("+5", "paper analysis tests"),
                ("418", "combined recorded total"),
            ]
        ):
            x = 0.87 + i * 4.19
            box(s, x, 2.07, 3.7, 2.2, WHITE, LINE)
            text(s, x + 0.13, 2.43, 3.44, 0.78, number, 49, NAVY, True, PP_ALIGN.CENTER)
            text(s, x + 0.13, 3.47, 3.44, 0.52, label, 19, MUTED, align=PP_ALIGN.CENTER)
        text(
            s,
            0.95,
            4.88,
            11.3,
            1.05,
            "8 frontend tests · six browser routes · actual failure recovery\nKnown-answer math · hashes /split isolation · independent refits",
            23,
        )
        text(
            s,
            0.95,
            6.2,
            11.3,
            0.42,
            "Recorded evidence from Nov19/22,2026; no new app test run claimed.",
            18,
            MUTED,
        )
    elif layout in ("privacy", "limits"):
        bullets(s, body, 0.87, 1.98, 11.6, 4.65, 25 if layout == "privacy" else 23)
    elif layout == "timing":
        table(
            s,
            0.87,
            2.0,
            11.6,
            2.25,
            ["Warm request", "Measured p95", "Target"],
            [["Dual prediction", "0.0658s", "≤3s"], ["Cached summary", "0.0453s", "≤5s"]],
            [0.47, 0.28, 0.25],
            25,
        )
        text(
            s,
            0.97,
            4.9,
            11.2,
            1.3,
            "3 warmups +30 sequential requests · nearest-rank p95\n100-character synthetic input · i5-13420H · Linux\nCold startup, concurrency and maximum-length latency unmeasured.",
            22,
            MUTED,
        )
    elif layout == "closing":
        text(s, 0.82, 0.76, 11.8, 0.4, "THE PROJECT IN THREE IDEAS", 15, "B9CDE2", True)
        text(
            s,
            0.8,
            1.6,
            11.8,
            1.6,
            "Count clearly. Compare fairly.\nExplain uncertainty.",
            43,
            WHITE,
            True,
        )
        bullets(s, body[:3], 0.88, 3.7, 11.5, 2.1, 24, WHITE)
        box(s, 0.78, 6.18, 11.7, 0.55, WHITE)
        link = text(s, 0.9, 6.38, 11.3, 0.4, "github.com/hixam001/mail-sense", 21, "D7E5F3")
        link.text_frame.paragraphs[0].runs[0].hyperlink.address = item["url"]
        link.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb("D7E5F3")
        link.text_frame.paragraphs[0].runs[0].font.underline = False
    elif layout == "references":
        labels = [
            "Sahami et al. (1998)\nBayesian junk-mail filtering",
            "McCallum & Nigam (1998)\nBernoulli / Multinomial event models",
            "Metsis et al. (2006)\nWhich Naive Bayes for spam?",
            "MailSense project (2026)\nSource, data provenance and paper",
            "Dietterich (1998)\nStatistical tests for classifier comparisons",
            "Wilson (1927)\nScore-based proportion intervals",
            "Efron (1979)\nNonparametric bootstrap",
            "Apache SpamAssassin\nCorpus README and revision history",
            "scikit-learn 1.9.1\nNaive Bayes implementation reference",
            "NIST Dataplot\nLog-odds inference and confidence limits",
        ]
        for i, (r, label) in enumerate(zip(REFS, labels, strict=True)):
            x = 0.82 + (i // 5) * 6.12
            y = 1.9 + (i % 5) * 0.93
            shape = text(s, x, y, 5.7, 0.83, f"[{r['id']}] {label}", 17)
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    run.hyperlink.address = r["url"]
                    run.font.color.rgb = rgb(NAVY)
                    run.font.underline = False
    elif layout == "api":
        groups = [
            ("Readiness /data", "GET health\nGET dataset/{summary,statistics,distributions}"),
            (
                "Probability /inference",
                "GET probability/{word,distributions}\nPOST statistics/hypothesis-test\nGET statistics/confidence-interval",
            ),
            ("Models", "POST predict\nGET models/{metrics,comparison,explanations}"),
        ]
        for i, (title, detail) in enumerate(groups):
            y = 1.90 + i * 1.48
            box(s, 0.85, y, 11.6, 1.25, WHITE, LINE)
            text(s, 1.05, y + 0.18, 3.0, 0.8, title, 22, NAVY, True)
            text(s, 4.2, y + 0.15, 7.95, 0.98, detail, 18)
        text(
            s,
            0.97,
            6.56,
            11.2,
            0.3,
            "All paths start /api/v1; preparation and training have no HTTP endpoint.",
            17,
            MUTED,
        )
    elif layout == "commands":
        blocks = [
            (
                "INSTALL",
                "python3 scripts/node.py install\npython3 scripts/node.py npm --prefix frontend ci\nuv sync --project backend --frozen",
            ),
            (
                "RUN IN TWO TERMINALS",
                "uv run --directory backend --frozen python -m scripts.serve\npython3 scripts/node.py npm --prefix frontend run dev",
            ),
            (
                "RESEARCH CHECK",
                "uv run --directory backend --frozen python -m scripts.analyze_paper verify",
            ),
        ]
        for i, (title, code) in enumerate(blocks):
            y = 1.91 + i * 1.48
            box(s, 0.86, y, 11.6, 1.23, WHITE, LINE)
            text(s, 1.06, y + 0.15, 2.8, 0.9, title, 18, NAVY, True)
            text(s, 4.05, y + 0.15, 8.10, 0.98, code, 15)
        text(
            s,
            0.98,
            6.55,
            11.3,
            0.3,
            "Prepare corpus and frozen models first; exact sequence is in README /SETUP.",
            17,
            MUTED,
        )
    else:
        raise ValueError(layout)
    return s


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333333)
    prs.slide_height = Inches(7.5)
    prs.core_properties.title = "MailSense: Project Presentation"
    prs.core_properties.author = ""
    prs.core_properties.last_modified_by = ""
    prs.core_properties.comments = ""
    for i, item in enumerate(CONTENT["slides"], 1):
        draw(prs, i, item)
    output = HERE / "MailSense_Project_Presentation.pptx"
    prs.save(output)
    notes = [
        "# MailSense presenter notes",
        "Suggested main talk: approximately 20 minutes plus the guided demo. Timing is a delivery suggestion.",
    ]
    for i, s in enumerate(CONTENT["slides"], 1):
        notes += [
            f"\n## Slide{i:02}: {s['title']}",
            s["notes"],
            "Sources: " + ", ".join(s["sources"]),
        ]
    (HERE / "presenter_notes.md").write_text("\n\n".join(notes) + "\n")
    print(f"Created {len(prs.slides)} editable slides with speaker notes: {output}")


if __name__ == "__main__":
    main()
