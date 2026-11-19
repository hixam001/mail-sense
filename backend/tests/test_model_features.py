import hashlib

import numpy as np
import pytest

from app.services.model_features import fit_features
from app.services.text_features import tokenize


def feature_rows():
    samples = [
        ("spam", "train", "offer prize winner"),
        ("spam", "train", "free prize offer"),
        ("ham", "train", "meeting project notes"),
        ("ham", "train", "project meeting agenda"),
        ("spam", "test", "heldoutonly offer"),
        ("ham", "test", "unseenonly project"),
    ]
    return [
        dict(
            message_id=hashlib.sha256(str(i).encode()).hexdigest(),
            label=label,
            split=split,
            model_text=text,
        )
        for i, (label, split, text) in enumerate(samples)
    ]


def test_t19_vocabulary_excludes_heldout_only_words_and_keeps_fixed_columns():
    result = fit_features(feature_rows())
    assert "heldoutonly" not in result.vectorizer.vocabulary_
    assert "unseenonly" not in result.vectorizer.vocabulary_
    assert result.train_counts.shape[1] == result.test_counts.shape[1] == result.feature_count
    assert result.train_counts.shape[0] == 4 and result.test_counts.shape[0] == 2
    assert result.vectorizer.build_analyzer()("FREE free e-mail") == tokenize("FREE free e-mail")


def test_holdout_mutations_do_not_change_training_features_or_vocabulary():
    rows = feature_rows()
    first = fit_features(rows)
    for row in rows:
        if row["split"] == "test":
            row["model_text"] = "entirely different heldout words"
            row["label"] = "ham"
    second = fit_features(list(reversed(rows)))
    assert first.vocabulary_sha256 == second.vocabulary_sha256
    assert first.train_ids == second.train_ids
    np.testing.assert_array_equal(first.train_counts.toarray(), second.train_counts.toarray())


@pytest.mark.parametrize(
    "problem", ["overlap", "duplicate_id", "bad_split", "empty_words", "no_test"]
)
def test_invalid_training_boundaries(problem):
    rows = feature_rows()
    if problem == "overlap":
        rows[-1]["model_text"] = rows[0]["model_text"]
    elif problem == "duplicate_id":
        rows[-1]["message_id"] = rows[0]["message_id"]
    elif problem == "bad_split":
        rows[0]["split"] = "validation"
    elif problem == "empty_words":
        for row in rows:
            if row["split"] == "train":
                row["model_text"] = "a !"
    else:
        rows = [row for row in rows if row["split"] == "train"]
    with pytest.raises(ValueError):
        fit_features(rows)
