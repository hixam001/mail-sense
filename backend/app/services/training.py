"""Approved Naive Bayes estimators fitted only on the shared training partition."""

import numpy as np
from scipy.sparse import issparse
from sklearn.naive_bayes import BernoulliNB, MultinomialNB


def train_multinomial(features):
    model = MultinomialNB(alpha=1.0, force_alpha=True, fit_prior=True)
    model.fit(features.train_counts, features.train_labels)
    if list(model.classes_) != ["ham", "spam"]:
        raise ValueError("invalid_model_classes")
    return model


def binary_presence(counts):
    if not issparse(counts) or not np.isfinite(counts.data).all() or np.any(counts.data < 0):
        raise ValueError("invalid_count_matrix")
    return (counts > 0).astype(np.int64).tocsr()


def train_bernoulli(features):
    model = BernoulliNB(alpha=1.0, force_alpha=True, fit_prior=True, binarize=None)
    model.fit(binary_presence(features.train_counts), features.train_labels)
    if list(model.classes_) != ["ham", "spam"]:
        raise ValueError("invalid_model_classes")
    return model
