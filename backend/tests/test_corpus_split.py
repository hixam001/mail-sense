"""Known split allocations, artifact integrity and synthetic end-to-end isolation."""

import hashlib
import json
import math
import random
import sys
from pathlib import Path

import pytest
from test_corpus_dataset import INPUTS, OUTPUTS, mail, prepare, snapshot

from app.services import corpus_dataset as dataset
from app.services import corpus_split as split
from scripts import split_dataset as cli


@pytest.fixture
def corpus(tmp_path):
    groups = ("easy_ham", "easy_ham_2", "hard_ham", "spam", "spam_2")
    messages = {group: [mail(f"{group} {index}") for index in range(7)] for group in groups}
    messages["easy_ham"].append(mail("easy_ham 0"))
    messages["hard_ham"].extend([mail("easy_ham 0"), mail("conflict")])
    messages["spam"].append(mail("conflict"))
    root = prepare(tmp_path, messages)
    dataset.prepare_dataset(root)
    return root


def rows(ham, spam):
    return [
        {"message_id": f"{i:064x}", "label": "ham" if i < ham else "spam"}
        for i in range(ham + spam)
    ]


@pytest.mark.parametrize(
    "ham,spam,train_counts,test_counts",
    [
        (20, 10, {"ham": 16, "spam": 8}, {"ham": 4, "spam": 2}),
        (6, 5, {"ham": 4, "spam": 4}, {"ham": 2, "spam": 1}),
        (3, 3, {"ham": 2, "spam": 2}, {"ham": 1, "spam": 1}),
    ],
)
def test_known_allocations_rounding_and_order_independence(ham, spam, train_counts, test_counts):
    data = rows(ham, spam)
    train, test = split._partition(data)
    assert len(test) == math.ceil(len(data) * 0.2)
    assert len(train) + len(test) == len(data)
    assert set(train).isdisjoint(test)
    assert set(train) | set(test) == {row["message_id"] for row in data}
    labels = {row["message_id"]: row["label"] for row in data}
    assert {label: sum(labels[i] == label for i in train) for label in ("ham", "spam")} == (
        train_counts
    )
    assert {label: sum(labels[i] == label for i in test) for label in ("ham", "spam")} == (
        test_counts
    )
    random.Random(93).shuffle(data)
    assert (train, test) == split._partition(data)


@pytest.mark.parametrize(
    "ham,spam", [(0, 0), (10, 0), (0, 10), (9, 1), (2, 2), (3, 2), (8, 2), (2, 8)]
)
def test_insufficient_class_support_is_rejected_instead_of_rebalanced(ham, spam):
    with pytest.raises(split.SplitError, match="insufficient_class_support"):
        split._partition(rows(ham, spam))


def test_duplicate_ids_are_rejected():
    data = rows(10, 10)
    data[1]["message_id"] = data[0]["message_id"]
    with pytest.raises(split.SplitError, match="duplicate_split_input_id"):
        split._partition(data)


def test_t02_end_to_end_duplicate_conflict_removal_split_isolation_and_repeatability(corpus):
    original = snapshot(corpus, INPUTS + OUTPUTS)
    records, report = dataset.load_dataset(corpus)
    assert report["retained_records"] == 35
    assert report["duplicate_records_excluded"] == report["conflicting_records_excluded"] == 2
    manifest = split.prepare_split(corpus)
    assert (manifest["train_records"], manifest["test_records"]) == (28, 7)
    assert manifest["train_counts"] == {"ham": 17, "spam": 11}
    assert manifest["test_counts"] == {"ham": 4, "spam": 3}
    assert manifest["dataset_id"] == report["dataset_id"]
    train, test = set(manifest["train_ids"]), set(manifest["test_ids"])
    assert len(train) == len(manifest["train_ids"]) and len(test) == len(manifest["test_ids"])
    assert train.isdisjoint(test)
    assert train | test == {row["message_id"] for row in records}
    excluded = {row["message_id"] for row in report["exclusions"]}
    assert excluded.isdisjoint(train | test)
    hashes = {row["message_id"]: row["content_sha256"] for row in records}
    assert {hashes[i] for i in train}.isdisjoint(hashes[i] for i in test)
    output = (corpus / split.SPLIT_FILE).read_bytes()
    assert split.prepare_split(corpus) == manifest
    assert (corpus / split.SPLIT_FILE).read_bytes() == output
    assert split.verify_split(corpus) == manifest
    assert snapshot(corpus, INPUTS + OUTPUTS) == original
    for subset in ("train", "test"):
        ids = manifest[f"{subset}_ids"]
        assert ids == sorted(ids)
        assert (
            hashlib.sha256("".join(i + "\n" for i in ids).encode()).hexdigest()
            == (manifest[f"{subset}_ids_sha256"])
        )


