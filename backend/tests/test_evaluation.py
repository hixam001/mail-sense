import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import confusion_matrix
from sklearn.naive_bayes import BernoulliNB, MultinomialNB
from test_model_store import corpus as corpus

from app.services.evaluation import (
    EVALUATION_FILE,
    build_evaluation,
    classification_metrics,
    prepare_evaluation,
    verify_evaluation,
)
from app.services.model_store import prepare_models


def test_t22_confusion_metrics_match_known_manual_example():
    actual = ["spam"] * 60 + ["ham"] * 140
    predicted = ["spam"] * 50 + ["ham"] * 10 + ["spam"] * 5 + ["ham"] * 135
    result = classification_metrics(actual, predicted)
    assert result["confusion_matrix"] == dict(tn=135, fp=5, fn=10, tp=50)
    assert result["accuracy"] == 0.925
    assert result["precision"] == pytest.approx(50 / 55)
    assert result["recall"] == pytest.approx(50 / 60)
    assert result["f1"] == pytest.approx(100 / 115)
    assert result["false_positive_rate"] == pytest.approx(5 / 140)
    np.testing.assert_array_equal(
        confusion_matrix(actual, predicted, labels=["ham", "spam"]), [[135, 5], [10, 50]]
    )


def test_zero_denominators_and_bad_labels_are_truthful():
    result = classification_metrics(["ham"], ["ham"])
    assert result["accuracy"] == 1 and result["precision"] is None
    assert result["recall"] is None and result["notes"]
    assert classification_metrics([], [])["accuracy"] is None
    for actual, predicted in [(["ham"], []), (["unknown"], ["ham"])]:
        with pytest.raises(ValueError):
            classification_metrics(actual, predicted)


def test_evaluation_uses_same_ids_without_any_refitting(corpus, monkeypatch):
    prepare_models(corpus)

    def forbidden(*args, **kwargs):
        pytest.fail("Evaluation fitted a model or vocabulary")

    for cls in (CountVectorizer, MultinomialNB, BernoulliNB):
        monkeypatch.setattr(cls, "fit", forbidden)
    monkeypatch.setattr(CountVectorizer, "fit_transform", forbidden)
    report = build_evaluation(corpus)
    assert report["same_test_ids"]
    assert len({m["test_ids_sha256"] for m in report["models"].values()}) == 1
    for metrics in report["models"].values():
        assert sum(metrics["confusion_matrix"].values()) == report["test_count"]
        assert metrics["positive_class"] == "spam"


def test_report_is_reproducible_public_and_tamper_detected(corpus):
    prepare_models(corpus)
    first = prepare_evaluation(corpus)
    path = corpus / EVALUATION_FILE
    original = path.read_bytes()
    assert prepare_evaluation(corpus) == first and path.read_bytes() == original
    assert verify_evaluation(corpus) == first
    assert b"private-member-" not in original and b"private@" not in original
    report = json.loads(original)
    report["models"]["bernoulli"]["test_ids_sha256"] = "0" * 64
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="evaluation_report_mismatch"):
        verify_evaluation(corpus)


def test_failed_report_publication_preserves_previous_metrics(corpus, monkeypatch):
    prepare_models(corpus)
    prepare_evaluation(corpus)
    path = corpus / EVALUATION_FILE
    original = path.read_bytes()
    replace = Path.replace

    def fail(self, target):
        if ".evaluation-" in str(self):
            raise OSError("synthetic publication failure")
        return replace(self, target)

    monkeypatch.setattr(Path, "replace", fail)
    with pytest.raises(OSError):
        prepare_evaluation(corpus)
    assert path.read_bytes() == original
    assert not (corpus / "data/raw/.acquisition.lock").exists()
