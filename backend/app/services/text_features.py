"""Fixed text features shared by summary records and future model preprocessing."""

import re

TOKENIZER_VERSION = "unicode-word-v1"
TOKEN_PATTERN = r"(?u)\b\w\w+\b"
_TOKENS = re.compile(TOKEN_PATTERN)


def tokenizer_config():
    return {
        "version": TOKENIZER_VERSION,
        "lowercase": True,
        "token_pattern": TOKEN_PATTERN,
        "strip_accents": None,
        "stop_words": None,
        "ngram_range": [1, 1],
    }


def tokenize(text):
    """Return Unicode word unigrams of length >= 2; no fitted state or filtering."""
    return _TOKENS.findall(text.lower())


def token_count(text):
    return sum(1 for _ in _TOKENS.finditer(text.lower()))
