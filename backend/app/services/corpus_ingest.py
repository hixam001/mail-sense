"""Bounded private extraction and deterministic pre-deduplication parse artifacts."""

import bz2
import hashlib
import json
import platform
import tarfile
import tempfile
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from app.services.corpus_sources import SourceArchive, SourceManifest, corpus_lock, verify_sources
from app.services.mail_parser import (
    DEFAULT_LIMITS,
    PREPROCESSING_VERSION,
    WARNING_CODES,
    MessageRejected,
    normalize_text,
    parse_message,
)

RECORD_FILE = "data/processed/messages.parsed.jsonl"
REPORT_FILE = "data/processed/parsing_report.json"
MANIFEST_FILE = "data/processed/source_manifest.json"
REJECTION_CODES = {
    "message_limit",
    "header_limit",
    "mime_parts_limit",
    "mime_depth_limit",
    "text_limit",
    "malformed_mime",
    "empty_text",
}
TOTAL_KEYS = {
    "files_seen",
    "files_accepted",
    "files_rejected",
    "metadata_files_ignored",
    "directories_ignored",
}
SOURCE_KEYS = TOTAL_KEYS | {
    "archive_name",
    "source_group",
    "label",
    "archive_sha256",
    "archive_members",
    "rejection_counts",
    "warning_counts",
    "rejections",
}
REPORT_KEYS = TOTAL_KEYS | {
    "schema_version",
    "stage",
    "preprocessing_version",
    "python_version",
    "limits",
    "records_file",
    "records_sha256",
    "records_size_bytes",
    "sources",
}
RECORD_KEYS = {
    "message_id",
    "source_group",
    "source_archive",
    "source_file",
    "label",
    "subject_text",
    "body_text",
    "model_text",
    "character_count",
    "content_sha256",
    "parse_warnings",
}


class IngestionError(ValueError):
    """Fixed public failure code, with no archive names or message content."""


class _BoundedReader:
    def __init__(self, stream, maximum):
        self.stream, self.maximum, self.used = stream, maximum, 0

    def read(self, size=-1):
        remaining = self.maximum - self.used
        data = self.stream.read(min(size, remaining + 1) if size >= 0 else remaining + 1)
        self.used += len(data)
        if self.used > self.maximum:
            raise IngestionError("archive_expansion_limit")
        return data


def safe_member_name(name, group):
    if not isinstance(name, str) or len(name) > 512:
        raise IngestionError("archive_path")
    if (
        "\\" in name
        or ":" in name
        or any(ord(c) < 32 or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in name)
    ):
        raise IngestionError("archive_path")
    parts = name.rstrip("/").split("/")
    if len(parts) > 8 or parts[0] != group or any(p in {"", ".", ".."} for p in parts):
        raise IngestionError("archive_path")
    return "/".join(parts)


def message_id(source, name):
    identity = f"{source.sha256}\0{source.source_group}\0{name}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _archive(path, source, staging, emit, limits):
    counts = dict(
        archive_name=source.archive_name,
        source_group=source.source_group,
        label=source.label,
        archive_sha256=source.sha256,
        archive_members=0,
        directories_ignored=0,
        metadata_files_ignored=0,
        files_seen=0,
        files_accepted=0,
        files_rejected=0,
    )
    rejections, warnings, diagnostics, seen = Counter(), Counter(), [], set()

    def reject(identifier, reason):
        counts["files_rejected"] += 1
        rejections[reason] += 1
        diagnostics.append({"message_id": identifier, "reason": reason})

    try:
        with bz2.open(path, "rb") as compressed:
            expanded = _BoundedReader(compressed, limits.archive_expanded_bytes)
            with tarfile.open(fileobj=expanded, mode="r|") as archive:
                for member in archive:
                    counts["archive_members"] += 1
                    if counts["archive_members"] > limits.archive_members:
                        raise IngestionError("archive_members_limit")
                    name = safe_member_name(member.name, source.source_group)
                    if name in seen:
                        raise IngestionError("duplicate_archive_path")
                    seen.add(name)
                    if member.isdir():
                        counts["directories_ignored"] += 1
                        continue
                    if member.type not in {tarfile.REGTYPE, tarfile.AREGTYPE} or (
                        member.issparse() or member.size < 0
                    ):
                        raise IngestionError("unsafe_archive_member")
                    if "/" not in name or member.name.endswith("/"):
                        raise IngestionError("archive_path")
                    if name == f"{source.source_group}/cmds":
                        counts["metadata_files_ignored"] += 1
                        continue
                    identifier = message_id(source, name)
                    counts["files_seen"] += 1
                    if member.size > limits.message_bytes:
                        reject(identifier, "message_limit")
                        continue
                    data_stream = archive.extractfile(member)
                    if data_stream is None:
                        raise IngestionError("invalid_archive")
                    with data_stream:
                        data = data_stream.read(member.size + 1)
                    if len(data) != member.size:
                        raise IngestionError("truncated_archive_member")
                    # An owned private directory and generated basename are used instead
                    # of archive-controlled filesystem paths, modes, owners or links.
                    private = staging / f"{identifier}.eml"
                    try:
                        with private.open("xb") as output:
                            output.write(data)
                        try:
                            parsed = parse_message(private.read_bytes(), limits)
                        except MessageRejected as error:
                            reject(identifier, error.reason)
                            continue
                        emit(
                            dict(
                                message_id=identifier,
                                source_group=source.source_group,
                                source_archive=source.archive_name,
                                source_file=name,
                                label=source.label,
                                **asdict(parsed),
                            )
                        )
                        counts["files_accepted"] += 1
                        warnings.update(parsed.parse_warnings)
                    finally:
                        private.unlink(missing_ok=True)
            # Finish decompression to check its trailer/CRC and bound trailing padding.
            while expanded.read(64 * 1024):
                pass
    except IngestionError:
        raise
    except (EOFError, tarfile.TarError) as error:
        raise IngestionError("invalid_archive") from error
    return {
        **counts,
        "rejection_counts": dict(sorted(rejections.items())),
        "warning_counts": dict(sorted(warnings.items())),
        "rejections": diagnostics,
    }


