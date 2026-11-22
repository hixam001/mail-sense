"""Known-answer checks for the conference paper's secondary statistical analysis."""

import math

import pytest
from scripts.analyze_paper import association, exact_p, paired_analysis, wilson


def test_exact_discordant_binomial_known_answer():
    assert exact_p(10, 0) == pytest.approx(2 / 2**10)
    assert exact_p(0, 10) == exact_p(10, 0)
    assert exact_p(5, 5) == 1
    assert exact_p(0, 0) == 1


def test_identical_paired_models_have_zero_difference_in_every_resample():
    truth = ["ham", "ham", "spam", "spam"]
    prediction = ["ham", "spam", "ham", "spam"]
    result = paired_analysis(truth, prediction, prediction, replicates=100)
    assert result["overall"] == {
        "both_correct": 2,
        "multinomial_only": 0,
        "bernoulli_only": 0,
        "both_wrong": 2,
    }
    assert result["exact_mcnemar_p"] == 1
    assert all(
        value == {"estimate": 0, "lower": 0, "upper": 0}
        for value in result["bootstrap"]["differences"].values()
    )


def test_paired_class_differences_have_expected_direction():
    truth = ["ham", "ham", "spam", "spam"]
    result = paired_analysis(truth, truth, ["spam", "ham", "ham", "ham"], replicates=100)
    differences = result["bootstrap"]["differences"]
    assert differences["accuracy"]["estimate"] == 0.75
    assert differences["recall"]["estimate"] == 1
    assert differences["false_positive_rate"]["estimate"] == -0.5


def test_wilson_and_contingency_hand_fixtures():
    interval = wilson(300, 1000)
    assert interval["lower"] == pytest.approx(0.272406842477)
    assert interval["upper"] == pytest.approx(0.329123860917)
    effect = association(180, 120, 70, 630)
    assert effect["chi_square"] == 280
    assert effect["phi"] == math.sqrt(0.28)
    assert effect["odds_ratio"] == 13.5
    assert effect["p_spam_given_present"] == 0.72


def test_invalid_paired_lengths_rejected():
    with pytest.raises(ValueError, match="invalid_paired_input"):
        paired_analysis(["ham"], [], [])
