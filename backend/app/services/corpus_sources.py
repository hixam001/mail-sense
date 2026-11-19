"""Acquire canonical official archives and verify provenance without parsing mail."""

import hashlib
import tempfile
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

BASE_URL = "https://spamassassin.apache.org/old/publiccorpus/"
README_URL = BASE_URL + "readme.html"
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
# The March 2005 spam_2 revision corrects a misclassified ham message.
CANONICAL = {
    "easy_ham": ("20030228_easy_ham.tar.bz2", "ham"),
    "easy_ham_2": ("20030228_easy_ham_2.tar.bz2", "ham"),
    "hard_ham": ("20030228_hard_ham.tar.bz2", "ham"),
    "spam": ("20030228_spam.tar.bz2", "spam"),
    "spam_2": ("20050311_spam_2.tar.bz2", "spam"),
}


class SourceArchive(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    archive_name: str
    source_url: str
    source_group: Literal["easy_ham", "easy_ham_2", "hard_ham", "spam", "spam_2"]
    label: Literal["ham", "spam"]
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0, le=MAX_ARCHIVE_BYTES)
    acquired_at: AwareDatetime
    processing_status: Literal["not_started", "complete"]
    files_seen: int | None = Field(ge=0)
    files_accepted: int | None = Field(ge=0)
    files_rejected: int | None = Field(ge=0)

    @model_validator(mode="after")
    def validate_provenance(self):
        filename, label = CANONICAL[self.source_group]
        if (self.archive_name, self.label, self.source_url) != (
            filename, label, BASE_URL + filename
        ):
            raise ValueError("Archive filename, label and URL must match its canonical group")
        if self.acquired_at.utcoffset() != timedelta(0):
            raise ValueError("Acquisition timestamp must be UTC")
        counts = (self.files_seen, self.files_accepted, self.files_rejected)
        if self.processing_status == "not_started":
            if any(value is not None for value in counts):
                raise ValueError("Unprocessed archives must have null parsing counts")
        elif any(value is None for value in counts):
            raise ValueError("Completed parsing requires all three counts")
        elif self.files_seen != self.files_accepted + self.files_rejected:
            raise ValueError("Parsing counts must reconcile")
        return self


class SourceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    dataset_source: Literal["apache_spamassassin_public_corpus"]
    source_index_url: str
    source_readme_url: str
    selection_policy: Literal["one_canonical_archive_per_group"]
    checksum_origin: Literal["locally_computed_sha256"]
    archives: list[SourceArchive] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def validate_selection(self):
        if self.source_index_url != BASE_URL or self.source_readme_url != README_URL:
            raise ValueError("Manifest must identify the official corpus index and README")
        if {record.source_group for record in self.archives} != set(CANONICAL):
            raise ValueError("Manifest requires exactly one archive for each approved group")
        return self


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.URLError("Corpus downloads do not follow redirects")


def _open_official(url):
    request = urllib.request.Request(url, headers={"User-Agent": "MailSense corpus acquisition"})
    return urllib.request.build_opener(_RejectRedirects()).open(request, timeout=30)


def _paths(root):
    root = Path(root).resolve()
    raw = root / "data/raw"
    manifest = root / "data/processed/source_manifest.json"
    for path in [raw, manifest]:
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            raise ValueError("Corpus paths must stay within the project and cannot be symlinks")
    return raw, manifest


def load_manifest(path):
    return SourceManifest.model_validate_json(Path(path).read_text(encoding="utf-8"))


def _verify_file(raw, record):
    path = raw / record.archive_name
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Missing or linked archive: {record.archive_name}")
    if path.stat().st_size != record.size_bytes:
        raise ValueError(f"Archive size mismatch: {record.archive_name}")
    with path.open("rb") as stream:
        if stream.read(4) not in [b"BZh" + bytes([n]) for n in range(ord("1"), ord("9") + 1)]:
            raise ValueError(f"Archive is not a bzip2 candidate: {record.archive_name}")
        stream.seek(0)
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != record.sha256:
        raise ValueError(f"Archive SHA-256 mismatch: {record.archive_name}")


