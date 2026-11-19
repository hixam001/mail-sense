"""Synthetic dependency compatibility checks, not measured corpus/model results."""

import json
import platform
import tomllib
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from scipy.stats import chi2_contingency
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import BernoulliNB, MultinomialNB

from app.main import app

ROOT = Path(__file__).resolve().parents[2]


def test_pinned_python_runtime():
    assert platform.python_version() == (ROOT / ".python-version").read_text().strip()


def test_release_versions_match_package_locks_and_api():
    backend = tomllib.loads((ROOT / "backend/pyproject.toml").read_text())
    python_lock = tomllib.loads((ROOT / "backend/uv.lock").read_text())
    frontend = json.loads((ROOT / "frontend/package.json").read_text())
    npm_lock = json.loads((ROOT / "frontend/package-lock.json").read_text())
    locked_backend = next(
        package for package in python_lock["package"] if package["name"] == "mailsense-backend"
    )
    assert {
        backend["project"]["version"],
        locked_backend["version"],
        frontend["version"],
        npm_lock["version"],
        npm_lock["packages"][""]["version"],
        app.version,
    } == {"1.0.0"}


def test_native_statistics_libraries():
    values = pd.Series(np.array([2, 4, 4, 6]))
    assert values.mean() == 4
    assert values.var(ddof=1) == pytest.approx(8 / 3)
    result = chi2_contingency([[180, 120], [70, 630]], correction=False)
    assert result.statistic == pytest.approx(280)
    assert result.dof == 1


@pytest.mark.parametrize("classifier", [MultinomialNB, BernoulliNB])
def test_model_dependencies_and_artifact_roundtrip(classifier, tmp_path):
    texts = [
        "offer prize winner",
        "free prize offer",
        "meeting project notes",
        "project meeting agenda",
    ]
    labels = np.array([1, 1, 0, 0])
    vocabulary = CountVectorizer()
    matrix = vocabulary.fit_transform(texts)
    model = classifier(alpha=1.0).fit(matrix, labels)
    sample = vocabulary.transform(["meeting agenda"])
    expected = model.predict_proba(sample)
    assert expected.shape == (1, 2)
    assert np.isfinite(expected).all()
    assert expected.sum() == pytest.approx(1)
    artifact = tmp_path / "synthetic-model.joblib"
    joblib.dump((vocabulary, model), artifact)
    restored_vocabulary, restored_model = joblib.load(artifact)
    np.testing.assert_allclose(
        restored_model.predict_proba(restored_vocabulary.transform(["meeting agenda"])), expected
    )


def test_fastapi_client_dependency_compatibility():
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get("/").json() == {"message": "MailSense API is running."}
        assert {"/", "/api/v1/health"}.issubset(client.get("/openapi.json").json()["paths"])
        assert client.get("/api/v1/health").status_code == 200
