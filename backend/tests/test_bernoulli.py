import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.special import softmax
from test_model_features import feature_rows

from app.services.model_features import fit_features
from app.services.training import binary_presence, train_bernoulli, train_multinomial


def test_manual_bernoulli_likelihood_and_absent_terms_match():
    rows = feature_rows()
    rows[0]["model_text"] = "offer offer prize winner"
    features = fit_features(rows)
    original = features.train_counts.copy()
    model = train_bernoulli(features)
    dense = (features.train_counts.toarray() > 0).astype(int)
    for index, label in enumerate(model.classes_):
        selected = dense[features.train_labels == label]
        theta = (selected.sum(axis=0) + 1) / (len(selected) + 2)
        np.testing.assert_allclose(np.exp(model.feature_log_prob_[index]), theta)
    sample = binary_presence(features.vectorizer.transform(["offer offer"]))
    theta = np.exp(model.feature_log_prob_)
    x = sample.toarray()
    manual = x @ np.log(theta).T + (1 - x) @ np.log1p(-theta).T + model.class_log_prior_
    np.testing.assert_allclose(model.predict_proba(sample), softmax(manual, axis=1))
    assert (features.train_counts != original).nnz == 0
    single = binary_presence(features.vectorizer.transform(["offer"]))
    np.testing.assert_allclose(model.predict_proba(single), model.predict_proba(sample))
    assert model.binarize is None and model.alpha == 1


def test_same_vocabulary_counts_preserved_and_no_holdout_label_use():
    features = fit_features(feature_rows())
    first = train_multinomial(features)
    bernoulli = train_bernoulli(features)
    features.test_labels[:] = "ham"
    again = train_bernoulli(features)
    np.testing.assert_array_equal(bernoulli.feature_log_prob_, again.feature_log_prob_)
    np.testing.assert_array_equal(
        first.feature_log_prob_, train_multinomial(features).feature_log_prob_
    )
    assert bernoulli.n_features_in_ == first.n_features_in_ == features.feature_count


def test_sparse_zero_and_invalid_count_handling():
    counts = csr_matrix(([0, 2], ([0, 0], [0, 1])), shape=(1, 3))
    assert binary_presence(counts).toarray().tolist() == [[0, 1, 0]]
    for bad in (csr_matrix([[-1, 2]]), csr_matrix([[float("nan"), 1]]), np.array([[1, 2]])):
        with pytest.raises(ValueError):
            binary_presence(bad)
