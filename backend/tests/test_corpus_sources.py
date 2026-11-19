"""Synthetic transport/manifest regression cases; no real mail is parsed here."""

import io
import json
import urllib.error
from contextlib import contextmanager

import pytest
from pydantic import ValidationError

from app.services import corpus_sources as sources


class Response(io.BytesIO):
    def __init__(self, data, *, length=None, status=200):
        super().__init__(data)
        self.status = status
        self.headers = {"Content-Length": str(len(data) if length is None else length)}


def payload(url):
    # Only the download header/integrity boundary is tested; this is not a tarball.
    return b"BZh9synthetic-" + url.rsplit("/", 1)[-1].encode()


def opener(url):
    assert url in {sources.BASE_URL + filename for filename, _ in sources.CANONICAL.values()}
    return Response(payload(url))


@pytest.fixture
def acquired(tmp_path):
    return tmp_path, sources.download_sources(tmp_path, opener=opener)


def manifest_path(root):
    return root / "data/processed/source_manifest.json"


def test_acquire_all_groups_with_real_metadata_and_unknown_counts(acquired):
    root, manifest = acquired
    assert len(manifest.archives) == 5
    assert {r.source_group for r in manifest.archives} == set(sources.CANONICAL)
    for record in manifest.archives:
        assert record.processing_status == "not_started"
        assert record.files_seen is record.files_accepted is record.files_rejected is None
        assert record.acquired_at.utcoffset().total_seconds() == 0
    assert sources.verify_sources(root) == manifest


def test_complete_cache_is_offline_and_does_not_rewrite_provenance(acquired, monkeypatch):
    root, manifest = acquired
    before = manifest_path(root).read_bytes()

    def forbidden(url):
        pytest.fail(f"Network accessed despite a complete cache: {url}")

    monkeypatch.setattr(sources, "_open_official", forbidden)
    assert sources.verify_sources(root) == manifest
    assert sources.download_sources(root) == manifest
    assert manifest_path(root).read_bytes() == before


@pytest.mark.parametrize("field,value", [
    ("archive_name", "../../private"),
    ("archive_name", "20021010_easy_ham.tar.bz2"),
    ("source_url", "https://example.com/mail.tar.bz2"),
    ("label", "spam"),
    ("sha256", "not-a-checksum"),
    ("size_bytes", -1),
    ("acquired_at", "2026-11-19T00:00:00"),
    ("files_seen", 0),
])
def test_invalid_record_is_rejected_without_rewriting(acquired, field, value):
    root, _ = acquired
    data = json.loads(manifest_path(root).read_text())
    data["archives"][0][field] = value
    manifest_path(root).write_text(json.dumps(data))
    with pytest.raises(ValidationError):
        sources.verify_sources(root)


def test_duplicate_or_missing_group_is_rejected(acquired):
    root, _ = acquired
    data = json.loads(manifest_path(root).read_text())
    data["archives"][1] = data["archives"][0]
    manifest_path(root).write_text(json.dumps(data))
    with pytest.raises(ValidationError, match="exactly one"):
        sources.verify_sources(root)


def test_corrupted_local_bytes_fail_without_overwrite(acquired):
    root, manifest = acquired
    record = manifest.archives[0]
    path = root / "data/raw" / record.archive_name
    path.write_bytes(path.read_bytes()[:-1] + b"!")
    before = manifest_path(root).read_bytes()
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        sources.download_sources(root, opener=opener)
    assert manifest_path(root).read_bytes() == before


def test_missing_archive_is_restored_against_its_recorded_hash(acquired):
    root, manifest = acquired
    record = manifest.archives[0]
    (root / "data/raw" / record.archive_name).unlink()
    with pytest.raises(ValueError, match="Missing"):
        sources.verify_sources(root)
    urls = []

    def recording(url):
        urls.append(url)
        return opener(url)

    restored = sources.download_sources(root, opener=recording)
    assert urls == [record.source_url]
    assert restored.archives[0].sha256 == record.sha256
    sources.verify_sources(root)


def test_upstream_change_during_restore_preserves_manifest(acquired):
    root, manifest = acquired
    record = manifest.archives[0]
    path = root / "data/raw" / record.archive_name
    path.unlink()
    before = manifest_path(root).read_bytes()
    with pytest.raises(ValueError, match="pinned provenance"):
        sources.download_sources(root, opener=lambda url: Response(payload(url) + b"changed"))
    assert manifest_path(root).read_bytes() == before
    assert not path.exists()


