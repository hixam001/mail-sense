"""Approved Naive Bayes estimators fitted only on the shared training partition."""

from sklearn.naive_bayes import MultinomialNB


def train_multinomial(features):
    model = MultinomialNB(alpha=1.0, force_alpha=True, fit_prior=True)
    model.fit(features.train_counts, features.train_labels)
    if list(model.classes_) != ["ham", "spam"]:
        raise ValueError("invalid_model_classes")
    return model
