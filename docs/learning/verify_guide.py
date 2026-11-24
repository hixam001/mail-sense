"""Independently reconcile handbook navigation, facts, inventories and exports."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tomllib
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pymupdf
from docx import Document

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(value):
    return re.sub(
        r"\s+", "", unicodedata.normalize("NFKC", str(value)).replace("−", "-")
    )


def inventory_check(source):
    inventory = json.loads((HERE / "dependency_inventory.json").read_text())
    with (HERE / "dependency_inventory.csv").open(newline="") as handle:
        assert list(csv.DictReader(handle)) == inventory
    npm = json.loads((ROOT / "frontend/package-lock.json").read_text())["packages"]
    actual = {r["source"]: r for r in inventory if r["environment"] == "frontend-lock"}
    assert set(actual) == set(npm) - {""}
    for path, row in actual.items():
        item = npm[path]
        assert row["name"] == (item.get("name") or path.split("node_modules/")[-1])
        assert row["version"] == item["version"]
        assert row["status"] == ("dev" if item.get("dev") else "runtime") + (
            ";optional" if item.get("optional") else ""
        )
    lock = tomllib.loads((ROOT / "backend/uv.lock").read_text())
    expected = {
        (p["name"], p["version"]) for p in lock["package"] if "registry" in p["source"]
    }
    assert expected == {
        (r["name"], r["version"])
        for r in inventory
        if r["environment"] == "backend-lock"
    }
    for group, executable in (
        ("publication-tools", ".tools/learning-venv/bin/python"),
        ("graph-memory", "memory/.venv/bin/python"),
    ):
        command = "import importlib.metadata as m,json; print(json.dumps([(d.metadata['Name'],d.version) for d in m.distributions()]))"
        installed = json.loads(
            subprocess.check_output([str(ROOT / executable), "-c", command], text=True)
        )
        assert set(map(tuple, installed)) == {
            (r["name"], r["version"]) for r in inventory if r["environment"] == group
        }, group
    printed = [
        tuple(row)
        for page in source["pages"]
        for b in page["blocks"]
        if b["type"] == "table" and b["columns"][0] == "Package"
        for row in b["rows"]
    ]
    assert Counter(printed) == Counter(
        (r["name"], r["version"], r["status"]) for r in inventory
    )
    counts = Counter(r["environment"] for r in inventory)
    assert counts == {
        "backend-lock": 35,
        "frontend-lock": 213,
        "publication-tools": 17,
        "graph-memory": 31,
    }
    assert len(inventory) == source["inventory_rows"] == 296
    return dict(counts)


def facts_check(source):
    pages = {p["id"]: p for p in source["pages"]}
    evaluation = json.loads((ROOT / "artifacts/reports/evaluation.json").read_text())
    paper = json.loads((ROOT / "artifacts/reports/paper_statistics.json").read_text())
    stats = json.loads(
        (ROOT / "artifacts/reports/statistics_verification.json").read_text()
    )["measured"]["scopes"]["all"]
    table = next(b for b in pages["G09"]["blocks"] if b["type"] == "table")
    for row, key in zip(
        table["rows"],
        ("mean", "median", "q1", "q3", "sample_variance", "sample_std"),
        strict=True,
    ):
        for cell, label in zip(row[1:], ("ham", "spam"), strict=True):
            assert cell == f"{stats['token_statistics']['groups'][label][key]:,.3f}"
    table = next(b for b in pages["G11"]["blocks"] if b["type"] == "table")
    for row, label in zip(table["rows"][:2], ("spam", "ham"), strict=True):
        values = stats["free_word"]["counts"]
        assert [int(x.replace(",", "")) for x in row[1:]] == [
            values[label + "_present"],
            values[label + "_absent"],
            values[label + "_present"] + values[label + "_absent"],
        ]
    timing = json.loads((ROOT / "artifacts/reports/runtime_smoke.json").read_text())
    table = next(b for b in pages["G31"]["blocks"] if b["type"] == "table")
    for row, key in zip(table["rows"], ("prediction", "cached_summary"), strict=True):
        assert [float(c) for c in row[1:3]] == [
            round(timing[key][f], 6) for f in ("median_seconds", "p95_seconds")
        ]
    tables = [b for b in pages["G17"]["blocks"] if b["type"] == "table"]
    for ri, model in enumerate(("multinomial", "bernoulli")):
        result = evaluation["models"][model]
        assert list(map(int, tables[0]["rows"][ri][1:])) == [
            result["confusion_matrix"][k] for k in ("tn", "fp", "fn", "tp")
        ]
        for row, key in zip(
            tables[1]["rows"],
            ("accuracy", "precision", "recall", "f1", "false_positive_rate"),
            strict=True,
        ):
            assert row[ri + 2] == f"{100 * result[key]:.2f}%"
    tables = [b for b in pages["G18"]["blocks"] if b["type"] == "table"]
    assert [int(r[1].replace(",", "")) for r in tables[0]["rows"]] == [
        paper["paired"]["overall"][key]
        for key in ("both_correct", "multinomial_only", "bernoulli_only", "both_wrong")
    ]
    for row, key in zip(
        tables[1]["rows"], ("accuracy", "recall", "false_positive_rate"), strict=True
    ):
        values = paper["paired"]["bootstrap"]["differences"][key]
        assert row[1] == f"{100 * values['estimate']:.2f}"
        assert (
            compact(row[2])
            == f"[{100 * values['lower']:.2f},{100 * values['upper']:.2f}]"
        )
    table = next(b for b in pages["G19"]["blocks"] if b["type"] == "table")
    for cost, m, b in table["rows"]:
        expected = paper["cost_sensitivity"]["examples"][cost]
        assert [int(m), int(b)] == [expected["multinomial"], expected["bernoulli"]]
    schema = json.loads((HERE / "api_schema.json").read_text())
    observed = subprocess.check_output(
        [
            str(ROOT / "backend/.venv/bin/python"),
            "-c",
            "import json; from app.main import app; print(json.dumps(app.openapi(),sort_keys=True))",
        ],
        cwd=ROOT / "backend",
        text=True,
    )
    assert json.loads(observed) == schema, "OpenAPI snapshot drift"
    expected = {
        (method.upper(), path.removeprefix("/api/v1"))
        for path, spec in schema["paths"].items()
        if path.startswith("/api/v1/")
        for method in spec
    }
    table = next(b for b in pages["G24"]["blocks"] if b["type"] == "table")
    assert {tuple(r[0].split(" ", 1)) for r in table["rows"]} == expected and len(
        expected
    ) == 12
    plan = (ROOT / "docs/IMPLEMENTATION_PLAN.md").read_text()
    tickets = set(re.findall(r"^\| (MSE-\d+) \|", plan, re.M))
    included = {
        row[0]
        for page in source["pages"]
        for block in page["blocks"]
        if block["type"] == "table" and block["columns"][0] == "Ticket"
        for row in block["rows"]
    }
    assert included == tickets and len(tickets) == 42
    return len(expected), len(tickets)


def check():
    source = json.loads((HERE / "guide.json").read_text())
    counts = inventory_check(source)
    routes, tickets = facts_check(source)
    navigation = json.loads((HERE / "guide_navigation.json").read_text())
    doc = Document(HERE / "MailSense_Complete_Guide.docx")
    pdf = pymupdf.open(HERE / "MailSense_Complete_Guide.pdf")
    assert len(source["pages"]) == 55 and len(pdf) == 58
    assert not doc.core_properties.author and not doc.core_properties.last_modified_by
    assert (
        source["authors"] == 5
        and source["instructor_blank"]
        and not source["submission_date"]
    )
    text = pdf[0].get_text()
    assert all(re.search(rf"Author {i}:\s*_+", text) for i in range(1, 6))
    assert re.search(r"Instructor:\s*_+", text)
    assert "Submission" not in text and "Affiliation" not in text
    manuscript = (HERE / "MailSense_Complete_Guide.md").read_text()
    observations = []
    toc = pdf.get_toc()
    with ZipFile(HERE / "MailSense_Complete_Guide.docx") as archive:
        xml = ET.fromstring(archive.read("word/document.xml"))
        native = compact("".join(xml.itertext()))
        assert not xml.findall(".//w:ins", NS) and not xml.findall(".//w:del", NS)
        assert {
            x.attrib["{" + NS["w"] + "}name"]
            for x in xml.findall(".//w:bookmarkStart", NS)
        } == set(navigation)
        embedded = {
            sha_bytes(archive.read(n))
            for n in archive.namelist()
            if n.startswith("word/media/")
        }
    for index, chapter in enumerate(source["pages"], 4):
        page = pdf[index - 1]
        normalized = compact(page.get_text())
        assert navigation[chapter["id"]] == index
        assert compact(chapter["id"] + chapter["title"]) in normalized, (
            index,
            chapter["title"],
        )
        assert any(
            title.startswith(chapter["id"] + " ") and number == index
            for _, title, number in toc
        )
        assert all((ROOT / path).exists() for path in chapter["sources"]), chapter["id"]
        for block in chapter["blocks"]:
            if block["type"] == "table":
                items = [
                    str(c) for row in [block["columns"], *block["rows"]] for c in row
                ]
            elif block["type"] in ("steps", "bullets"):
                items = block["items"]
            elif block["type"] == "image":
                assert sha(ROOT / block["path"]) in embedded
                items = [block["caption"]]
            else:
                items = [block["text"]]
            for item in items:
                assert compact(item) in native, (chapter["id"], "DOCX", item[:70])
                assert compact(item) in normalized, (chapter["id"], "PDF", item[:100])
                assert item in manuscript or block["type"] == "table", (
                    chapter["id"],
                    "Markdown",
                )
        words = page.get_text("words")
        assert len(words) > 50
        assert "\ufffd" not in page.get_text()
        assert all(
            w[0] >= 20
            and w[2] <= page.rect.width - 20
            and w[1] >= 15
            and w[3] <= page.rect.height - 15
            for w in words
        ), index
        observations.append(
            {"chapter": chapter["id"], "page": index, "words": len(words)}
        )
    links = [
        x
        for p in (pdf[1], pdf[2])
        for x in p.get_links()
        if x["kind"] == pymupdf.LINK_GOTO
    ]
    assert len(links) == 55 and {x["page"] + 1 for x in links} == set(
        navigation.values()
    )
    for chapter in source["pages"]:
        # TOC labels and displayed numbers must agree with actual bookmark targets.
        text = compact(pdf[1].get_text() + pdf[2].get_text())
        assert (
            compact(chapter["id"] + chapter["title"] + str(navigation[chapter["id"]]))
            in text
        )
    captures = json.loads((HERE / "screenshots.json").read_text())
    assert (
        captures["routes"]
        == ["/", "/dataset", "/probability", "/statistics", "/detect", "/evaluation"]
        and captures["result"] == "pass"
    )
    assert embedded == {sha(p) for p in (HERE / "figures").glob("*.png")}
    reference_urls = {
        r["url"] for r in json.loads((ROOT / "docs/paper/references.json").read_text())
    }
    assert reference_urls <= {
        link.get("uri") for page in pdf for link in page.get_links()
    }
    for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", manuscript):
        if not target.startswith(("http", "#")):
            assert (HERE / target.split("#")[0]).exists(), (label, target)
    paths = [
        HERE / p
        for p in (
            "guide.json",
            "guide_navigation.json",
            "MailSense_Complete_Guide.docx",
            "MailSense_Complete_Guide.pdf",
            "MailSense_Complete_Guide.md",
            "dependency_inventory.csv",
            "dependency_inventory.json",
            "api_schema.json",
            "screenshots.json",
            "build_guide.py",
            "verify_guide.py",
            "capture_screens.py",
            "capture_screens.mjs",
            "requirements.txt",
        )
    ]
    paths += list((HERE / "figures").glob("*.png"))
    paths += [
        ROOT / p
        for p in (
            "frontend/package-lock.json",
            "backend/uv.lock",
            "docs/paper/references.json",
            "artifacts/reports/evaluation.json",
            "artifacts/reports/paper_statistics.json",
            "artifacts/reports/statistics_verification.json",
            "artifacts/reports/runtime_smoke.json",
        )
    ]
    return {
        "result": "pass",
        "task": "MSE-609",
        "scope": "Documentation exports, exact inventories/API snapshot, reconciled facts/navigation, original screenshot bytes and current six-screen capture only. Application suites and performance were not rerun.",
        "pages": len(pdf),
        "chapters": len(source["pages"]),
        "api_routes": routes,
        "delivery_tickets": tickets,
        "inventory": counts,
        "screenshots": captures,
        "observations": observations,
        "sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
    }


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    result = check()
    receipt = ROOT / "artifacts/reports/platform_guide.json"
    if args.record:
        result["verified_at"] = datetime.now(timezone.utc).isoformat()
        receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    else:
        previous = json.loads(receipt.read_text())
        assert {k: v for k, v in previous.items() if k != "verified_at"} == result, (
            "Receipt is stale"
        )
    print(
        "Guide: 58 pages, 55 chapters, 296 dependency entries, 12 API routes and 42 tickets reconciled."
    )
    print("VERDICT: PASS")


if __name__ == "__main__":
    main()
