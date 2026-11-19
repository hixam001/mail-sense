import math

import pytest
from scipy.stats import norm

from app.services.inference import confidence_interval, wilson_score


def test_known_300_of_1000_interval():
    result = wilson_score(300, 1000)
    assert result["point_estimate"] == 0.3
    assert result["lower"] == pytest.approx(0.2724, abs=0.00005)
    assert result["upper"] == pytest.approx(0.3291, abs=0.00005)
    assert "Historical" in result["limitations"]


@pytest.mark.parametrize("x", [0, 1, 5, 10])
@pytest.mark.parametrize("confidence", [0.8, 0.95, 0.99])
def test_independent_normal_quantile_and_boundaries(x, confidence):
    n = 10
    z = norm.ppf((1 + confidence) / 2)
    center = (x / n + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt((x / n) * (1 - x / n) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    result = wilson_score(x, n, confidence)
    assert result["lower"] == pytest.approx(max(0, center - half))
    assert result["upper"] == pytest.approx(min(1, center + half))
    assert 0 <= result["lower"] <= result["upper"] <= 1


@pytest.mark.parametrize(
    "x,n,confidence",
    [
        (-1, 10, 0.95),
        (11, 10, 0.95),
        (1, -1, 0.95),
        (True, 10, 0.95),
        (1, True, 0.95),
        (1.5, 10, 0.95),
        (1, 10, 0.79),
        (1, 10, 1),
        (1, 10, float("nan")),
        (1, 10, True),
    ],
)
def test_invalid_interval_parameters(x, n, confidence):
    with pytest.raises(ValueError):
        wilson_score(x, n, confidence)


def test_empty_and_scope_denominators():
    assert wilson_score(0, 0)["point_estimate"] is None
    assert wilson_score(0, 0)["lower"] is None
    rows = [dict(label="spam", split="train"), dict(label="ham", split="test")]
    assert confidence_interval(rows, "train")["spam_count"] == 1
    assert confidence_interval(rows, "test")["sample_size"] == 1
