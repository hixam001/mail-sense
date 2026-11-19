"""Synthetic end-to-end dataset fixtures and independent CSV/tokenizer checks."""

import csv
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest
from sklearn.feature_extraction.text import CountVectorizer

from app.services import corpus_dataset as dataset
from app.services import corpus_ingest as ingest
from app.services import corpus_sources as sources
from app.services.text_features import token_count, tokenize
from scripts import prepare_dataset as cli


def mail(body):
    return ("From: private@example.invalid\nSubject: Fixture\n\n" + body).encode()


def prepare(root, messages=None):
    messages = (
        messages
        if messages is not None
        else {
            "easy_ham": [mail("same ham"), mail("same ham"), mail("conflict")],
            "easy_ham_2": [mail("same ham"), mail("café été")],
            "hard_ham": [mail("unique ham"), mail("conflict")],
            "spam": [mail("same spam"), mail("conflict"), mail("conflict")],
            "spam_2": [mail("same spam"), mail("conflict"), mail("unique spam")],
        }
    )
    archives = {}
    for group, (filename, _) in sources.CANONICAL.items():
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:bz2") as archive:
            for index, content in enumerate(messages.get(group, [])):
                info = tarfile.TarInfo(f"{group}/private-member-{index}")
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
        archives[filename] = buffer.getvalue()

    class Response(io.BytesIO):
        status = 200

        def __init__(self, data):
            super().__init__(data)
            self.headers = {"Content-Length": str(len(data))}

    sources.download_sources(root, opener=lambda url: Response(archives[url.rsplit("/", 1)[-1]]))
    ingest.ingest_sources(root)
    return root


@pytest.fixture
def corpus(tmp_path):
    return prepare(tmp_path)


def parsed_rows(root):
    return [json.loads(line) for line in (root / ingest.RECORD_FILE).read_text().splitlines()]


def retained_rows(root):
    with (root / dataset.DATASET_FILE).open(newline="") as stream:
        return list(csv.DictReader(stream))


def snapshot(root, paths):
    return {name: (root / name).read_bytes() for name in paths}


INPUTS = (ingest.RECORD_FILE, ingest.REPORT_FILE, ingest.MANIFEST_FILE)
OUTPUTS = (dataset.DATASET_FILE, dataset.DATASET_REPORT_FILE)


def test_actual_archives_to_unique_records_conflicts_counts_and_complete_provenance(corpus):
    original = snapshot(corpus, INPUTS)
    report = dataset.prepare_dataset(corpus)
    assert (report["input_records"], report["retained_records"]) == (13, 5)
    assert (report["duplicate_records_excluded"], report["conflicting_records_excluded"]) == (3, 5)
    assert (report["duplicate_groups"], report["conflicting_groups"]) == (2, 1)
    assert report["input_class_counts"] == {"ham": 7, "spam": 6}
    assert report["class_counts"] == {"ham": 3, "spam": 2}
    retained, parsed = retained_rows(corpus), parsed_rows(corpus)
    assert len({row["model_text"] for row in retained}) == len(retained)
    assert [row["message_id"] for row in retained] == sorted(row["message_id"] for row in retained)
    analyzer = CountVectorizer().build_analyzer()  # Never fit a vocabulary.
    for row in retained:
        prior = next(p for p in parsed if p["message_id"] == row["message_id"])
        for key in ingest.RECORD_KEYS - {"parse_warnings", "character_count"}:
            assert row[key] == prior[key]
        assert json.loads(row["parse_warnings"]) == prior["parse_warnings"]
        assert int(row["character_count"]) == len(row["model_text"])
        assert int(row["token_count"]) == len(analyzer(row["model_text"]))
        assert "split" not in row
    for text in {row["model_text"] for row in parsed}:
        members = [row for row in parsed if row["model_text"] == text]
        selected = [row for row in retained if row["model_text"] == text]
        if len({row["label"] for row in members}) > 1:
            assert selected == []  # Includes all same-label repeats in a conflict group.
        else:
            assert selected[0]["message_id"] == min(row["message_id"] for row in members)
    retained_ids = {row["message_id"] for row in retained}
    excluded_ids = {row["message_id"] for row in report["exclusions"]}
    assert retained_ids.isdisjoint(excluded_ids)
    assert retained_ids | excluded_ids == {row["message_id"] for row in parsed}
    for item in report["exclusions"]:
        if item["reason"] == "duplicate":
            assert item["retained_message_id"] in retained_ids
        else:
            assert item["reason"] == "label_conflict" and item["retained_message_id"] is None
    for measured in report["sources"]:
        assert measured["input_records"] == sum(
            measured[k]
            for k in (
                "retained_records",
                "duplicate_records_excluded",
                "conflicting_records_excluded",
            )
        )
    assert snapshot(corpus, INPUTS) == original
    assert (corpus / dataset.DATASET_FILE).stat().st_mode & 0o777 == 0o600
    assert dataset.verify_dataset(corpus) == report


