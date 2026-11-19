"""Empirical word-document probabilities with visible denominators and no smoothing."""

import unicodedata

from app.services.analytics_data import select_records
from app.services.corpus_split import load_split_dataset
from app.services.text_features import tokenize


def normalize_word(word):
    if not isinstance(word, str) or not 1 <= len(word) <= 64:
        raise ValueError("invalid_word")
    normalized = unicodedata.normalize("NFC", word.strip()).lower()
    if tokenize(normalized) != [normalized]:
        raise ValueError("invalid_word")
    return normalized


def fraction(numerator, denominator):
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def word_contingency(rows, word, scope="all"):
    word = normalize_word(word)
    selected = select_records(rows, scope)
    counts = dict(spam_present=0, spam_absent=0, ham_present=0, ham_absent=0)
    for row in selected:
        present = word in set(tokenize(row["model_text"]))
        counts[f"{row['label']}_{'present' if present else 'absent'}"] += 1
    spam = counts["spam_present"] + counts["spam_absent"]
    observed = counts["spam_present"] + counts["ham_present"]
    total = len(selected)
    notes = []
    if not observed:
        notes.append("Word not observed in selected subset")
    if not spam:
        notes.append("No spam observations; word likelihood given spam is undefined.")
    if not total:
        notes.append("No observations in selected subset.")
    return {
        "word": word,
        "scope": scope,
        "total": total,
        "counts": counts,
        "probabilities": {
            "p_spam": fraction(spam, total),
            "p_word": fraction(observed, total),
            "p_spam_and_word": fraction(counts["spam_present"], total),
            "p_word_given_spam": fraction(counts["spam_present"], spam),
            "p_spam_given_word": fraction(counts["spam_present"], observed),
        },
        "notes": notes,
    }


def dataset_word_probability(root, word, scope="all"):
    rows, _ = load_split_dataset(root, scope)
    return word_contingency(rows, word, scope)
