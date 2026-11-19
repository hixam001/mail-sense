"""One canonical vocabulary fitted exclusively on the frozen training partition."""

import hashlib
import json
from dataclasses import dataclass

import numpy as np
from scipy.sparse import csr_array, csr_matrix
from sklearn.feature_extraction.text import CountVectorizer

from app.services.corpus_split import load_split_dataset
from app.services.text_features import TOKEN_PATTERN, tokenizer_config


@dataclass
class FeatureSet:
    vectorizer: CountVectorizer
    train_counts: csr_matrix | csr_array
    test_counts: csr_matrix | csr_array
    train_ids: list[str]
    test_ids: list[str]
    train_labels: np.ndarray
    test_labels: np.ndarray
    vocabulary_sha256: str

    @property
    def feature_count(self):
        return len(self.vectorizer.vocabulary_)


def vocabulary_hash(vectorizer):
    mapping = [[word, int(index)] for word, index in sorted(vectorizer.vocabulary_.items())]
    return hashlib.sha256(json.dumps(mapping, separators=(",", ":")).encode()).hexdigest()


def fit_features(rows):
    ordered = sorted(rows, key=lambda row: row["message_id"])
    if len({row["message_id"] for row in ordered}) != len(ordered) or any(
        row.get("split") not in {"train", "test"} or row.get("label") not in {"ham", "spam"}
        for row in ordered
    ):
        raise ValueError("invalid_training_records")
    train = [row for row in ordered if row["split"] == "train"]
    test = [row for row in ordered if row["split"] == "test"]
    if not test or {row["label"] for row in train} != {"ham", "spam"}:
        raise ValueError("invalid_training_partitions")
    if {row["model_text"] for row in train} & {row["model_text"] for row in test}:
        raise ValueError("training_content_overlap")
    vectorizer = CountVectorizer(
        lowercase=True,
        token_pattern=TOKEN_PATTERN,
        strip_accents=None,
        stop_words=None,
        ngram_range=(1, 1),
        min_df=1,
        max_df=1.0,
        dtype=np.int64,
    )
    try:
        train_counts = vectorizer.fit_transform([row["model_text"] for row in train]).tocsr()
    except ValueError as error:
        raise ValueError("empty_training_vocabulary") from error
    test_counts = vectorizer.transform([row["model_text"] for row in test]).tocsr()
    return FeatureSet(
        vectorizer,
        train_counts,
        test_counts,
        [row["message_id"] for row in train],
        [row["message_id"] for row in test],
        np.array([row["label"] for row in train]),
        np.array([row["label"] for row in test]),
        vocabulary_hash(vectorizer),
    )


def build_features(root):
    rows, manifest = load_split_dataset(root)
    return fit_features(rows), manifest


def feature_metadata(features):
    return dict(
        tokenizer=tokenizer_config(),
        vocabulary_sha256=features.vocabulary_sha256,
        feature_count=features.feature_count,
        training_record_count=len(features.train_ids),
        test_record_count=len(features.test_ids),
    )
