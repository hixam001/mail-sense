"""Validated probability/inference requests and explicit numerical responses."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import Scope
from app.services.probability import normalize_word


class FractionResponse(BaseModel):
    numerator: int
    denominator: int
    value: float | None


class WordProbabilityResponse(BaseModel):
    word: str
    scope: Scope
    total: int
    counts: dict[str, int]
    probabilities: dict[str, FractionResponse]
    notes: list[str]


class BinomialResponse(BaseModel):
    word: str
    scope: Scope
    bernoulli_p: float | None
    bernoulli: dict[str, float | None]
    trials: int
    successes: int
    binomial_pmf: float | None
    assumptions: list[str]
    notes: list[str]


class HypothesisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    word: str = Field(min_length=1, max_length=64)
    scope: Scope = "all"
    alpha: float = Field(default=0.05, gt=0, lt=1, allow_inf_nan=False)

    @field_validator("word")
    @classmethod
    def normalized_word(cls, value):
        return normalize_word(value)


class HypothesisResponse(BaseModel):
    word: str
    scope: Scope
    test: Literal["pearson_chi_square_independence"]
    null_hypothesis: str
    alternative_hypothesis: str
    observed: list[list[int]]
    expected: list[list[float]]
    chi_square: float | None
    degrees_of_freedom: int
    p_value: float | None
    alpha: float
    continuity_correction: bool
    assumptions_satisfied: bool
    warnings: list[str]
    reject_null: bool | None
    limitations: str


class ConfidenceResponse(BaseModel):
    scope: Scope
    method: Literal["wilson"]
    confidence: float
    sample_size: int
    spam_count: int
    point_estimate: float | None
    lower: float | None
    upper: float | None
    limitations: str
    notes: list[str]