def _outputs(root):
    root = Path(root).resolve()
    paths = [root / name for name in (RECORD_FILE, REPORT_FILE, MANIFEST_FILE)]
    for path in paths:
        if not path.resolve().is_relative_to(root) or path.is_symlink() or path.is_dir():
            raise IngestionError("invalid_output_path")
    return root, paths


def publish_artifacts(pairs, staging, validate):
    """Publish a preparation stage, restoring the previous set on ordinary failures."""
    backups, published = {}, []
    try:
        for index, (temporary, target) in enumerate(pairs):
            if target.exists():
                backup = staging / f"previous-{index}"
                target.replace(backup)
                backups[target] = backup
            temporary.replace(target)
            published.append(target)
        return validate()
    except BaseException:
        for _, target in reversed(pairs):
            if target in published:
                target.unlink(missing_ok=True)
            if target in backups:
                backups[target].replace(target)
        raise


def ingest_sources(root, limits=DEFAULT_LIMITS):
    root, (records_path, report_path, manifest_path) = _outputs(root)
    raw = root / "data/raw"
    with corpus_lock(raw):
        manifest = verify_sources(root)
        with tempfile.TemporaryDirectory(prefix=".ingest-", dir=raw) as temporary:
            staging = Path(temporary)
            records = staging / "messages.parsed.jsonl"
            digest, output_size = hashlib.sha256(), 0
            with records.open("xb") as output:
                records.chmod(0o600)

                def emit(record):
                    nonlocal output_size
                    data = (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode()
                    output_size += len(data)
                    if output_size > limits.output_bytes:
                        raise IngestionError("output_limit")
                    output.write(data)
                    digest.update(data)

                sources = [
                    _archive(raw / source.archive_name, source, staging, emit, limits)
                    for source in manifest.archives
                ]
            report = dict(
                schema_version=1,
                stage="parsed_before_deduplication",
                preprocessing_version=PREPROCESSING_VERSION,
                python_version=platform.python_version(),
                limits=asdict(limits),
                records_file=RECORD_FILE,
                records_sha256=digest.hexdigest(),
                records_size_bytes=output_size,
                sources=sources,
                **{
                    key: sum(s[key] for s in sources)
                    for key in (
                        "files_seen",
                        "files_accepted",
                        "files_rejected",
                        "metadata_files_ignored",
                        "directories_ignored",
                    )
                },
            )
            parsed_sources = [
                SourceArchive(
                    **{
                        **source.model_dump(),
                        "processing_status": "complete",
                        **{
                            key: counts[key]
                            for key in ("files_seen", "files_accepted", "files_rejected")
                        },
                    }
                )
                for source, counts in zip(manifest.archives, sources, strict=True)
            ]
            updated = SourceManifest(**{**manifest.model_dump(), "archives": parsed_sources})
            new_report, new_manifest = (
                staging / "parsing_report.json",
                staging / "source_manifest.json",
            )
            new_report.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            new_manifest.write_text(updated.model_dump_json(indent=2) + "\n", encoding="utf-8")
            verify_sources(root)  # Detect changes to inputs before publication.
            return publish_artifacts(
                [(records, records_path), (new_report, report_path), (new_manifest, manifest_path)],
                staging,
                lambda: verify_parsed_sources(root, limits),
            )


def verify_parsed_sources(root, limits=DEFAULT_LIMITS):
    root, (records_path, report_path, _) = _outputs(root)
    manifest = verify_sources(root)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        not isinstance(report, dict)
        or set(report) != REPORT_KEYS
        or any(type(report[k]) is not int or report[k] < 0 for k in TOTAL_KEYS)
        or (report.get("schema_version"), report.get("stage"), report.get("preprocessing_version"))
        != (1, "parsed_before_deduplication", PREPROCESSING_VERSION)
        or report.get("limits") != asdict(limits)
        or report.get("records_file") != RECORD_FILE
    ):
        raise IngestionError("invalid_parsing_report")
    if report.get("python_version") != platform.python_version():
        raise IngestionError("parser_runtime_mismatch")
    size = records_path.stat().st_size
    if size != report["records_size_bytes"] or size > limits.output_bytes:
        raise IngestionError("parsed_output_size_mismatch")
    with records_path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != report["records_sha256"]:
            raise IngestionError("parsed_output_hash_mismatch")
    counts, warnings, identifiers = Counter(), {}, set()
    by_group = {source.source_group: source for source in manifest.archives}
    with records_path.open("rb") as stream:
        while line := stream.readline(8 * limits.text_characters + 4097):
            if not line.endswith(b"\n") or len(line) > 8 * limits.text_characters + 4096:
                raise IngestionError("invalid_parsed_record")
            row = json.loads(line)
            if not isinstance(row, dict) or set(row) != RECORD_KEYS:
                raise IngestionError("invalid_parsed_record")
            source = by_group[row["source_group"]]
            name = safe_member_name(row["source_file"], source.source_group)
            model = "\n".join(text for text in (row["subject_text"], row["body_text"]) if text)
            if (
                not model
                or model != row["model_text"]
                or len(model) != row["character_count"]
                or len(model) > limits.text_characters
                or any(normalize_text(row[k]) != row[k] for k in ("subject_text", "body_text"))
                or hashlib.sha256(model.encode()).hexdigest() != row["content_sha256"]
                or row["message_id"] != message_id(source, name)
                or row["message_id"] in identifiers
                or row["label"] != source.label
                or row["source_archive"] != source.archive_name
                or not set(row["parse_warnings"]).issubset(WARNING_CODES)
                or row["parse_warnings"] != sorted(set(row["parse_warnings"]))
                or "split" in row
                or "token_count" in row
            ):
                raise IngestionError("invalid_parsed_record")
            identifiers.add(row["message_id"])
            counts[source.source_group] += 1
            warnings.setdefault(source.source_group, Counter()).update(row["parse_warnings"])
    if len(report["sources"]) != len(manifest.archives):
        raise IngestionError("invalid_parsing_report")
    for source, measured in zip(manifest.archives, report["sources"], strict=True):
        group = source.source_group
        if (
            not isinstance(measured, dict)
            or set(measured) != SOURCE_KEYS
            or any(
                type(measured[k]) is not int or measured[k] < 0
                for k in TOTAL_KEYS | {"archive_members"}
            )
            or any(set(item) != {"message_id", "reason"} for item in measured["rejections"])
        ):
            raise IngestionError("invalid_parsing_report")
        if (
            source.processing_status != "complete"
            or measured["archive_name"] != source.archive_name
            or measured["source_group"] != group
            or measured["label"] != source.label
            or measured["archive_sha256"] != source.sha256
            or source.files_accepted != counts[group]
            or measured["warning_counts"] != dict(warnings.get(group, {}))
            or any(
                measured[k] != getattr(source, k)
                for k in ("files_seen", "files_accepted", "files_rejected")
            )
            or measured["archive_members"]
            != source.files_seen
            + measured["directories_ignored"]
            + measured["metadata_files_ignored"]
            or len(measured["rejections"]) != source.files_rejected
            or dict(Counter(item["reason"] for item in measured["rejections"]))
            != measured["rejection_counts"]
            or not set(measured["rejection_counts"]).issubset(REJECTION_CODES)
        ):
            raise IngestionError("parsing_counts_mismatch")
        for rejection in measured["rejections"]:
            identifier = rejection["message_id"]
            if len(identifier) != 64 or any(c not in "0123456789abcdef" for c in identifier):
                raise IngestionError("invalid_diagnostic_id")
            if identifier in identifiers:
                raise IngestionError("duplicate_diagnostic_id")
            identifiers.add(identifier)
    for key in (
        "files_seen",
        "files_accepted",
        "files_rejected",
        "metadata_files_ignored",
        "directories_ignored",
    ):
        if report[key] != sum(source[key] for source in report["sources"]):
            raise IngestionError("parsing_counts_mismatch")
    return report
