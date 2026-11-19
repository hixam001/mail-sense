import copy
from types import SimpleNamespace

import numpy as np
import pytest
from test_model_features import feature_rows

from app.services.model_features import fit_features
from app.services.prediction import predict_text, word_explanation
from app.services.training import binary_presence, train_bernoulli, train_multinomial


@pytest.fixture
def loaded():
    features = fit_features(feature_rows())
    return SimpleNamespace(
        vectorizer=features.vectorizer,
        models=dict(multinomial=train_multinomial(features), bernoulli=train_bernoulli(features)),
    )


@pytest.mark.parametrize("text", ["offer offer prize", "project meeting", "unknownonlytoken"])
def test_full_explanation_reconciles_with_public_log_probabilities(loaded, text):
    result = predict_text(loaded, text, top_n=1)
    x = loaded.vectorizer.transform([text])
    for name, model in loaded.models.items():
        details = result["models"][name]
        logp = model.predict_log_proba(binary_presence(x) if name == "bernoulli" else x)[0]
        classes = model.classes_.tolist()
        expected = logp[classes.index("spam")] - logp[classes.index("ham")]
        assert details["log_odds"] == pytest.approx(expected, abs=1e-12)
        decomposed = details["class_prior_log_odds"] + details["absence_log_odds_contribution"]
        decomposed += details["other_present_log_odds"]
        decomposed += sum(t["log_odds_contribution"] for t in details["top_contributions"])
        assert decomposed == pytest.approx(expected, abs=1e-12)
        assert details["absence_terms_included"] == (name == "bernoulli")


def test_repetition_unknown_tokens_class_lookup_and_no_output_text_echo(loaded, capsys):
    first = predict_text(loaded, "offer")
    repeated = predict_text(loaded, "offer offer")
    assert first["models"]["bernoulli"]["log_odds"] == repeated["models"]["bernoulli"]["log_odds"]
    assert (
        first["models"]["multinomial"]["log_odds"] != repeated["models"]["multinomial"]["log_odds"]
    )
    unknown = predict_text(loaded, "unknownonlytoken")
    assert unknown["input"]["recognized_token_count"] == 0
    assert all(not model["top_contributions"] for model in unknown["models"].values())
    assert len(unknown["warnings"]) == 2
    reverse = copy.deepcopy(loaded)
    for model in reverse.models.values():
        model.classes_ = model.classes_[::-1]
        model.feature_log_prob_ = model.feature_log_prob_[::-1]
        model.class_log_prior_ = model.class_log_prior_[::-1]
    reordered = predict_text(reverse, "offer")
    for name in first["models"]:
        assert first["models"][name]["spam_probability"] == pytest.approx(
            reordered["models"][name]["spam_probability"]
        )
    assert "text" not in first["input"]
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("text", ["", "   ", "x" * 50001, None, 42, "\x00"])
def test_invalid_input_limits(loaded, text):
    with pytest.raises(ValueError):
        predict_text(loaded, text)


def test_maximum_input_and_word_weights(loaded):
    assert predict_text(loaded, "x" * 50000)["input"]["character_count"] == 50000
    weight = word_explanation(loaded, "offer", "multinomial")
    assert weight["in_vocabulary"] and weight["log_odds_when_present"] > 0
    bernoulli = word_explanation(loaded, "offer", "bernoulli")
    assert bernoulli["absence_terms_included"]
    assert np.isfinite(bernoulli["log_odds_when_absent"])
    missing = word_explanation(loaded, "unknownonlytoken", "bernoulli")
    assert missing["in_vocabulary"] is False and missing["log_odds_when_present"] is None
