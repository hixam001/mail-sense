"""Real synthetic tar/bzip2 fixtures; no public-corpus text is embedded in tests."""

import bz2
import hashlib
import io
import json
import sys
import tarfile
from dataclasses import replace
from pathlib import Path

import pytest

from app.services import corpus_ingest as ingest
from app.services import corpus_sources as sources
from app.services.mail_parser import DEFAULT_LIMITS
from scripts import ingest_corpus as cli

MAIL = b"Subject: Private fixture subject\nFrom: secret@example.invalid\n\nPrivate fixture body"


def archive_bytes(group, entries=None):
    entries = (
        entries
        if entries is not None
        else [
            (group, tarfile.DIRTYPE, b""),
            (group + "/cmds", tarfile.REGTYPE, b"NEVER EXECUTE THIS PRIVATE CONTROL"),
            (group + "/secret-original-name", tarfile.REGTYPE, MAIL),
            (group + "/empty-name", tarfile.REGTYPE, b"From: nobody@example.invalid\n\n"),
        ]
    )
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:bz2", format=tarfile.USTAR_FORMAT) as archive:
        for name, kind, data in entries:
            member = tarfile.TarInfo(name)
            member.type, member.size = kind, len(data)
            if kind in {tarfile.SYMTYPE, tarfile.LNKTYPE}:
                member.linkname = "../../escape"
            archive.addfile(member, io.BytesIO(data))
    return output.getvalue()


def prepare(root, first=None):
    raw, processed = root / "data/raw", root / "data/processed"
    raw.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    records = []
    for index, (group, (filename, label)) in enumerate(sources.CANONICAL.items()):
        data = first if index == 0 and first is not None else archive_bytes(group)
        (raw / filename).write_bytes(data)
        records.append(
            dict(
                archive_name=filename,
                source_url=sources.BASE_URL + filename,
                source_group=group,
                label=label,
                sha256=hashlib.sha256(data).hexdigest(),
                size_bytes=len(data),
                acquired_at="2026-11-19T00:00:00Z",
                processing_status="not_started",
                files_seen=None,
                files_accepted=None,
                files_rejected=None,
            )
        )
    manifest = dict(
        schema_version=1,
        dataset_source="apache_spamassassin_public_corpus",
        source_index_url=sources.BASE_URL,
        source_readme_url=sources.README_URL,
        selection_policy="one_canonical_archive_per_group",
        checksum_origin="locally_computed_sha256",
        archives=records,
    )
    (root / ingest.MANIFEST_FILE).write_text(json.dumps(manifest))
    return root


@pytest.fixture
def corpus(tmp_path):
    return prepare(tmp_path)


def snapshot(root):
    return {
        name: (root / name).read_bytes()
        for name in (
            ingest.RECORD_FILE,
            ingest.REPORT_FILE,
            ingest.MANIFEST_FILE,
        )
    }


