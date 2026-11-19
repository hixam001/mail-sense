"""Local educational API with verified artifact readiness and safe errors."""

from pathlib import Path

from fastapi import FastAPI

from app.api.dataset import router as dataset_router
from app.api.errors import install_errors
from app.api.probability import router as probability_router
from app.core.state import ApplicationState
from app.schemas.common import ErrorEnvelope, HealthResponse


def create_app(root=None):
    application = FastAPI(
        title="MailSense API",
        description="Local probability and statistics service.",
        version="1.0.0",
        responses={code: {"model": ErrorEnvelope} for code in (400, 404, 422, 500, 503)},
    )
    application.state.mail_sense = ApplicationState(root or Path(__file__).resolve().parents[2])
    install_errors(application)
    application.include_router(dataset_router)
    application.include_router(probability_router)

    @application.get("/", summary="Scaffold greeting")
    def greeting():
        return {"message": "MailSense API scaffold is running."}

    @application.get("/api/v1/health", tags=["Readiness"], response_model=HealthResponse)
    def health():
        return application.state.mail_sense.health()

    return application


app = create_app()
