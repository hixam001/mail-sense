"""Deterministic retained records and public provenance, before train/test splitting."""

import csv
import hashlib
import io
import json
import platform
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from app.services.corpus_ingest import (
    MANIFEST_FILE,
    RECORD_FILE,
    REPORT_FILE,
    publish_artifacts,
    verify_parsed_sources,
)
from app.services.corpus_sources import CANONICAL, corpus_lock
from app.services.mail_parser import DEFAULT_LIMITS, PREPROCESSING_VERSION
from app.services.text_features import token_count, tokenizer_config

DATASET_FILE = "data/processed/messages.csv"
DATASET_REPORT_FILE = "data/processed/deduplication_report.json"
DEDUPLICATION_VERSION = "exact-text-v1"
REPRESENTATIVE_POLICY = "smallest_message_id"
MAX_OUTPUT_BYTES = DEFAULT_LIMITS.output_bytes
CSV_FIELDS = (
    "message_id",
    "source_group",
    "source_archive",
    "source_file",
    "label",
    "subject_text",
    "body_text",
    "model_text",
    "character_count",
    "token_count",
    "content_sha256",
    "parse_warnings",
)


class DatasetError(ValueError):
    """Fixed failure code; never includes message content or member filenames."""


def _file_info(path):
    with path.open("rb") as stream:
        return {
            "sha256": hashlib.file_digest(stream, "sha256").hexdigest(),
            "size_bytes": path.stat().st_size,
        }


def _paths(root):
    root = Path(root).resolve()
    outputs = [root / name for name in (DATASET_FILE, DATASET_REPORT_FILE)]
    for path in outputs:
        if not path.resolve().is_relative_to(root) or path.is_symlink() or path.is_dir():
            raise DatasetError("invalid_dataset_path")
    return root, outputs


def _deduplicate(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["content_sha256"]].append(row)
    retained, exclusions = [], []
    duplicate_groups = conflicting_groups = 0
    for content_hash, members in sorted(groups.items()):
        if any(row["model_text"] != members[0]["model_text"] for row in members):
            raise DatasetError("content_hash_collision")
        ordered = sorted(members, key=lambda row: row["message_id"])
        conflict = len({row["label"] for row in members}) > 1
        if conflict:
            conflicting_groups += 1
            excluded, representative = ordered, None
        else:
            representative = ordered[0]
            retained.append(
                {**representative, "token_count": token_count(representative["model_text"])}
            )
            excluded = ordered[1:]
            duplicate_groups += bool(excluded)
        exclusions.extend(
            {
                "message_id": row["message_id"],
                "content_sha256": content_hash,
                "reason": "label_conflict" if conflict else "duplicate",
                "retained_message_id": None if conflict else representative["message_id"],
            }
            for row in excluded
        )
    return (
        sorted(retained, key=lambda row: row["message_id"]),
        sorted(exclusions, key=lambda row: row["message_id"]),
        duplicate_groups,
        conflicting_groups,
    )