def test_pipeline_counts_private_features_repeatability_and_provenance(corpus):
    before = sources.verify_sources(corpus)
    report = ingest.ingest_sources(corpus)
    assert (report["files_seen"], report["files_accepted"], report["files_rejected"]) == (10, 5, 5)
    assert report["metadata_files_ignored"] == report["directories_ignored"] == 5
    rows = [json.loads(line) for line in (corpus / ingest.RECORD_FILE).read_text().splitlines()]
    assert len({row["message_id"] for row in rows}) == 5
    assert len({row["content_sha256"] for row in rows}) == 1  # Not deduplicated here.
    for row in rows:
        assert row["model_text"] == "Private fixture subject\nPrivate fixture body"
        assert not {"token_count", "split"} & row.keys()
    public = (corpus / ingest.REPORT_FILE).read_text()
    for secret in ("Private fixture", "secret@example", "secret-original-name", "empty-name"):
        assert secret not in public
    after = sources.verify_sources(corpus)
    for old, new in zip(before.archives, after.archives, strict=True):
        assert new.model_dump(
            exclude={"processing_status", "files_seen", "files_accepted", "files_rejected"}
        ) == old.model_dump(
            exclude={"processing_status", "files_seen", "files_accepted", "files_rejected"}
        )
    original = snapshot(corpus)
    assert (corpus / ingest.RECORD_FILE).stat().st_mode & 0o777 == 0o600
    assert ingest.ingest_sources(corpus) == report
    assert snapshot(corpus) == original
    assert ingest.verify_parsed_sources(corpus) == report
    assert not list((corpus / "data/raw").glob(".ingest-*"))
    assert not (corpus / "data/raw/.acquisition.lock").exists()


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "/tmp/escape",
        "easy_ham/../escape",
        "easy_ham/./escape",
        "easy_ham//escape",
        "easy_ham\\escape",
        "C:/escape",
        "spam/wrong-group",
        "easy_ham/line\nfeed",
        "easy_ham/" + "deep/" * 9 + "file",
    ],
)
def test_unsafe_paths_abort_without_publication(tmp_path, name):
    root = prepare(tmp_path, archive_bytes("easy_ham", [(name, tarfile.REGTYPE, MAIL)]))
    original = (root / ingest.MANIFEST_FILE).read_bytes()
    with pytest.raises(ingest.IngestionError, match="archive_path"):
        ingest.ingest_sources(root)
    assert (root / ingest.MANIFEST_FILE).read_bytes() == original
    assert not (root / ingest.RECORD_FILE).exists()
    assert not (tmp_path / "escape").exists()
    assert not list((root / "data/raw").glob(".ingest-*"))


@pytest.mark.parametrize(
    "kind",
    [
        tarfile.SYMTYPE,
        tarfile.LNKTYPE,
        tarfile.CHRTYPE,
        tarfile.BLKTYPE,
        tarfile.FIFOTYPE,
        tarfile.CONTTYPE,
        tarfile.GNUTYPE_SPARSE,
    ],
)
def test_links_and_special_files_are_refused(tmp_path, kind):
    root = prepare(tmp_path, archive_bytes("easy_ham", [("easy_ham/link", kind, b"")]))
    with pytest.raises(ingest.IngestionError, match="unsafe_archive_member"):
        ingest.ingest_sources(root)
    assert not (root / ingest.REPORT_FILE).exists()


def test_duplicate_member_is_fatal_even_if_mail_is_valid(tmp_path):
    entry = ("easy_ham/repeated", tarfile.REGTYPE, MAIL)
    root = prepare(tmp_path, archive_bytes("easy_ham", [entry, entry]))
    with pytest.raises(ingest.IngestionError, match="duplicate_archive_path"):
        ingest.ingest_sources(root)


@pytest.mark.parametrize(
    "limit,value,reason",
    [
        ("archive_members", 1, "archive_members_limit"),
        ("archive_expanded_bytes", 1024, "archive_expansion_limit"),
        ("output_bytes", 32, "output_limit"),
    ],
)
def test_resource_limits_abort_and_leave_manifest_untouched(corpus, limit, value, reason):
    original = (corpus / ingest.MANIFEST_FILE).read_bytes()
    with pytest.raises(ingest.IngestionError, match=reason):
        ingest.ingest_sources(corpus, replace(DEFAULT_LIMITS, **{limit: value}))
    assert (corpus / ingest.MANIFEST_FILE).read_bytes() == original
    assert not (corpus / ingest.RECORD_FILE).exists()


def test_oversize_message_is_counted_and_does_not_abort(corpus):
    limits = replace(DEFAULT_LIMITS, message_bytes=16)
    report = ingest.ingest_sources(corpus, limits)
    assert report["files_seen"] == report["files_rejected"] == 10
    assert report["files_accepted"] == 0
    assert (corpus / ingest.RECORD_FILE).read_bytes() == b""
    assert all(s["rejection_counts"] == {"message_limit": 2} for s in report["sources"])


