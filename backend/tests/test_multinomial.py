import numpy as np
from scipy.special import softmax
from test_model_features import feature_rows

from app.services.model_features import fit_features
from app.services.training import train_multinomial


def test_laplace_counts_and_probabilities_match_manual_formula():
    features = fit_features(feature_rows())
    model = train_multinomial(features)
    dense = features.train_counts.toarray()
    for index, label in enumerate(model.classes_):
        counts = dense[features.train_labels == label].sum(axis=0)
        expected = (counts + 1) / (counts.sum() + features.feature_count)
        np.testing.assert_allclose(np.exp(model.feature_log_prob_[index]), expected)
    sample = features.vectorizer.transform(["offer prize"])
    manual = softmax(sample.toarray() @ model.feature_log_prob_.T + model.class_log_prior_, axis=1)
    np.testing.assert_allclose(model.predict_proba(sample), manual)
    assert model.predict(sample).tolist() == ["spam"]
    assert model.alpha == 1


def test_heldout_labels_do_not_influence_multinomial_parameters():
    features = fit_features(feature_rows())
    first = train_multinomial(features)
    features.test_labels[:] = "ham"
    second = train_multinomial(features)
    np.testing.assert_array_equal(first.feature_log_prob_, second.feature_log_prob_)
    np.testing.assert_array_equal(first.class_log_prior_, second.class_log_prior_)
