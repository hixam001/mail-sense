"""Verified stratified membership over frozen retained records; no fitted features."""

import hashlib
import json
import platform
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import sklearn
from sklearn.model_selection import train_test_split

from app.services.corpus_dataset import DATASET_FILE, DATASET_REPORT_FILE, load_dataset
from app.services.corpus_ingest import publish_artifacts
from app.services.corpus_sources import corpus_lock

SPLIT_FILE = "data/processed/split_manifest.json"
SPLIT_VERSION = "stratified-v1"
SEED = 42
TEST_FRACTION = 0.2
MAX_MANIFEST_BYTES = 16 * 1024 * 1024


class SplitError(ValueError):
    """Fixed public failure code, excluding message content and member filenames."""


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _file_info(path):
    with path.open("rb") as stream:
        return {
            "sha256": hashlib.file_digest(stream, "sha256").hexdigest(),
            "size_bytes": path.stat().st_size,
        }


def _path(root):
    root = Path(root).resolve()
    path = root / SPLIT_FILE
    if not path.resolve().is_relative_to(root) or path.is_symlink() or path.is_dir():
        raise SplitError("invalid_split_path")
    return root, path


def _partition(rows):
    ordered = sorted(rows, key=lambda row: row["message_id"])
    ids = [row["message_id"] for row in ordered]
    if len(set(ids)) != len(ids):
        raise SplitError("duplicate_split_input_id")
    labels = [row["label"] for row in ordered]
    counts = Counter(labels)
    if set(counts) != {"ham", "spam"} or min(counts.values()) < 2:
        raise SplitError("insufficient_class_support")
    try:
        train, test = train_test_split(
            ids,
            test_size=TEST_FRACTION,
            random_state=SEED,
            stratify=labels,
            shuffle=True,
        )
    except ValueError as error:
        raise SplitError("insufficient_class_support") from error
    by_id = dict(zip(ids, labels, strict=True))
    if any({by_id[item] for item in subset} != {"ham", "spam"} for subset in (train, test)):
        raise SplitError("insufficient_class_support")
    return sorted(train), sorted(test)


def _membership_hash(ids):
    return hashlib.sha256("".join(identifier + "\n" for identifier in ids).encode()).hexdigest()


def _expected(root):
    rows, dataset = load_dataset(root)
    train, test = _partition(rows)
    by_id = {row["message_id"]: row["label"] for row in rows}
    configuration = {
        "schema_version": 1,
        "split_version": SPLIT_VERSION,
        "dataset_id": dataset["dataset_id"],
        "seed": SEED,
        "train_fraction": 1 - TEST_FRACTION,
        "test_fraction": TEST_FRACTION,
        "stratified_by": "label",
        "shuffle": True,
        "canonical_order": "message_id",
        "algorithm": "sklearn.model_selection.train_test_split",
        "rounding_policy": "ceil_test_size_complement_train",
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "preprocessing_version": dataset["preprocessing_version"],
        "tokenizer": dataset["tokenizer"],
    }
    membership = {"train_ids": train, "test_ids": test}
    manifest = {
        **configuration,
        **membership,
        "split_id": hashlib.sha256(_canonical_json({**configuration, **membership})).hexdigest(),
        "inputs": {
            **dataset["inputs"],
            **{name: _file_info(root / name) for name in (DATASET_FILE, DATASET_REPORT_FILE)},
        },
        "total_records": len(rows),
        "train_records": len(train),
        "test_records": len(test),
        "total_counts": dataset["class_counts"],
        "train_counts": {
            label: sum(by_id[item] == label for item in train) for label in ("ham", "spam")
        },
        "test_counts": {
            label: sum(by_id[item] == label for item in test) for label in ("ham", "spam")
        },
        "train_ids_sha256": _membership_hash(train),
        "test_ids_sha256": _membership_hash(test),
    }
    return rows, manifest


def prepare_split(root):
    root, path = _path(root)
    with corpus_lock(root / "data/raw"):
        _, manifest = _expected(root)
        data = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        if len(data) > MAX_MANIFEST_BYTES:
            raise SplitError("split_manifest_limit")
        with tempfile.TemporaryDirectory(prefix=".split-", dir=root / "data/raw") as temporary:
            staging = Path(temporary)
            output = staging / "split_manifest.json"
            output.write_bytes(data)
            if any(_file_info(root / name) != info for name, info in manifest["inputs"].items()):
                raise SplitError("split_input_changed")
            return publish_artifacts([(output, path)], staging, lambda: verify_split(root))


def _verified(root):
    root, path = _path(root)
    rows, expected = _expected(root)
    with path.open("rb") as stream:
        data = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(data) > MAX_MANIFEST_BYTES:
        raise SplitError("split_manifest_limit")
    if _canonical_json(json.loads(data)) != _canonical_json(expected):
        raise SplitError("split_manifest_mismatch")
    return rows, expected


def verify_split(root):
    return _verified(root)[1]


def load_split_dataset(root, scope="all"):
    """Join verified membership by ID; return fresh private rows and the manifest."""
    if scope not in {"all", "train", "test"}:
        raise SplitError("invalid_split_scope")
    rows, manifest = _verified(root)
    test_ids = set(manifest["test_ids"])
    joined = [
        {**row, "split": "test" if row["message_id"] in test_ids else "train"} for row in rows
    ]
    return [row for row in joined if scope == "all" or row["split"] == scope], manifest
