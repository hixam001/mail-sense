"""Shared public API types; no schema exposes private corpus records."""

from typing import Any, Literal

from pydantic import BaseModel, Field

Scope = Literal["all", "train", "test"]
ModelName = Literal["multinomial", "bernoulli"]
CountMetric = Literal["character_count", "token_count"]


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class ModelReadiness(BaseModel):
    multinomial: bool
    bernoulli: bool


class HealthResponse(BaseModel):
    status: Literal["ready", "degraded"]
    dataset_ready: bool
    models_ready: ModelReadiness
    evaluation_ready: bool
    split_id: str | None
