from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.numerical_verification import teaching_records


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path)
    app.state.mail_sense = SimpleNamespace(
        dataset_snapshot=lambda: (teaching_records(), {}, {}, {})
    )
    with TestClient(app) as session:
        yield session


def test_known_probability_binomial_and_t05_values_through_http(client):
    probability = client.get("/api/v1/probability/word", params={"word": "FREE"})
    assert probability.status_code == 200
    body = probability.json()
    assert body["total"] == 1000 and body["word"] == "free"
    assert body["probabilities"]["p_spam_given_word"] == dict(
        numerator=180, denominator=250, value=0.72
    )
    binomial = client.get("/api/v1/probability/distributions", params={"word": "free"}).json()
    assert binomial["bernoulli_p"] == 0.25
    assert binomial["binomial_pmf"] == pytest.approx(0.1877117156982422)
    test = client.post("/api/v1/statistics/hypothesis-test", json={"word": "free"})
    assert test.status_code == 200
    assert test.json()["observed"] == [[180, 120], [70, 630]]
    assert test.json()["chi_square"] == 280 and test.json()["reject_null"] is True
    interval = client.get("/api/v1/statistics/confidence-interval").json()
    assert interval["spam_count"] == 300 and interval["sample_size"] == 1000
    assert interval["lower"] == pytest.approx(0.2724, abs=0.00005)


def test_absent_words_and_unsuitable_test_return_null_decisions(client):
    probability = client.get("/api/v1/probability/word", params={"word": "unseenonlytoken"}).json()
    assert probability["probabilities"]["p_spam_given_word"]["value"] is None
    test = client.post(
        "/api/v1/statistics/hypothesis-test", json={"word": "unseenonlytoken"}
    ).json()
    assert test["chi_square"] is None and test["reject_null"] is None and test["warnings"]


@pytest.mark.parametrize(
    "path,params",
    [
        ("probability/word", {}),
        ("probability/word", {"word": "free prize"}),
        ("probability/word", {"word": "a"}),
        ("probability/word", {"word": "private@example.invalid"}),
        ("probability/distributions", {"word": "free", "trials": 0}),
        ("probability/distributions", {"word": "free", "trials": 101}),
        ("probability/distributions", {"word": "free", "trials": 2, "successes": 3}),
        ("statistics/confidence-interval", {"confidence": 0.5}),
        ("statistics/confidence-interval", {"confidence": "nan"}),
    ],
)
def test_invalid_probability_queries_are_safe(client, path, params):
    response = client.get("/api/v1/" + path, params=params)
    assert response.status_code == 422 and response.json()["error"]["code"] == "INVALID_INPUT"
    assert "private@example.invalid" not in response.text


@pytest.mark.parametrize(
    "payload",
    [
        {"word": "free", "alpha": 0},
        {"word": "free", "alpha": 1},
        {"word": "free prize"},
        {"word": "free", "scope": "invalid"},
        {"word": "free", "file": "/tmp/private/path"},
    ],
)
def test_invalid_hypothesis_body_is_redacted(client, payload):
    response = client.post("/api/v1/statistics/hypothesis-test", json=payload)
    assert response.status_code == 422
    assert "/tmp/private" not in response.text


def test_missing_and_empty_data_fail_safely(tmp_path):
    app = create_app(tmp_path)
    with TestClient(app) as session:
        assert session.get("/api/v1/probability/word", params={"word": "free"}).status_code == 503
        assert (
            session.post("/api/v1/statistics/hypothesis-test", json={"word": "free"}).status_code
            == 503
        )
        app.state.mail_sense = SimpleNamespace(dataset_snapshot=lambda: ([], {}, {}, {}))
        response = session.get("/api/v1/statistics/confidence-interval")
        assert response.status_code == 503 and response.json()["error"]["code"] == "EMPTY_SUBSET"
