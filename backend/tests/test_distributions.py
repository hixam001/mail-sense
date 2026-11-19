import numpy as np
import pytest

from app.services.distributions import distributions


def record(value, label="ham", split="train", text="word"):
    return dict(
        token_count=value, character_count=value * 2, label=label, split=split, model_text=text
    )


def test_histogram_endpoints_reconcile_with_numpy_and_boxplot():
    rows = [record(i) for i in [0, 1, 2, 3, 4, 5, 10]]
    result = distributions(rows)
    edges = [item["lower"] for item in result["bins"]] + [result["bins"][-1]["upper"]]
    expected, _ = np.histogram([r["token_count"] for r in rows], bins=edges)
    assert [item["count"] for item in result["bins"]] == expected.tolist()
    assert sum(item["count"] for item in result["bins"]) == 7
    assert result["boxplot"] == dict(min=0, q1=1.5, median=3, q3=4.5, max=10)
    assert result["unit"] == "tokens/email"


def test_constant_empty_and_scope_class_filters():
    rows = [record(2), record(2), record(9, "spam", "test")]
    result = distributions(rows, "train", class_label="ham")
    assert result["bins"] == [dict(lower=2, upper=3, count=2)]
    assert result["selected_records"] == 2
    empty = distributions(rows, "train", class_label="spam")
    assert empty["bins"] == [] and empty["boxplot"] is None


def test_t10_document_frequency_not_token_frequency_with_deterministic_ties():
    rows = [
        record(10, text="free " * 10 + "offer"),
        record(1, text="free zebra"),
        record(3, "spam", "test", "offer offer prize"),
    ]
    result = distributions(rows, metric="top_words", top_n=3)
    assert result["items"] == [
        dict(word="free", count=2),
        dict(word="offer", count=2),
        dict(word="prize", count=1),
    ]
    assert result["frequency_type"] == "document_frequency"
    assert distributions(rows, "test", "top_words", "spam")["items"][0] == {
        "word": "offer",
        "count": 1,
    }
    assert distributions([], metric="top_words")["items"] == []


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(metric="invalid"),
        dict(scope="invalid"),
        dict(class_label="invalid"),
        dict(top_n=0),
        dict(top_n=31),
        dict(top_n=True),
        dict(top_n=1.5),
    ],
)
def test_invalid_distribution_options(kwargs):
    with pytest.raises(ValueError):
        distributions([], **kwargs)
