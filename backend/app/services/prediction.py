"""Transient dual-model prediction and faithful signed log-odds explanations."""

import numpy as np

from app.services.mail_parser import normalize_text
from app.services.model_store import load_models
from app.services.probability import normalize_word
from app.services.training import binary_presence


def _direction(value):
    return "spam" if value > 0 else "ham" if value < 0 else "neutral"


def predict_text(loaded, text, top_n=10):
    if not isinstance(text, str):
        raise ValueError("invalid_text")
    trimmed = text.strip()
    if not trimmed or len(trimmed) > 50_000:
        raise ValueError("invalid_text_length")
    normalized = normalize_text(trimmed)
    if not normalized:
        raise ValueError("empty_normalized_text")
    if type(top_n) is not int or not 1 <= top_n <= 20:
        raise ValueError("invalid_explanation_limit")
    counts = loaded.vectorizer.transform([normalized]).tocsr()
    names = loaded.vectorizer.get_feature_names_out()
    indices, frequencies = counts.indices, counts.data
    results = {}
    for name, model in loaded.models.items():
        classes = model.classes_.tolist()
        spam, ham = classes.index("spam"), classes.index("ham")
        prior = float(model.class_log_prior_[spam] - model.class_log_prior_[ham])
        weight = model.feature_log_prob_[spam] - model.feature_log_prob_[ham]
        absence = 0.0
        if name == "bernoulli":
            absent_weights = np.log1p(-np.exp(model.feature_log_prob_[spam])) - np.log1p(
                -np.exp(model.feature_log_prob_[ham])
            )
            absence = float(absent_weights.sum() - absent_weights[indices].sum())
            values = weight[indices]
            x = binary_presence(counts)
        else:
            values = weight[indices] * frequencies
            x = counts
        terms = [
            dict(
                token=str(names[index]),
                presence="present",
                log_odds_contribution=float(value),
                direction=_direction(value),
            )
            for index, value in zip(indices, values, strict=True)
        ]
        terms.sort(key=lambda item: (-abs(item["log_odds_contribution"]), item["token"]))
        top = terms[:top_n]
        total = float(values.sum())
        probabilities = model.predict_proba(x)[0]
        results[name] = dict(
            prediction=str(classes[int(np.argmax(probabilities))]),
            spam_probability=float(probabilities[spam]),
            top_contributions=top,
            class_prior_log_odds=prior,
            absence_terms_included=name == "bernoulli",
            absence_log_odds_contribution=absence,
            other_present_log_odds=total - sum(term["log_odds_contribution"] for term in top),
            log_odds=prior + total + absence,
        )
    warnings = ["Probabilities are model estimates, not calibrated certainty."]
    if not len(indices):
        warnings.append("No known tokens; results use class priors and Bernoulli absence effects.")
    return dict(
        input=dict(character_count=len(trimmed), recognized_token_count=int(counts.sum())),
        models=results,
        agreement=len({item["prediction"] for item in results.values()}) == 1,
        warnings=warnings,
    )


def predict(root, text):
    return predict_text(load_models(root), text)


def word_explanation(loaded, word, model):
    if model not in {"multinomial", "bernoulli"}:
        raise ValueError("invalid_model")
    word = normalize_word(word)
    estimator = loaded.models[model]
    classes = estimator.classes_.tolist()
    spam, ham = classes.index("spam"), classes.index("ham")
    index = loaded.vectorizer.vocabulary_.get(word)
    weight = (
        float(estimator.feature_log_prob_[spam, index] - estimator.feature_log_prob_[ham, index])
        if index is not None
        else None
    )
    result = dict(
        model=model,
        word=word,
        in_vocabulary=index is not None,
        log_odds_when_present=weight,
        interpretation=(
            f"Present token favors {_direction(weight)}; this does not imply "
            "causation or determine the full prediction."
            if weight is not None
            else "Word is absent from the fitted vocabulary; no weight is available."
        ),
    )
    if model == "bernoulli":
        result.update(
            absence_terms_included=True,
            log_odds_when_absent=float(
                np.log1p(-np.exp(estimator.feature_log_prob_[spam, index]))
                - np.log1p(-np.exp(estimator.feature_log_prob_[ham, index]))
            )
            if index is not None
            else None,
        )
    return result


def explain_word(root, word, model):
    return word_explanation(load_models(root), word, model)