def test_repeat_runs_are_identical_and_offline(corpus, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Dataset preparation attempted network access")

    monkeypatch.setattr(sources, "_open_official", forbidden)
    first = dataset.prepare_dataset(corpus)
    output = snapshot(corpus, OUTPUTS)
    assert dataset.prepare_dataset(corpus) == first
    assert snapshot(corpus, OUTPUTS) == output
    assert not list((corpus / "data/raw").glob(".dataset-*"))
    assert not (corpus / "data/raw/.acquisition.lock").exists()


def test_selection_is_independent_of_input_order(corpus):
    rows = parsed_rows(corpus)
    assert dataset._deduplicate(rows) == dataset._deduplicate(list(reversed(rows)))
    first = dataset.prepare_dataset(corpus)
    original = snapshot(corpus, OUTPUTS)
    reversed_data = b"".join(
        (json.dumps(row, sort_keys=True) + "\n").encode() for row in reversed(rows)
    )
    (corpus / ingest.RECORD_FILE).write_bytes(reversed_data)
    report_path = corpus / ingest.REPORT_FILE
    report = json.loads(report_path.read_text())
    report.update(
        records_size_bytes=len(reversed_data),
        records_sha256=hashlib.sha256(reversed_data).hexdigest(),
    )
    report_path.write_text(json.dumps(report))
    second = dataset.prepare_dataset(corpus)
    assert first["dataset_id"] == second["dataset_id"]
    assert (corpus / dataset.DATASET_FILE).read_bytes() == original[dataset.DATASET_FILE]
    assert first["exclusions"] == second["exclusions"]
    assert first["inputs"] != second["inputs"]  # Report records the changed serialized input.


def test_hash_collision_fails_closed(corpus):
    rows = parsed_rows(corpus)[:2]
    rows[1] = {**rows[0], "model_text": "different text with a forged identical hash"}
    with pytest.raises(dataset.DatasetError, match="content_hash_collision"):
        dataset._deduplicate(rows)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", []),
        ("I a ! 7 _", []),
        ("FREE free Free", ["free", "free", "free"]),
        ("café ÉTÉ 中文 привет", ["café", "été", "中文", "привет"]),
        ("can't e-mail foo_bar 42", ["can", "mail", "foo_bar", "42"]),
        ("Straße STRASSE İSTANBUL", ["straße", "strasse", "stanbul"]),
    ],
)
def test_fixed_tokens_match_independent_sklearn_analyzer_without_fitting(text, expected):
    vectorizer = CountVectorizer()
    assert tokenize(text) == expected == vectorizer.build_analyzer()(text)
    assert token_count(text) == len(expected)
    assert not hasattr(vectorizer, "vocabulary_")


