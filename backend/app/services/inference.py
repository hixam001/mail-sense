"""Statistical inference with explicit suitability checks and historical-data caveats."""

import math
from numbers import Integral, Real

import numpy as np
from scipy.stats import chi2

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
