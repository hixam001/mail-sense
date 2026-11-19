import hashlib

import pytest
from fastapi.testclient import TestClient
from test_model_store import corpus as corpus  # noqa: F401

from app.main import create_app
from app.services.evaluation import prepare_evaluation
from app.services.model_store import prepare_models
from app.services.prediction import predict_text


@pytest.fixture
def client(corpus):
    prepare_models(corpus)
    prepare_evaluation(corpus)
    with TestClient(create_app(corpus)) as session:
        yield session


def test_prediction_matches_service_and_score_decomposition(client, corpus):
    paths = [p for p in corpus.rglob("*") if p.is_file()]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    text = "  easy_ham privateuniqueexample@invalid.example  "
    response = client.post("/api/v1/predict", json={"text": text})
    assert response.status_code == 200
    body = response.json()
    assert body == predict_text(client.app.state.mail_sense.model_snapshot(), text)
    assert text.strip() not in response.text
    for name, result in body["models"].items():
        assert result["absence_terms_included"] == (name == "bernoulli")
        assert result["log_odds"] == pytest.approx(
            result["class_prior_log_odds"]
            + sum(t["log_odds_contribution"] for t in result["top_contributions"])
            + result["other_present_log_odds"]
            + result["absence_log_odds_contribution"]
        )
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths} == before
    assert set(p for p in corpus.rglob("*") if p.is_file()) == set(paths)


@pytest.mark.parametrize("text", ["", "  \n", None, 123, "x" * 50_001, "\x00\x01"])
def test_invalid_text_safe_errors(client, text):
    response = client.post("/api/v1/predict", json={"text": text})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"
    assert "x" * 100 not in response.text


def test_text_boundary_extra_fields_and_unknown_vocabulary(client):
    assert (
        client.post("/api/v1/predict", json={"text": " " + "x" * 50_000 + " "}).status_code == 200
    )
    response = client.post("/api/v1/predict", json={"text": "novocabularytoken"}).json()
    assert response["input"]["recognized_token_count"] == 0
    assert len(response["warnings"]) == 2
    assert all(not r["top_contributions"] for r in response["models"].values())
    extra = client.post("/api/v1/predict", json={"text": "word", "path": "/tmp/private"})
    assert extra.status_code == 422 and "/tmp/private" not in extra.text


def test_verified_metrics_and_explanations(client):
    comparison = client.get("/api/v1/models/comparison")
    assert comparison.status_code == 200
    body = comparison.json()
    assert body["same_test_ids"]
    for name in ("multinomial", "bernoulli"):
        metric = client.get("/api/v1/models/metrics", params={"model": name})
        assert metric.status_code == 200 and metric.json() == body["models"][name]
        assert metric.json()["test_ids_sha256"] == body["test_ids_sha256"]
        explanation = client.get(
            "/api/v1/models/explanations", params={"model": name, "word": "EASY_HAM"}
        ).json()
        assert explanation["in_vocabulary"] and explanation["word"] == "easy_ham"
        assert explanation["absence_terms_included"] == (name == "bernoulli")
        unknown = client.get(
            "/api/v1/models/explanations", params={"model": name, "word": "novocabularytoken"}
        ).json()
        assert not unknown["in_vocabulary"] and unknown["log_odds_when_present"] is None


@pytest.mark.parametrize(
    "path,params",
    [
        ("metrics", {}),
        ("metrics", {"model": "Multinomial"}),
        ("explanations", {"model": "bernoulli", "word": "two words"}),
    ],
)
def test_invalid_model_queries(client, path, params):
    assert client.get("/api/v1/models/" + path, params=params).status_code == 422


def test_missing_artifacts_are_safe(tmp_path):
    with TestClient(create_app(tmp_path)) as session:
        assert session.post("/api/v1/predict", json={"text": "meeting"}).status_code == 503
        for path, params in [
            ("metrics", {"model": "multinomial"}),
            ("comparison", {}),
            ("explanations", {"model": "bernoulli", "word": "free"}),
        ]:
            response = session.get("/api/v1/models/" + path, params=params)
            assert response.status_code == 503 and str(tmp_path) not in response.text
