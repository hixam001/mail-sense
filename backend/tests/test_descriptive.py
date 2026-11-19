import math
import statistics

import numpy as np
import pytest

from app.services.descriptive import descriptive_statistics, summarize


def test_t03_known_descriptive_fixture():
    result = summarize([2, 4, 4, 6])
    assert result["mean"] == result["median"] == result["mode"] == 4
    assert result["sample_variance"] == pytest.approx(8 / 3)
    assert result["sample_std"] == pytest.approx(math.sqrt(8 / 3))
    assert (result["q1"], result["q3"], result["iqr"]) == (3.5, 4.5, 1)


@pytest.mark.parametrize("values", [[0], [9, 1], [0, 0, 0], [7, 2, 9, 1, 4], [1.5, 2.5, 9.5]])
def test_independent_statistics_and_linear_quantiles(values):
    result = summarize(values)
    assert result["mean"] == statistics.mean(values)
    assert result["median"] == statistics.median(values)
    assert (result["q1"], result["q3"]) == tuple(np.quantile(values, [0.25, 0.75], method="linear"))
    if len(values) > 1:
        assert result["sample_variance"] == statistics.variance(values)


def test_ties_and_empty_singleton_are_truthful():
    assert summarize([9, 2, 9, 2])["mode"] == 2
    assert summarize([9, 2, 9, 2])["mode_tied"] is True
    assert summarize([])["mean"] is None
    assert summarize([4])["sample_variance"] is None
    assert summarize([4])["sample_std"] is None
    assert summarize([4])["notes"]


@pytest.mark.parametrize("value", [True, "4", None, float("nan"), float("inf"), -1, 1e308])
def test_invalid_or_overflowing_counts_fail(value):
    with pytest.raises(ValueError):
        summarize([value, 0])


def test_scope_class_counts_and_units():
    rows = [
        {"label": "spam", "split": "train", "token_count": 2, "character_count": 8},
        {"label": "ham", "split": "test", "token_count": 4, "character_count": 16},
    ]
    result = descriptive_statistics(rows, "train", "character_count")
    assert result["groups"]["spam"]["mean"] == 8
    assert result["groups"]["ham"]["n"] == 0
    assert result["unit"] == "characters/email"
    with pytest.raises(ValueError):
        descriptive_statistics(rows, "unknown")
    with pytest.raises(ValueError):
        descriptive_statistics(rows, metric="unknown")
