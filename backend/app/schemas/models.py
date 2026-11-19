"""Transient inference inputs and explicit dual-model evaluation responses."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import ModelName
from app.services.mail_parser import normalize_text


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=50_000)

    @field_validator("text", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("text")
    @classmethod
    def nonempty_normalized_text(cls, value):
        if not normalize_text(value):
            raise ValueError("empty_normalized_text")
        return value


class InputStatistics(BaseModel):
    character_count: int
    recognized_token_count: int


class TermContribution(BaseModel):
    token: str
    presence: Literal["present"]
    log_odds_contribution: float
    direction: Literal["ham", "spam", "neutral"]


class ModelPrediction(BaseModel):
    prediction: Literal["ham", "spam"]
    spam_probability: float = Field(ge=0, le=1, allow_inf_nan=False)
    top_contributions: list[TermContribution]
    class_prior_log_odds: float
    absence_terms_included: bool
    absence_log_odds_contribution: float
    other_present_log_odds: float
    log_odds: float


class DualPredictions(BaseModel):
    multinomial: ModelPrediction
    bernoulli: ModelPrediction


class PredictionResponse(BaseModel):
    input: InputStatistics
    models: DualPredictions
    agreement: bool
    warnings: list[str]


class ModelMetrics(BaseModel):
    model: ModelName
    split_id: str
    positive_class: Literal["spam"]
    test_count: int
    test_ids_sha256: str
    confusion_matrix: dict[str, int]
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1: float | None
    false_positive_rate: float | None
    zero_division_policy: str
    notes: list[str]


class DualMetrics(BaseModel):
    multinomial: ModelMetrics
    bernoulli: ModelMetrics


class ComparisonResponse(BaseModel):
    dataset_id: str
    split_id: str
    artifact_id: str
    test_count: int
    test_ids_sha256: str
    same_test_ids: bool
    models: DualMetrics
    limitations: list[str]


class WordExplanation(BaseModel):
    model: ModelName
    word: str
    in_vocabulary: bool
    log_odds_when_present: float | None
    interpretation: str
    absence_terms_included: bool = False
    log_odds_when_absent: float | None = None
