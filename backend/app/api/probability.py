"""Empirical probability and assumption-aware inference over verified cached data."""

from fastapi import APIRouter, Query, Request

from app.api.errors import ApiError
from app.api.validation import canonical_word, selected_dataset
from app.schemas.common import Scope
from app.schemas.probability import (
    BinomialResponse,
    ConfidenceResponse,
    HypothesisRequest,
    HypothesisResponse,
    WordProbabilityResponse,
)
from app.services.inference import confidence_interval, hypothesis_test
from app.services.probability import word_contingency, word_distribution

router = APIRouter(prefix="/api/v1", tags=["Probability and inference"])


@router.get("/probability/word", response_model=WordProbabilityResponse)
def word_probability(
    request: Request, word: str = Query(..., min_length=1, max_length=64), scope: Scope = "all"
):
    word = canonical_word(word)
    return word_contingency(selected_dataset(request, scope), word, scope)


@router.get("/probability/distributions", response_model=BinomialResponse)
def binomial(
    request: Request,
    word: str = Query(..., min_length=1, max_length=64),
    scope: Scope = "all",
    trials: int = Query(10, ge=1, le=100),
    successes: int = Query(1, ge=0, le=100),
):
    word = canonical_word(word)
    if successes > trials:
        raise ApiError(
            422,
            "INVALID_INPUT",
            "Successes must be between zero and trials.",
            {"field": "successes"},
        )
    return word_distribution(selected_dataset(request, scope), word, scope, trials, successes)


@router.post("/statistics/hypothesis-test", response_model=HypothesisResponse)
def hypothesis(request: Request, payload: HypothesisRequest):
    return hypothesis_test(
        selected_dataset(request, payload.scope), payload.word, payload.scope, payload.alpha
    )


@router.get("/statistics/confidence-interval", response_model=ConfidenceResponse)
def interval(
    request: Request,
    scope: Scope = "all",
    confidence: float = Query(0.95, ge=0.80, le=0.99, allow_inf_nan=False),
):
    return confidence_interval(selected_dataset(request, scope), scope, confidence)
