"""Cross-route public contract, resource isolation and schema coverage."""

import pytest
from fastapi.testclient import TestClient
from test_model_store import corpus as corpus  # noqa: F401

from app.main import create_app
from app.services.evaluation import EVALUATION_FILE, prepare_evaluation
from app.services.model_store import prepare_models

CASES = [
    ("GET", "/health", {}, {"status", "dataset_ready", "models_ready", "evaluation_ready"}),
    ("GET", "/dataset/summary", {}, {"total", "class_counts", "source_archives", "scope"}),
    ("GET", "/dataset/statistics", {}, {"metric", "unit", "groups", "scope"}),
    ("GET", "/dataset/distributions", {"metric": "token_count"}, {"bins", "boxplot", "items"}),
    ("GET", "/probability/word", {"word": "easy_ham"}, {"counts", "probabilities", "total"}),
    ("GET", "/probability/distributions", {"word": "easy_ham"}, {"bernoulli_p", "binomial_pmf"}),
    (
        "POST",
        "/statistics/hypothesis-test",
        {"word": "easy_ham"},
        {"observed", "expected", "reject_null"},
    ),
    ("GET", "/statistics/confidence-interval", {}, {"lower", "upper", "sample_size"}),
    ("POST", "/predict", {"text": "Synthetic easy_ham"}, {"models", "agreement", "warnings"}),
    (
        "GET",
        "/models/metrics",
        {"model": "multinomial"},
        {"confusion_matrix", "accuracy", "recall"},
    ),
    ("GET", "/models/comparison", {}, {"models", "same_test_ids", "test_ids_sha256"}),
    (
        "GET",
        "/models/explanations",
        {"word": "easy_ham", "model": "bernoulli"},
        {"in_vocabulary", "log_odds_when_absent"},
    ),
]


@pytest.fixture
def client(corpus):
    prepare_models(corpus)
    prepare_evaluation(corpus)
    with TestClient(create_app(corpus), base_url="http://127.0.0.1") as session:
        yield session


@pytest.mark.parametrize("method,path,parameters,keys", CASES)
def test_all_twelve_public_routes_and_openapi(client, method, path, parameters, keys):
    response = client.request(
        method, "/api/v1" + path, **{"json" if method == "POST" else "params": parameters}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert keys <= response.json().keys()
    operation = client.get("/openapi.json").json()["paths"]["/api/v1" + path][method.lower()]
    assert "$ref" in operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert operation["responses"]["503"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "ErrorEnvelope"
    )


@pytest.mark.parametrize("method,path,parameters,keys", CASES[1:])
def test_missing_resources_are_uniform_503(tmp_path, method, path, parameters, keys):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        response = client.request(
            method, "/api/v1" + path, **{"json" if method == "POST" else "params": parameters}
        )
    assert response.status_code == 503
    assert set(response.json()) == {"error"}
    assert set(response.json()["error"]) == {"code", "message", "details"}
    assert str(tmp_path) not in response.text


def test_aggregate_scopes_and_identities_reconcile(client):
    summaries = {
        s: client.get("/api/v1/dataset/summary", params={"scope": s}).json()
        for s in ("all", "train", "test")
    }
    assert summaries["all"]["total"] == summaries["train"]["total"] + summaries["test"]["total"]
    for scope, summary in summaries.items():
        assert sum(summary["class_counts"].values()) == summary["total"]
        assert sum(summary["source_groups"].values()) == summary["total"]
        words = client.get(
            "/api/v1/probability/word", params={"word": "easy_ham", "scope": scope}
        ).json()
        assert sum(words["counts"].values()) == summary["total"]
        for label in ("ham", "spam"):
            assert (
                sum(words["counts"][f"{label}_{p}"] for p in ("present", "absent"))
                == summary["class_counts"][label]
            )
    comparison = client.get("/api/v1/models/comparison").json()
    assert comparison["split_id"] == summaries["all"]["split_id"]
    assert comparison["test_count"] == summaries["test"]["total"]


def test_stale_evaluation_does_not_disable_data_or_inference(client, corpus):
    (corpus / EVALUATION_FILE).write_text('{"schema_version": 999}')
    health = client.get("/api/v1/health").json()
    assert health["status"] == "degraded" and not health["evaluation_ready"]
    assert health["dataset_ready"] and all(health["models_ready"].values())
    assert client.get("/api/v1/models/comparison").status_code == 503
    assert client.get("/api/v1/dataset/summary").status_code == 200
    assert client.post("/api/v1/predict", json={"text": "synthetic example"}).status_code == 200