def _csv_chunks(rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    yield buffer.getvalue().encode("utf-8")
    for row in rows:
        buffer.seek(0)
        buffer.truncate()
        values = {key: row[key] for key in CSV_FIELDS}
        values["parse_warnings"] = json.dumps(row["parse_warnings"], separators=(",", ":"))
        writer.writerow(values)
        yield buffer.getvalue().encode("utf-8")


def _measure_csv(rows, output=None):
    digest, size = hashlib.sha256(), 0
    for chunk in _csv_chunks(rows):
        size += len(chunk)
        if size > MAX_OUTPUT_BYTES:
            raise DatasetError("dataset_output_limit")
        digest.update(chunk)
        if output is not None:
            output.write(chunk)
    return {"sha256": digest.hexdigest(), "size_bytes": size}


def _expected(root):
    parsed = verify_parsed_sources(root)
    input_info = {
        name: _file_info(root / name) for name in (MANIFEST_FILE, REPORT_FILE, RECORD_FILE)
    }
    rows, digest, size = [], hashlib.sha256(), 0
    with (root / RECORD_FILE).open("rb") as stream:
        while line := stream.readline(8 * DEFAULT_LIMITS.text_characters + 4097):
            size += len(line)
            if size > DEFAULT_LIMITS.output_bytes or not line.endswith(b"\n"):
                raise DatasetError("invalid_dataset_input")
            digest.update(line)
            rows.append(json.loads(line))
    if (
        size != parsed["records_size_bytes"]
        or digest.hexdigest() != parsed["records_sha256"]
        or len(rows) != parsed["files_accepted"]
        or input_info[RECORD_FILE] != {"sha256": digest.hexdigest(), "size_bytes": size}
    ):
        raise DatasetError("dataset_input_changed")
    retained, exclusions, duplicate_groups, conflicting_groups = _deduplicate(rows)
    reasons = {item["message_id"]: item["reason"] for item in exclusions}
    source_counts = []
    for group, (archive, label) in CANONICAL.items():
        members = [row for row in rows if row["source_group"] == group]
        excluded = Counter(reasons.get(row["message_id"]) for row in members)
        source_counts.append(
            {
                "source_group": group,
                "archive_name": archive,
                "label": label,
                "input_records": len(members),
                "retained_records": excluded[None],
                "duplicate_records_excluded": excluded["duplicate"],
                "conflicting_records_excluded": excluded["label_conflict"],
            }
        )
    record_info = _measure_csv(retained)
    configuration = {
        "schema_version": 1,
        "preprocessing_version": PREPROCESSING_VERSION,
        "deduplication_version": DEDUPLICATION_VERSION,
        "representative_policy": REPRESENTATIVE_POLICY,
        "tokenizer": tokenizer_config(),
    }
    identity = json.dumps(
        {**configuration, "records_sha256": record_info["sha256"]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    totals = Counter(item["reason"] for item in exclusions)
    report = {
        **configuration,
        "stage": "retained_before_split",
        "python_version": platform.python_version(),
        "dataset_id": hashlib.sha256(identity).hexdigest(),
        "inputs": input_info,
        "records_file": DATASET_FILE,
        "records_sha256": record_info["sha256"],
        "records_size_bytes": record_info["size_bytes"],
        "input_records": len(rows),
        "retained_records": len(retained),
        "parse_rejections": parsed["files_rejected"],
        "duplicate_records_excluded": totals["duplicate"],
        "conflicting_records_excluded": totals["label_conflict"],
        "duplicate_groups": duplicate_groups,
        "conflicting_groups": conflicting_groups,
        "input_class_counts": {
            label: sum(row["label"] == label for row in rows) for label in ("ham", "spam")
        },
        "class_counts": {
            label: sum(row["label"] == label for row in retained) for label in ("ham", "spam")
        },
        "sources": source_counts,
        "exclusions": exclusions,
    }
    return retained, report


def prepare_dataset(root):
    root, (records_path, report_path) = _paths(root)
    with corpus_lock(root / "data/raw"):
        retained, report = _expected(root)
        with tempfile.TemporaryDirectory(prefix=".dataset-", dir=root / "data/raw") as temporary:
            staging = Path(temporary)
            records, metadata = staging / "messages.csv", staging / "deduplication_report.json"
            with records.open("xb") as output:
                records.chmod(0o600)
                if _measure_csv(retained, output) != {
                    "sha256": report["records_sha256"],
                    "size_bytes": report["records_size_bytes"],
                }:
                    raise DatasetError("dataset_output_changed")
            metadata.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            if any(_file_info(root / name) != info for name, info in report["inputs"].items()):
                raise DatasetError("dataset_input_changed")
            return publish_artifacts(
                [(records, records_path), (metadata, report_path)],
                staging,
                lambda: verify_dataset(root),
            )


def load_dataset(root):
    """Return typed canonical rows after rederiving and verifying their CSV/report."""
    root, (records_path, report_path) = _paths(root)
    retained, expected = _expected(root)
    actual = json.loads(report_path.read_text(encoding="utf-8"))
    # Compare canonical JSON as well as values: reject bool/int and extra fields.
    if json.dumps(actual, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise DatasetError("dataset_report_mismatch")
    if _file_info(records_path) != {
        "sha256": expected["records_sha256"],
        "size_bytes": expected["records_size_bytes"],
    }:
        raise DatasetError("dataset_records_mismatch")
    return retained, expected


def verify_dataset(root):
    return load_dataset(root)[1]
