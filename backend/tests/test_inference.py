import pytest
from scipy.stats import chi2_contingency

from app.services.inference import hypothesis_test, pearson_table


def test_known_pearson_table_without_continuity_correction():
    result = pearson_table([[180, 120], [70, 630]])
    assert result["expected"] == [[75, 225], [175, 525]]
    assert result["chi_square"] == 280
    assert result["p_value"] == pytest.approx(7.50924e-63, rel=1e-6)
    assert result["degrees_of_freedom"] == 1
    assert result["continuity_correction"] is False
    assert result["reject_null"] is True


@pytest.mark.parametrize("table", [[[20, 30], [40, 50]], [[5, 10], [8, 13]], [[100, 1], [1, 100]]])
def test_independent_scipy_reference(table):
    expected = chi2_contingency(table, correction=False)
    actual = pearson_table(table)
    assert actual["chi_square"] == pytest.approx(expected.statistic)
    assert actual["p_value"] == pytest.approx(expected.pvalue)


@pytest.mark.parametrize(
    "table", [[[1, 1], [1, 1]], [[0, 10], [0, 20]], [[0, 0], [0, 0]], [[3, 2], [0, 0]]]
)
def test_unsuitable_tables_never_produce_automatic_decisions(table):
    result = pearson_table(table)
    assert result["assumptions_satisfied"] is False
    assert result["reject_null"] is None
    assert result["warnings"]


@pytest.mark.parametrize(
    "table",
    [
        [[1, 2]],
        [[-1, 2], [3, 4]],
        [[True, 2], [3, 4]],
        [[0.5, 2], [3, 4]],
        [[float("nan"), 2], [3, 4]],
    ],
)
def test_invalid_count_tables(table):
    with pytest.raises(ValueError):
        pearson_table(table)


@pytest.mark.parametrize("alpha", [0, 1, -0.5, float("nan"), True])
def test_invalid_significance_levels(alpha):
    with pytest.raises(ValueError):
        pearson_table([[10, 10], [10, 10]], alpha)


def test_absent_word_and_empty_dataset_are_defined():
    result = hypothesis_test([dict(label="ham", model_text="meeting")], "free")
    assert result["chi_square"] is None and result["reject_null"] is None
    assert hypothesis_test([], "free")["p_value"] is None
