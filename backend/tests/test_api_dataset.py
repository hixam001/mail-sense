import pytest
from fastapi.testclient import TestClient
from test_model_store import corpus as corpus

from app.main import create_app
from app.services.descriptive import descriptive_statistics
from app.services.distributions import distributions


@pytest.mark.parametrize("scope,total", [("all", 25), ("train", 20), ("test", 5)])
def test_summary_reconciles_scoped_counts_without_models(corpus, scope, total):
    with TestClient(create_app(corpus), base_url="http://127.0.0.1") as client:
        response = client.get("/api/v1/dataset/summary", params={"scope": scope})
        assert response.status_code == 200
        result = response.json()
        assert result["total"] == total == sum(result["class_counts"].values())
        assert sum(result["source_groups"].values()) == total
        assert sum(result["class_proportions"].values()) == pytest.approx(1)
        assert result["exclusion_scope"] == "source_corpus_before_split"
        assert len(result["source_archives"]) == 5
        assert "model_text" not in response.text and "source_file" not in response.text
        assert "private@example" not in response.text


def test_api_numeric_and_word_aggregates_match_verified_services(corpus):
    app = create_app(corpus)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        rows, _, _, _ = app.state.mail_sense.dataset_snapshot()
        stats = client.get(
            "/api/v1/dataset/statistics", params={"scope": "test", "metric": "token_count"}
        )
        assert stats.status_code == 200
        assert stats.json() == descriptive_statistics(rows, "test", "token_count")
        numeric = client.get(
            "/api/v1/dataset/distributions",
            params={"scope": "train", "metric": "character_count", "class_label": "ham"},
        ).json()
        assert sum(item["count"] for item in numeric["bins"]) == 12
        assert (
            numeric["boxplot"] == distributions(rows, "train", "character_count", "ham")["boxplot"]
        )
        words = client.get(
            "/api/v1/dataset/distributions", params={"metric": "top_words", "top_n": 3}
        )
        assert words.status_code == 200
        assert words.json()["items"] == distributions(rows, metric="top_words", top_n=3)["items"]


@pytest.mark.parametrize(
    "path,params",
    [
        ("summary", {"scope": "invalid"}),
        ("statistics", {"metric": "invalid"}),
        ("distributions", {}),
        ("distributions", {"metric": "invalid"}),
        ("distributions", {"metric": "top_words", "top_n": 31}),
        ("distributions", {"metric": "top_words", "class_label": "invalid"}),
    ],
)
def test_bad_dataset_queries_are_redacted_422(tmp_path, path, params):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        result = client.get(f"/api/v1/dataset/{path}", params=params)
        assert result.status_code == 422 and result.json()["error"]["code"] == "INVALID_INPUT"


@pytest.mark.parametrize("path", ["summary", "statistics", "distributions?metric=top_words"])
def test_missing_dataset_returns_safe_503(tmp_path, path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        response = client.get(f"/api/v1/dataset/{path}")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DATASET_UNAVAILABLE"
        assert str(tmp_path) not in response.text
