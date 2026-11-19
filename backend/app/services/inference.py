"""Statistical inference with explicit suitability checks and historical-data caveats."""

import math
from numbers import Integral, Real
from statistics import NormalDist

import numpy as np
from scipy.stats import chi2

from app.services.analytics_data import select_records
from app.services.corpus_split import load_split_dataset
from app.services.probability import word_contingency


def pearson_table(observed, alpha=0.05):
    if (
        isinstance(alpha, bool)
        or not isinstance(alpha, Real)
        or not math.isfinite(alpha)
        or not 0 < alpha < 1
    ):
        raise ValueError("invalid_alpha")
    array = np.asarray(observed, dtype=object)
    if array.shape != (2, 2) or any(
        isinstance(value, bool) or not isinstance(value, Integral) or value < 0
        for value in array.flat
    ):
        raise ValueError("invalid_contingency_table")
    table = [[int(value) for value in row] for row in array]
    total = sum(sum(row) for row in table)
    row_sums = [sum(row) for row in table]
    columns = [sum(table[i][j] for i in range(2)) for j in range(2)]
    try:
        expected = [
            [row_sums[i] * columns[j] / total if total else 0 for j in range(2)] for i in range(2)
        ]
    except OverflowError as error:
        raise ValueError("invalid_contingency_table") from error
    positive = all(value > 0 and math.isfinite(value) for row in expected for value in row)
    suitable = positive and all(value >= 5 for row in expected for value in row)
    statistic = (
        sum(
            (table[i][j] - expected[i][j]) ** 2 / expected[i][j] for i in range(2) for j in range(2)
        )
        if positive
        else None
    )
    if statistic is not None and not math.isfinite(statistic):
        raise ValueError("invalid_contingency_table")
    p_value = float(chi2.sf(statistic, 1)) if statistic is not None else None
    warnings = []
    if not positive:
        warnings.append("Zero expected count: chi-square statistic and p-value are undefined.")
    elif not suitable:
        warnings.append("Expected counts below 5: chi-square approximation may be unsuitable.")
    if p_value == 0:
        warnings.append("P-value underflowed to zero in floating-point arithmetic.")
    return {
        "test": "pearson_chi_square_independence",
        "null_hypothesis": "Word presence and email class are independent.",
        "alternative_hypothesis": "Word presence and email class are associated.",
        "observed": table,
        "expected": expected,
        "chi_square": statistic,
        "degrees_of_freedom": 1,
        "p_value": p_value,
        "alpha": alpha,
        "continuity_correction": False,
        "assumptions_satisfied": suitable,
        "warnings": warnings,
        "reject_null": p_value < alpha if suitable else None,
        "limitations": "Independence is assumed, not established. Association is not causation.",
    }


def hypothesis_test(rows, word, scope="all", alpha=0.05):
    empirical = word_contingency(rows, word, scope)
    counts = empirical["counts"]
    table = [
        [counts["spam_present"], counts["spam_absent"]],
        [counts["ham_present"], counts["ham_absent"]],
    ]
    return {"word": empirical["word"], "scope": scope, **pearson_table(table, alpha)}


def dataset_hypothesis_test(root, word, scope="all", alpha=0.05):
    rows, _ = load_split_dataset(root, scope)
    return hypothesis_test(rows, word, scope, alpha)


def wilson_score(spam_count, sample_size, confidence=0.95):
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, Real)
        or not math.isfinite(confidence)
        or not 0.80 <= confidence <= 0.99
    ):
        raise ValueError("invalid_confidence")
    if (
        any(
            isinstance(value, bool) or not isinstance(value, Integral)
            for value in (spam_count, sample_size)
        )
        or not 0 <= spam_count <= sample_size
    ):
        raise ValueError("invalid_interval_counts")
    x, n = int(spam_count), int(sample_size)
    result = dict(
        method="wilson",
        confidence=confidence,
        sample_size=n,
        spam_count=x,
        point_estimate=x / n if n else None,
        lower=None,
        upper=None,
        limitations="Historical, curated corpus; interval does not guarantee "
        "population representativeness.",
        notes=[],
    )
    if not n:
        result["notes"] = ["No observations; proportion and interval are undefined."]
        return result
    p = x / n
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    divisor = 1 + z * z / n
    center = (p + z * z / (2 * n)) / divisor
    half = z / divisor * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    result.update(lower=max(0.0, center - half), upper=min(1.0, center + half))
    return result


def confidence_interval(rows, scope="all", confidence=0.95):
    selected = select_records(rows, scope)
    return {
        "scope": scope,
        **wilson_score(sum(row["label"] == "spam" for row in selected), len(selected), confidence),
    }


def dataset_confidence_interval(root, scope="all", confidence=0.95):
    rows, _ = load_split_dataset(root, scope)
    return confidence_interval(rows, scope, confidence)