def verify_sources(root):
    """Check schema, selection and all local archive bytes without any network calls."""
    raw, path = _paths(root)
    manifest = load_manifest(path)
    for record in manifest.archives:
        _verify_file(raw, record)
    return manifest


def _fetch(url, path, opener):
    digest, size, prefix = hashlib.sha256(), 0, b""
    with opener(url) as response, path.open("xb") as output:
        if response.status != 200:
            raise ValueError("Corpus server did not return HTTP 200")
        length = response.headers.get("Content-Length")
        expected = int(length) if length is not None else None
        if expected is not None and not 0 < expected <= MAX_ARCHIVE_BYTES:
            raise ValueError("Corpus archive Content-Length exceeds the permitted size")
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_ARCHIVE_BYTES:
                raise ValueError("Corpus archive exceeds the permitted size")
            prefix = (prefix + chunk)[:4]
            digest.update(chunk)
            output.write(chunk)
    if not size or (expected is not None and size != expected):
        raise ValueError("Empty or truncated corpus archive")
    if len(prefix) != 4 or prefix[:3] != b"BZh" or prefix[3:4] not in b"123456789":
        raise ValueError("Corpus response is not a bzip2 candidate")
    return digest.hexdigest(), size


@contextmanager
def corpus_lock(raw):
    path = raw / ".acquisition.lock"
    try:
        stream = path.open("x")
    except FileExistsError as error:
        raise ValueError(
            "Corpus acquisition lock exists; check for another active download"
        ) from error
    try:
        with stream:
            yield
    finally:
        path.unlink(missing_ok=True)


def _write_manifest(path, manifest):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=".source_manifest-", delete=False
        ) as output:
            temporary = Path(output.name)
            output.write(manifest.model_dump_json(indent=2) + "\n")
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def download_sources(root, opener=None):
    """Download only absent canonical archives; existing manifests pin their bytes."""
    raw, path = _paths(root)
    raw.mkdir(parents=True, exist_ok=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with corpus_lock(raw):
        existing = load_manifest(path) if path.exists() else None
        records = {r.source_group: r for r in existing.archives} if existing else {}
        missing = []
        for group, (filename, _) in CANONICAL.items():
            target = raw / filename
            if target.is_symlink():
                raise ValueError(f"Linked archive cannot be used: {filename}")
            if target.exists():
                if not existing:
                    raise ValueError(f"Archive exists without a source manifest: {filename}")
                _verify_file(raw, records[group])
            else:
                missing.append(group)
        if not missing:
            return existing
        with tempfile.TemporaryDirectory(prefix=".acquire-", dir=raw) as temporary:
            staging = Path(temporary)
            for group in missing:
                filename, label = CANONICAL[group]
                digest, size = _fetch(
                    BASE_URL + filename, staging / filename, opener or _open_official
                )
                previous = records.get(group)
                if previous and (digest, size) != (previous.sha256, previous.size_bytes):
                    raise ValueError(f"Downloaded bytes differ from pinned provenance: {filename}")
                if previous:
                    values = previous.model_dump()
                    values["acquired_at"] = datetime.now(UTC)
                else:
                    values = dict(
                        archive_name=filename, source_url=BASE_URL + filename, source_group=group,
                        label=label, sha256=digest, size_bytes=size, acquired_at=datetime.now(UTC),
                        processing_status="not_started", files_seen=None, files_accepted=None,
                        files_rejected=None,
                    )
                records[group] = SourceArchive(**values)
            manifest = SourceManifest(
                schema_version=1, dataset_source="apache_spamassassin_public_corpus",
                source_index_url=BASE_URL, source_readme_url=README_URL,
                selection_policy="one_canonical_archive_per_group",
                checksum_origin="locally_computed_sha256",
                archives=[records[group] for group in CANONICAL],
            )
            for group in missing:
                filename = CANONICAL[group][0]
                (staging / filename).replace(raw / filename)
            _write_manifest(path, manifest)
        return verify_sources(root)