def test_interrupted_batch_does_not_publish_partial_provenance(tmp_path):
    requests = []

    def interrupted(url):
        requests.append(url)
        if len(requests) == 2:
            raise urllib.error.URLError("synthetic interruption")
        return opener(url)

    with pytest.raises(urllib.error.URLError):
        sources.download_sources(tmp_path, opener=interrupted)
    assert not manifest_path(tmp_path).exists()
    assert list((tmp_path / "data/raw").iterdir()) == []


@pytest.mark.parametrize("response", [
    lambda: Response(b"<html>not an archive</html>"),
    lambda: Response(b"BZh9data", length=100),
    lambda: Response(b"BZh9data", length=sources.MAX_ARCHIVE_BYTES + 1),
    lambda: Response(b"", length=0),
    lambda: Response(b"BZh9data", status=503),
])
def test_invalid_transport_response_is_not_published(tmp_path, response):
    with pytest.raises(ValueError):
        sources.download_sources(tmp_path, opener=lambda url: response())
    assert not manifest_path(tmp_path).exists()
    assert list((tmp_path / "data/raw").iterdir()) == []


def test_streaming_limit_applies_without_content_length(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "MAX_ARCHIVE_BYTES", 8)
    response = Response(b"BZh9" + b"x" * 32)
    response.headers = {}
    with pytest.raises(ValueError, match="permitted size"):
        sources.download_sources(tmp_path, opener=lambda url: response)
    assert not manifest_path(tmp_path).exists()


def test_unmanifested_existing_file_is_not_overwritten(tmp_path):
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    path = raw / sources.CANONICAL["easy_ham"][0]
    path.write_bytes(b"local bytes")
    with pytest.raises(ValueError, match="without a source manifest"):
        sources.download_sources(tmp_path, opener=opener)
    assert path.read_bytes() == b"local bytes"


def test_existing_acquisition_lock_is_preserved(tmp_path):
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    lock = raw / ".acquisition.lock"
    lock.write_text("another process")
    with pytest.raises(ValueError, match="lock exists"):
        sources.download_sources(tmp_path, opener=opener)
    assert lock.read_text() == "another process"


def test_download_redirects_are_rejected():
    with pytest.raises(urllib.error.URLError, match="redirects"):
        sources._RejectRedirects().redirect_request(None, None, 302, "Found", {}, "https://elsewhere/")


def test_linked_cache_directory_outside_project_is_rejected(tmp_path):
    root = tmp_path / "project"
    outside = tmp_path / "outside"
    (root / "data").mkdir(parents=True)
    outside.mkdir()
    (root / "data/raw").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="within the project"):
        sources.download_sources(root, opener=opener)
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("counts,valid", [
    ((2, 1, 1), True),
    ((2, 3, 0), False),
    ((2, None, 0), False),
])
def test_completed_parser_count_contract(acquired, counts, valid):
    root, _ = acquired
    data = json.loads(manifest_path(root).read_text())
    data["archives"][0].update(
        processing_status="complete", files_seen=counts[0],
        files_accepted=counts[1], files_rejected=counts[2],
    )
    manifest_path(root).write_text(json.dumps(data))
    if valid:
        sources.verify_sources(root)
    else:
        with pytest.raises(ValidationError):
            sources.verify_sources(root)


def test_failed_manifest_write_preserves_provenance_and_cleans_temporary(acquired, monkeypatch):
    root, manifest = acquired
    path = manifest_path(root)
    before = path.read_bytes()
    original = sources.tempfile.NamedTemporaryFile

    @contextmanager
    def failed_write(**kwargs):
        with original(**kwargs) as stream:
            class BrokenOutput:
                name = stream.name

                def write(self, text):
                    raise OSError("synthetic disk failure")

            yield BrokenOutput()

    monkeypatch.setattr(sources.tempfile, "NamedTemporaryFile", failed_write)
    with pytest.raises(OSError, match="disk failure"):
        sources._write_manifest(path, manifest)
    assert path.read_bytes() == before
    assert list(path.parent.glob(".source_manifest-*")) == []
