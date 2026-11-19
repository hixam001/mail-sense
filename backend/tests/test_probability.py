import pytest

from app.services.probability import normalize_word, word_contingency


def teaching_rows():
    rows = []
    for label, present, absent in (("spam", 180, 120), ("ham", 70, 630)):
        rows.extend(
            dict(label=label, model_text="free " * 10, split="train") for _ in range(present)
        )
        rows.extend(dict(label=label, model_text="meeting", split="test") for _ in range(absent))
    return rows


def test_t04_known_thousand_document_table_and_bayes():
    result = word_contingency(teaching_rows(), "FREE")
    assert result["counts"] == dict(
        spam_present=180, spam_absent=120, ham_present=70, ham_absent=630
    )
    expected = dict(
        p_spam=0.3, p_word=0.25, p_spam_and_word=0.18, p_word_given_spam=0.6, p_spam_given_word=0.72
    )
    assert {key: ratio["value"] for key, ratio in result["probabilities"].items()} == expected
    assert expected["p_spam_given_word"] == pytest.approx(
        expected["p_word_given_spam"] * expected["p_spam"] / expected["p_word"]
    )
    assert result["probabilities"]["p_spam_given_word"]["denominator"] == 250
    assert sum(result["counts"].values()) == result["total"] == 1000


def test_absent_word_missing_class_empty_and_scopes():
    result = word_contingency(teaching_rows(), "unseen")
    assert result["probabilities"]["p_spam_given_word"]["value"] is None
    assert result["notes"][0] == "Word not observed in selected subset"
    assert word_contingency(teaching_rows(), "free", "train")["total"] == 250
    assert word_contingency(teaching_rows(), "free", "test")["counts"]["spam_present"] == 0
    ham_only = word_contingency([dict(label="ham", model_text="free")], "free")
    assert ham_only["probabilities"]["p_word_given_spam"]["value"] is None
    assert ham_only["probabilities"]["p_spam_given_word"]["value"] == 0
    assert all(r["value"] is None for r in word_contingency([], "free")["probabilities"].values())


@pytest.mark.parametrize("word", ["", "a", "free offer", "free!", "x" * 65, None, 4])
def test_invalid_tokens_rejected(word):
    with pytest.raises(ValueError, match="invalid_word"):
        normalize_word(word)


def test_unicode_and_whitespace_normalization():
    assert normalize_word("  CAFÉ ") == "café"
    assert normalize_word("cafe\u0301") == "café"
    assert (
        word_contingency([dict(label="ham", model_text="Café café")], "CAFÉ")["counts"][
            "ham_present"
        ]
        == 1
    )
