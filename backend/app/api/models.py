"""Inference uses cached verified models; no fitting, text storage or input echo."""

from fastapi import APIRouter, Query, Request

from app.api.validation import canonical_word
from app.schemas.common import ModelName
from app.schemas.models import (
    ComparisonResponse,
    ModelMetrics,
    PredictionRequest,
    PredictionResponse,
    WordExplanation,
)
from app.services.prediction import predict_text, word_explanation

router = APIRouter(prefix="/api/v1", tags=["Models"])


@router.post("/predict", response_model=PredictionResponse)
def prediction(body: PredictionRequest, request: Request):
    return predict_text(request.app.state.mail_sense.model_snapshot(), body.text)


@router.get("/models/metrics", response_model=ModelMetrics)
def metrics(request: Request, model: ModelName):
    return request.app.state.mail_sense.evaluation_snapshot()["models"][model]


@router.get("/models/comparison", response_model=ComparisonResponse)
def comparison(request: Request):
    return request.app.state.mail_sense.evaluation_snapshot()


@router.get("/models/explanations", response_model=WordExplanation)
def explanation(request: Request, model: ModelName, word: str = Query(min_length=1, max_length=64)):
    word = canonical_word(word)
    return word_explanation(request.app.state.mail_sense.model_snapshot(), word, model)