@pytest.mark.parametrize(
    "broken",
    [
        archive_bytes("easy_ham")[:-8],
        bz2.compress(b"this is not tar data"),
        bz2.compress(b"\0" * 1024 + b"z" * 20000),
    ],
)
def test_corrupt_compression_or_archive_and_expanded_trailer_fail(tmp_path, broken):
    root = prepare(tmp_path, broken)
    with pytest.raises((ingest.IngestionError, OSError)):
        ingest.ingest_sources(root, replace(DEFAULT_LIMITS, archive_expanded_bytes=15000))
    assert not (root / ingest.RECORD_FILE).exists()


@pytest.mark.parametrize("artifact", ["records", "report_counts", "report_extra", "row_extra"])
def test_verifier_detects_changed_text_counts_and_unapproved_fields(corpus, artifact):
    ingest.ingest_sources(corpus)
    record_path, report_path = corpus / ingest.RECORD_FILE, corpus / ingest.REPORT_FILE
    report = json.loads(report_path.read_text())
    if artifact == "records":
        record_path.write_bytes(record_path.read_bytes().replace(b"fixture body", b"CHANGED body"))
    elif artifact == "report_counts":
        report["sources"][0]["files_accepted"] += 1
    elif artifact == "report_extra":
        report["raw_subject"] = "private"
    else:
        rows = [json.loads(line) for line in record_path.read_text().splitlines()]
        rows[0]["split"] = "train"
        data = "".join(json.dumps(row) + "\n" for row in rows).encode()
        record_path.write_bytes(data)
        report["records_size_bytes"] = len(data)
        report["records_sha256"] = hashlib.sha256(data).hexdigest()
    report_path.write_text(json.dumps(report))
    with pytest.raises(ingest.IngestionError):
        ingest.verify_parsed_sources(corpus)


@pytest.mark.parametrize("when", ["replace", "validate"])
def test_publication_failure_restores_every_previous_artifact(corpus, monkeypatch, when):
    ingest.ingest_sources(corpus)
    original, replace_path = snapshot(corpus), Path.replace
    failed = False

    def fail_once(self, target):
        nonlocal failed
        if not failed and self.name == "source_manifest.json" and ".ingest-" in str(self):
            failed = True
            raise OSError("synthetic write failure")
        return replace_path(self, target)

    if when == "replace":
        monkeypatch.setattr(Path, "replace", fail_once)
    else:

        def invalid(*args):
            raise ingest.IngestionError("synthetic validation failure")

        monkeypatch.setattr(ingest, "verify_parsed_sources", invalid)
    with pytest.raises((OSError, ingest.IngestionError)):
        ingest.ingest_sources(corpus)
    assert snapshot(corpus) == original
    assert not list((corpus / "data/raw").glob(".ingest-*"))


def test_cli_discloses_only_aggregate_counts(corpus, monkeypatch, capsys):
    monkeypatch.setattr(cli, "ROOT", corpus)
    monkeypatch.setattr(sys, "argv", ["ingest_corpus", "run"])
    assert cli.main() == 0
    output = capsys.readouterr().out
    assert "5 accepted / 10 candidates" in output
    assert "secret" not in output and "fixture" not in output
    (corpus / ingest.REPORT_FILE).write_text("invalid private fixture")
    monkeypatch.setattr(sys, "argv", ["ingest_corpus", "verify"])
    assert cli.main() == 1
    assert capsys.readouterr().err == (
        "Ingestion failed: missing_or_invalid_preparation_artifacts\n"
    )


def test_linked_output_is_refused(corpus, tmp_path):
    external = tmp_path / "elsewhere"
    external.write_text("keep")
    (corpus / ingest.RECORD_FILE).symlink_to(external)
    with pytest.raises(ingest.IngestionError, match="invalid_output_path"):
        ingest.ingest_sources(corpus)
    assert external.read_text() == "keep"