def test_joined_scope_records_are_typed_independent_and_leave_frozen_csv_unchanged(corpus):
    split.prepare_split(corpus)
    original = snapshot(corpus, INPUTS + OUTPUTS)
    all_rows, manifest = split.load_split_dataset(corpus)
    train, _ = split.load_split_dataset(corpus, "train")
    test, _ = split.load_split_dataset(corpus, "test")
    assert {row["message_id"] for row in train} == set(manifest["train_ids"])
    assert {row["message_id"] for row in test} == set(manifest["test_ids"])
    assert len(all_rows) == len(train) + len(test)
    assert all(row["split"] == "train" for row in train)
    assert all(row["split"] == "test" for row in test)
    assert all(type(row["token_count"]) is int for row in all_rows)
    all_rows[0]["parse_warnings"].append("caller_mutation")
    all_rows[0]["model_text"] = "changed by caller"
    fresh, _ = split.load_split_dataset(corpus)
    assert "caller_mutation" not in fresh[0]["parse_warnings"]
    assert fresh[0]["model_text"] != "changed by caller"
    assert snapshot(corpus, INPUTS + OUTPUTS) == original
    with pytest.raises(split.SplitError, match="invalid_split_scope"):
        split.load_split_dataset(corpus, "validation")


@pytest.mark.parametrize(
    "change",
    [
        "overlap",
        "missing",
        "unknown",
        "order",
        "counts",
        "hash",
        "seed",
        "runtime",
        "dataset",
        "extra",
        "bool",
    ],
)
def test_changed_membership_or_configuration_fails_full_rederivation(corpus, change):
    split.prepare_split(corpus)
    path = corpus / split.SPLIT_FILE
    manifest = json.loads(path.read_text())
    if change == "overlap":
        manifest["test_ids"][0] = manifest["train_ids"][0]
    elif change == "missing":
        manifest["test_ids"].pop()
    elif change == "unknown":
        manifest["train_ids"][0] = "0" * 64
    elif change == "order":
        manifest["train_ids"].reverse()
    elif change == "counts":
        manifest["train_counts"]["ham"] += 1
    elif change == "hash":
        manifest["test_ids_sha256"] = "0" * 64
    elif change == "seed":
        manifest["seed"] = 7
    elif change == "runtime":
        manifest["runtime"]["scikit_learn"] = "different"
    elif change == "dataset":
        manifest["dataset_id"] = "0" * 64
    elif change == "extra":
        manifest["subject_text"] = "private"
    else:
        manifest["schema_version"] = True
    path.write_text(json.dumps(manifest))
    with pytest.raises(split.SplitError, match="split_manifest_mismatch"):
        split.verify_split(corpus)


def test_recomputed_id_hashes_cannot_hide_swapped_membership(corpus):
    split.prepare_split(corpus)
    path = corpus / split.SPLIT_FILE
    manifest = json.loads(path.read_text())
    manifest["train_ids"][0], manifest["test_ids"][0] = (
        manifest["test_ids"][0],
        manifest["train_ids"][0],
    )
    for subset in ("train", "test"):
        manifest[f"{subset}_ids"].sort()
        manifest[f"{subset}_ids_sha256"] = split._membership_hash(manifest[f"{subset}_ids"])
    path.write_text(json.dumps(manifest))
    with pytest.raises(split.SplitError, match="split_manifest_mismatch"):
        split.verify_split(corpus)


