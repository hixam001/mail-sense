import json
import sys
from pathlib import Path

import numpy as np
import pytest
from test_corpus_dataset import mail, prepare

from app.services import model_store as store
from app.services.corpus_dataset import prepare_dataset
from app.services.corpus_split import SPLIT_FILE, prepare_split
from app.services.training import binary_presence
from scripts import train_models as cli


@pytest.fixture
def corpus(tmp_path):
    messages = {
        group: [mail(f"{group} {i}") for i in range(5)]
        for group in ("easy_ham", "easy_ham_2", "hard_ham", "spam", "spam_2")
    }
    prepare(tmp_path, messages)
    prepare_dataset(tmp_path)
    prepare_split(tmp_path)
    return tmp_path


def snapshot(root):
    return {
        name: (root / store.MODEL_DIR / name).read_bytes()
        for name in (*store.MODEL_FILES.values(), store.METADATA_FILE)
    }


def test_trusted_roundtrip_and_identical_retrain_preserve_original_provenance(corpus):
    first = store.prepare_models(corpus)
    original = snapshot(corpus)
    second = store.prepare_models(corpus)
    assert second.metadata == first.metadata
    assert snapshot(corpus) == original
    x = second.vectorizer.transform(["free offer", "project meeting"])
    for name, model in second.models.items():
        p = model.predict_proba(binary_presence(x) if name == "bernoulli" else x)
        assert np.isfinite(p).all() and np.allclose(p.sum(axis=1), 1)
    for name in original:
        assert (corpus / store.MODEL_DIR / name).stat().st_mode & 0o777 == 0o600


def test_all_hashes_are_checked_before_any_unpickle(corpus, monkeypatch):
    store.prepare_models(corpus)
    path = corpus / store.MODEL_DIR / store.MODEL_FILES["bernoulli"]
    path.write_bytes(path.read_bytes() + b"tampered")
    monkeypatch.setattr(
        store.joblib, "load", lambda *args: pytest.fail("Unpickled before all checksums")
    )
    with pytest.raises(store.ModelArtifactError, match="checksum"):
        store.load_models(corpus)


@pytest.mark.parametrize(
    "change", ["split", "runtime", "model_split", "vocabulary", "extra", "date", "files"]
)
def test_metadata_mismatch_prevents_unpickling(corpus, monkeypatch, change):
    store.prepare_models(corpus)
    path = corpus / store.MODEL_DIR / store.METADATA_FILE
    metadata = json.loads(path.read_text())
    if change == "split":
        metadata["split_id"] = "0" * 64
    elif change == "runtime":
        metadata["runtime"]["sklearn"] = "different"
    elif change == "model_split":
        metadata["models"]["bernoulli"]["split_id"] = "0" * 64
    elif change == "vocabulary":
        metadata["features"]["vocabulary_sha256"] = "0" * 64
    elif change == "extra":
        metadata["raw_text"] = "private"
    elif change == "date":
        metadata["trained_at"] = "2026-11-19T00:00:00"
    else:
        metadata["files"] = ["vectorizer", "multinomial", "bernoulli"]
    path.write_text(json.dumps(metadata))
    monkeypatch.setattr(
        store.joblib, "load", lambda *args: pytest.fail("Invalid metadata unpickled")
    )
    with pytest.raises(store.ModelArtifactError):
        store.load_models(corpus)


@pytest.mark.parametrize("filename", list(store.MODEL_FILES.values()) + [store.METADATA_FILE])
def test_missing_or_linked_artifacts_are_not_loaded(corpus, filename):
    store.prepare_models(corpus)
    path = corpus / store.MODEL_DIR / filename
    path.unlink()
    with pytest.raises((OSError, ValueError)):
        store.load_models(corpus)
    target = corpus / "keep"
    target.write_text("keep")
    path.symlink_to(target)
    with pytest.raises(store.ModelArtifactError):
        store.load_models(corpus)
    assert target.read_text() == "keep"


def test_stale_split_fails_before_artifact_load(corpus, monkeypatch):
    store.prepare_models(corpus)
    path = corpus / SPLIT_FILE
    data = json.loads(path.read_text())
    data["seed"] = 7
    path.write_text(json.dumps(data))
    monkeypatch.setattr(store.joblib, "load", lambda *args: pytest.fail("Stale input unpickled"))
    with pytest.raises(ValueError):
        store.load_models(corpus)


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("failure", ["replace", "validate"])
def test_failed_model_publication_restores_previous_complete_set(
    corpus, monkeypatch, existing, failure
):
    if existing:
        store.prepare_models(corpus)
    previous = snapshot(corpus) if existing else None
    real_load, real_replace = store.load_models, Path.replace
    calls = 0
    failed = False

    def load_with_fault(root):
        nonlocal calls
        calls += 1
        if (existing and calls == 1) or failure == "validate":
            raise store.ModelArtifactError("synthetic_validation_failure")
        return real_load(root)

    def replace_with_fault(self, target):
        nonlocal failed
        if (
            failure == "replace"
            and not failed
            and self.name == store.METADATA_FILE
            and ".models-" in str(self)
        ):
            failed = True
            raise OSError("synthetic publication failure")
        return real_replace(self, target)

    monkeypatch.setattr(store, "load_models", load_with_fault)
    monkeypatch.setattr(Path, "replace", replace_with_fault)
    with pytest.raises((OSError, store.ModelArtifactError)):
        store.prepare_models(corpus)
    if existing:
        assert snapshot(corpus) == previous
    else:
        assert all(
            not (corpus / store.MODEL_DIR / name).exists()
            for name in (*store.MODEL_FILES.values(), store.METADATA_FILE)
        )
    assert not list((corpus / store.MODEL_DIR).glob(".models-*"))
    assert not (corpus / "data/raw/.acquisition.lock").exists()


def test_cli_reports_counts_only_and_handles_corruption(corpus, monkeypatch, capsys):
    monkeypatch.setattr(cli, "ROOT", corpus)
    monkeypatch.setattr(sys, "argv", ["train_models", "run"])
    assert cli.main() == 0
    output = capsys.readouterr().out
    assert "private@" not in output and "private-member-" not in output
    monkeypatch.setattr(sys, "argv", ["train_models", "verify"])
    (corpus / store.MODEL_DIR / store.METADATA_FILE).write_text("invalid")
    assert cli.main() == 1
    assert (
        capsys.readouterr().err
        == "Model preparation failed: missing_invalid_or_incompatible_artifacts\n"
    )
