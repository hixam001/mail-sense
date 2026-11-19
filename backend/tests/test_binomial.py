import pytest
from scipy.stats import binom

from app.services.probability import bernoulli_binomial, word_distribution


def test_known_pmf_and_bernoulli_moments():
    result = bernoulli_binomial(0.25, 10, 1)
    assert result["binomial_pmf"] == pytest.approx(0.1877117156982422)
    assert result["bernoulli"]["variance"] == 0.1875
    assert result["assumptions"]


@pytest.mark.parametrize("p", [0, 0.01, 0.5, 0.99, 1])
def test_independent_scipy_pmf_and_complete_mass(p):
    values = [bernoulli_binomial(p, 10, k)["binomial_pmf"] for k in range(11)]
    assert values == pytest.approx(binom.pmf(range(11), 10, p).tolist())
    assert sum(values) == pytest.approx(1)


@pytest.mark.parametrize(
    "p,n,k",
    [
        (float("nan"), 10, 1),
        (float("inf"), 10, 1),
        (-0.1, 10, 1),
        (1.1, 10, 1),
        (True, 10, 1),
        (0.5, 0, 0),
        (0.5, 101, 1),
        (0.5, 1.5, 1),
        (0.5, True, 1),
        (0.5, 10, -1),
        (0.5, 10, 11),
        (0.5, 10, True),
        (0.5, 10, 0.5),
    ],
)
def test_invalid_parameters_are_rejected(p, n, k):
    with pytest.raises(ValueError):
        bernoulli_binomial(p, n, k)


def test_observed_probability_and_empty_denominator():
    rows = [dict(label="ham", model_text="free"), dict(label="spam", model_text="meeting")]
    assert word_distribution(rows, "free")["bernoulli_p"] == 0.5
    assert word_distribution(rows, "unseen")["binomial_pmf"] == 0
    assert word_distribution([], "free")["binomial_pmf"] is None