def test_normalization_dedup_is_exact_and_zero_token_records_are_retained(tmp_path):
    root = prepare(
        tmp_path,
        {
            "easy_ham": [
                mail("café"),
                mail("cafe\u0301"),
                mail("CAFÉ"),
                b"Subject: I\n\n!",
            ]
        },
    )
    report = dataset.prepare_dataset(root)
    rows = retained_rows(root)
    assert report["input_records"] == 4 and report["retained_records"] == 3
    assert report["duplicate_records_excluded"] == 1
    assert next(row for row in rows if row["model_text"] == "I\n!")["token_count"] == "0"


def test_no_parsed_rows_produces_header_only_csv_and_truthful_empty_summary(tmp_path):
    root = prepare(tmp_path, {"easy_ham": [b"\n\n"]})
    report = dataset.prepare_dataset(root)
    assert report["input_records"] == report["retained_records"] == 0
    assert report["parse_rejections"] == 1
    assert report["class_counts"] == {"ham": 0, "spam": 0}
    assert report["exclusions"] == retained_rows(root) == []
    assert dataset.verify_dataset(root) == report


@pytest.mark.parametrize("artifact", ["csv", "counts", "extra", "reason", "bool", "config"])
def test_verifier_rejects_corrupt_records_or_forged_report(corpus, artifact):
    dataset.prepare_dataset(corpus)
    path = corpus / dataset.DATASET_REPORT_FILE
    report = json.loads(path.read_text())
    if artifact == "csv":
        with (corpus / dataset.DATASET_FILE).open("ab") as stream:
            stream.write(b"tampered private@example.invalid")
    elif artifact == "counts":
        report["retained_records"] += 1
    elif artifact == "extra":
        report["subject_text"] = "private"
    elif artifact == "reason":
        report["exclusions"][0]["reason"] = "unknown"
    elif artifact == "bool":
        report["schema_version"] = True
    else:
        report["tokenizer"]["lowercase"] = False
    path.write_text(json.dumps(report))
    with pytest.raises(dataset.DatasetError):
        dataset.verify_dataset(corpus)


def test_self_consistent_tampered_output_hash_does_not_bypass_rederivation(corpus):
    dataset.prepare_dataset(corpus)
    data = (corpus / dataset.DATASET_FILE).read_bytes().replace(b"same ham", b"DIFF HAM")
    (corpus / dataset.DATASET_FILE).write_bytes(data)
    path = corpus / dataset.DATASET_REPORT_FILE
    report = json.loads(path.read_text())
    report.update(records_sha256=hashlib.sha256(data).hexdigest(), records_size_bytes=len(data))
    path.write_text(json.dumps(report))
    with pytest.raises(dataset.DatasetError, match="dataset_report_mismatch"):
        dataset.verify_dataset(corpus)


@pytest.mark.parametrize(
    "field,value",
    [
        ("label", "spam"),
        ("content_sha256", "0" * 64),
        ("model_text", ""),
    ],
)
def test_invalid_parse_inputs_fail_before_overwriting_previous_dataset(corpus, field, value):
    dataset.prepare_dataset(corpus)
    previous = snapshot(corpus, OUTPUTS)
    rows = parsed_rows(corpus)
    rows[0][field] = value
    data = "".join(json.dumps(row) + "\n" for row in rows).encode()
    (corpus / ingest.RECORD_FILE).write_bytes(data)
    path = corpus / ingest.REPORT_FILE
    report = json.loads(path.read_text())
    report.update(records_sha256=hashlib.sha256(data).hexdigest(), records_size_bytes=len(data))
    path.write_text(json.dumps(report))
    with pytest.raises(ingest.IngestionError):
        dataset.prepare_dataset(corpus)
    assert snapshot(corpus, OUTPUTS) == previous


@pytest.mark.parametrize("name", INPUTS + OUTPUTS)
def test_verification_fails_if_any_required_artifact_is_missing(corpus, name):
    dataset.prepare_dataset(corpus)
    (corpus / name).unlink()
    with pytest.raises((OSError, ValueError)):
        dataset.verify_dataset(corpus)