@pytest.mark.parametrize("name", INPUTS + OUTPUTS + (split.SPLIT_FILE,))
def test_missing_artifact_prevents_verified_split_loading(corpus, name):
    split.prepare_split(corpus)
    (corpus / name).unlink()
    with pytest.raises((OSError, ValueError)):
        split.load_split_dataset(corpus)


def test_changed_upstream_bytes_or_provenance_leave_previous_split_intact(corpus):
    split.prepare_split(corpus)
    previous = (corpus / split.SPLIT_FILE).read_bytes()
    path = corpus / dataset.DATASET_FILE
    with path.open("ab") as output:
        output.write(b"tampered")
    with pytest.raises(dataset.DatasetError):
        split.prepare_split(corpus)
    assert (corpus / split.SPLIT_FILE).read_bytes() == previous


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("when", ["replace", "validation"])
def test_publication_failure_preserves_prior_split_or_leaves_no_artifact(
    corpus,
    monkeypatch,
    existing,
    when,
):
    path = corpus / split.SPLIT_FILE
    if existing:
        split.prepare_split(corpus)
    previous = path.read_bytes() if existing else None
    replace_path, failed = Path.replace, False

    def fail_once(self, target):
        nonlocal failed
        if not failed and self.name == "split_manifest.json" and ".split-" in str(self):
            failed = True
            raise OSError("synthetic publication failure")
        return replace_path(self, target)

    def invalid(*args):
        raise split.SplitError("synthetic_validation_failure")

    if when == "replace":
        monkeypatch.setattr(Path, "replace", fail_once)
    else:
        monkeypatch.setattr(split, "verify_split", invalid)
    with pytest.raises((OSError, split.SplitError)):
        split.prepare_split(corpus)
    assert (path.read_bytes() if path.exists() else None) == previous
    assert not list((corpus / "data/raw").glob(".split-*"))
    assert not (corpus / "data/raw/.acquisition.lock").exists()


def test_manifest_limits_lock_and_symlink_guards(corpus, monkeypatch):
    split.prepare_split(corpus)
    path = corpus / split.SPLIT_FILE
    previous = path.read_bytes()
    monkeypatch.setattr(split, "MAX_MANIFEST_BYTES", 10)
    for operation in (split.prepare_split, split.verify_split):
        with pytest.raises(split.SplitError, match="split_manifest_limit"):
            operation(corpus)
    assert path.read_bytes() == previous
    (corpus / "data/raw/.acquisition.lock").touch()
    with pytest.raises(ValueError, match="lock exists"):
        split.prepare_split(corpus)
    (corpus / "data/raw/.acquisition.lock").unlink()
    path.unlink()
    target = corpus / "keep"
    target.write_text("keep")
    path.symlink_to(target)
    with pytest.raises(split.SplitError, match="invalid_split_path"):
        split.prepare_split(corpus)
    assert target.read_text() == "keep"


def test_split_cli_and_public_manifest_redact_message_data(corpus, monkeypatch, capsys):
    monkeypatch.setattr(cli, "ROOT", corpus)
    monkeypatch.setattr(sys, "argv", ["split_dataset", "run"])
    assert cli.main() == 0
    output = capsys.readouterr().out
    public = (corpus / split.SPLIT_FILE).read_text()
    for secret in ("private@example.invalid", "private-member-", "Fixture", "conflict"):
        assert secret not in output and secret not in public
    assert "28 train / 7 test" in output
    monkeypatch.setattr(sys, "argv", ["split_dataset", "verify"])
    assert cli.main() == 0
    capsys.readouterr()
    (corpus / split.SPLIT_FILE).write_text("invalid private JSON")
    assert cli.main() == 1
    assert capsys.readouterr().err == ("Split preparation failed: missing_or_invalid_artifacts\n")
