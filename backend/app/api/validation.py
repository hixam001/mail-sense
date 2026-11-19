"""Shared safe semantic validation for API tokens and selected records."""

from app.api.errors import ApiError
from app.services.analytics_data import select_records
from app.services.probability import normalize_word


def canonical_word(word):
    try:
        return normalize_word(word)
    except ValueError:
        raise ApiError(
            422,
            "INVALID_INPUT",
            "Enter one word of at least two word characters.",
            {"field": "word"},
        ) from None


def selected_dataset(request, scope):
    rows, _, _, _ = request.app.state.mail_sense.dataset_snapshot()
    if not select_records(rows, scope):
        raise ApiError(503, "EMPTY_SUBSET", "No observations are available in the selected subset.")
    return rows