def test_changed_source_provenance_makes_retained_artifacts_stale(corpus):
    dataset.prepare_dataset(corpus)
    path = corpus / ingest.MANIFEST_FILE
    manifest = json.loads(path.read_text())
    manifest["archives"][0]["acquired_at"] = "2026-11-20T00:00:00Z"
    path.write_text(json.dumps(manifest))
    with pytest.raises(dataset.DatasetError, match="dataset_report_mismatch"):
        dataset.verify_dataset(corpus)


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("when", ["replace", "validation"])
def test_failed_publication_restores_previous_set_or_leaves_no_outputs(
    corpus,
    monkeypatch,
    existing,
    when,
):
    if existing:
        dataset.prepare_dataset(corpus)
    previous = snapshot(corpus, OUTPUTS) if existing else {}
    replace_path, failed = Path.replace, False

    def fail_once(self, target):
        nonlocal failed
        if not failed and self.name == "deduplication_report.json" and ".dataset-" in str(self):
            failed = True
            raise OSError("synthetic publication failure")
        return replace_path(self, target)

    def invalid(*args):
        raise dataset.DatasetError("synthetic_validation_failure")

    if when == "replace":
        monkeypatch.setattr(Path, "replace", fail_once)
    else:
        monkeypatch.setattr(dataset, "verify_dataset", invalid)
    with pytest.raises((OSError, dataset.DatasetError)):
        dataset.prepare_dataset(corpus)
    if existing:
        assert snapshot(corpus, OUTPUTS) == previous
    else:
        assert all(not (corpus / name).exists() for name in OUTPUTS)
    assert not list((corpus / "data/raw").glob(".dataset-*"))
    assert not (corpus / "data/raw/.acquisition.lock").exists()


def test_limits_and_lock_fail_without_replacing_outputs(corpus, monkeypatch):
    dataset.prepare_dataset(corpus)
    previous = snapshot(corpus, OUTPUTS)
    monkeypatch.setattr(dataset, "MAX_OUTPUT_BYTES", 16)
    with pytest.raises(dataset.DatasetError, match="dataset_output_limit"):
        dataset.prepare_dataset(corpus)
    assert snapshot(corpus, OUTPUTS) == previous
    (corpus / "data/raw/.acquisition.lock").touch()
    with pytest.raises(ValueError, match="lock exists"):
        dataset.prepare_dataset(corpus)
    assert snapshot(corpus, OUTPUTS) == previous


@pytest.mark.parametrize("name", OUTPUTS)
def test_symlink_outputs_are_rejected_without_touching_targets(corpus, name):
    target = corpus / "keep"
    target.write_text("keep")
    (corpus / name).symlink_to(target)
    with pytest.raises(dataset.DatasetError, match="invalid_dataset_path"):
        dataset.prepare_dataset(corpus)
    assert target.read_text() == "keep"


def test_public_report_and_cli_have_no_private_message_data(corpus, monkeypatch, capsys):
    monkeypatch.setattr(cli, "ROOT", corpus)
    monkeypatch.setattr(sys, "argv", ["prepare_dataset", "run"])
    assert cli.main() == 0
    output = capsys.readouterr().out
    report = (corpus / dataset.DATASET_REPORT_FILE).read_text()
    for secret in ("private@example.invalid", "private-member-", "Fixture", "same ham", "café"):
        assert secret not in output and secret not in report
    assert "5 retained / 13 parsed" in output and "3 ham / 2 spam" in output
    monkeypatch.setattr(sys, "argv", ["prepare_dataset", "verify"])
    (corpus / dataset.DATASET_REPORT_FILE).write_text("private malformed JSON")
    assert cli.main() == 1
    assert capsys.readouterr().err == ("Dataset preparation failed: missing_or_invalid_artifacts\n")
