"""Empirical word-document probabilities with visible denominators and no smoothing."""

import math
import unicodedata
from numbers import Real

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


def bernoulli_binomial(p, trials=10, successes=1):
    if isinstance(p, bool) or not isinstance(p, Real) or not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("invalid_probability")
    if type(trials) is not int or not 1 <= trials <= 100:
        raise ValueError("invalid_trials")
    if type(successes) is not int or not 0 <= successes <= trials:
        raise ValueError("invalid_successes")
    return {
        "bernoulli_p": p,
        "trials": trials,
        "successes": successes,
        "bernoulli": {"p_zero": 1 - p, "p_one": p, "mean": p, "variance": p * (1 - p)},
        "binomial_pmf": math.comb(trials, successes)
        * p**successes
        * (1 - p) ** (trials - successes),
        "assumptions": [
            "The repeated trials are modeled as independent with constant p.",
            "This demonstration does not establish independence of historical emails.",
        ],
    }


def word_distribution(rows, word, scope="all", trials=10, successes=1):
    empirical = word_contingency(rows, word, scope)
    p = empirical["probabilities"]["p_word"]["value"]
    result = bernoulli_binomial(p if p is not None else 0, trials, successes)
    if p is None:
        result.update(
            bernoulli_p=None,
            binomial_pmf=None,
            bernoulli=dict.fromkeys(("p_zero", "p_one", "mean", "variance")),
        )
    return {"word": empirical["word"], "scope": scope, **result, "notes": empirical["notes"]}


def dataset_word_distribution(root, word, scope="all", trials=10, successes=1):
    rows, _ = load_split_dataset(root, scope)
    return word_distribution(rows, word, scope, trials, successes)
