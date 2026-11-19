import os

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from test_model_store import corpus as corpus

from app.api.errors import ApiError
from app.core import state as state_module
from app.main import create_app
from app.services.corpus_dataset import DATASET_FILE
from app.services.evaluation import prepare_evaluation
from app.services.model_store import MODEL_DIR, MODEL_FILES, prepare_models


def test_missing_artifacts_degrade_and_use_safe_errors(tmp_path):
    app = create_app(tmp_path)
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "degraded" and result["dataset_ready"] is False
        assert result["models_ready"] == dict(multinomial=False, bernoulli=False)
        assert result["split_id"] is None
        missing = client.get("/private/path/example")
        assert missing.status_code == 404 and missing.json()["error"]["code"] == "NOT_FOUND"
        assert "/private/path" not in missing.text and str(tmp_path) not in missing.text
    with pytest.raises(ApiError) as error:
        app.state.mail_sense.dataset_snapshot()
    assert error.value.status == 503


def test_data_remains_available_when_models_are_missing(corpus):
    with TestClient(create_app(corpus)) as client:
        result = client.get("/api/v1/health").json()
        assert result["dataset_ready"] and result["split_id"]
        assert result["models_ready"] == dict(multinomial=False, bernoulli=False)
        assert result["status"] == "degraded"


def test_actual_bundle_readiness_invalidates_on_corruption_and_recovers(corpus):
    prepare_models(corpus)
    prepare_evaluation(corpus)
    with TestClient(create_app(corpus)) as client:
        first = client.get("/api/v1/health").json()
        assert first["status"] == "ready" and first["evaluation_ready"]
        path = corpus / MODEL_DIR / MODEL_FILES["bernoulli"]
        original = path.read_bytes()
        path.write_bytes(original + b"changed")
        degraded = client.get("/api/v1/health").json()
        assert degraded["dataset_ready"] and degraded["status"] == "degraded"
        assert not any(degraded["models_ready"].values())
        path.write_bytes(original)
        assert client.get("/api/v1/health").json()["status"] == "ready"


def test_cache_uses_content_hashes_instead_of_size_or_timestamp(corpus, monkeypatch):
    original_load = state_module.load_split_dataset
    calls = []

    def counted(root):
        calls.append(root)
        return original_load(root)

    monkeypatch.setattr(state_module, "load_split_dataset", counted)
    with TestClient(create_app(corpus)) as client:
        assert client.get("/api/v1/health").json()["dataset_ready"]
        assert client.get("/api/v1/health").json()["dataset_ready"]
        assert len(calls) == 1
        path = corpus / DATASET_FILE
        original = path.read_bytes()
        stat = path.stat()
        changed = original.replace(b"Fixture", b"FiXture", 1)
        assert len(changed) == len(original) and changed != original
        path.write_bytes(changed)
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        assert client.get("/api/v1/health").json()["dataset_ready"] is False
        path.write_bytes(original)
        assert client.get("/api/v1/health").json()["dataset_ready"]
        assert len(calls) == 3


def test_validation_and_unexpected_errors_do_not_echo_input_or_paths(tmp_path):
    app = create_app(tmp_path)

    class Probe(BaseModel):
        word: int

    @app.post("/validation-probe")
    def validation(value: Probe):
        return value

    @app.get("/unexpected-probe")
    def unexpected():
        raise RuntimeError("private@example.invalid /tmp/private/path")

    with TestClient(app, raise_server_exceptions=False) as client:
        invalid = client.post("/validation-probe", json={"word": "private@example.invalid"})
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "INVALID_INPUT"
        assert (
            "private@example" not in invalid.text
            and "input" not in invalid.json()["error"]["details"]
        )
        failed = client.get("/unexpected-probe")
        assert failed.status_code == 500 and failed.json()["error"]["code"] == "INTERNAL_ERROR"
        assert "private@example" not in failed.text and "/tmp/" not in failed.text
