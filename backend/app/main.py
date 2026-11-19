"""Local educational API with verified artifact readiness and safe errors."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dataset import router as dataset_router
from app.api.errors import install_errors
from app.api.models import router as models_router
from app.api.probability import router as probability_router
from app.core.local_boundary import LOCAL_ORIGINS, LocalBoundary
from app.core.state import ApplicationState
from app.schemas.common import ErrorEnvelope, HealthResponse


def create_app(root=None):
    application = FastAPI(
        title="MailSense API",
        description="Local probability and statistics service.",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        responses={
            code: {"model": ErrorEnvelope} for code in (400, 403, 404, 413, 414, 422, 500, 503)
        },
    )
    application.state.mail_sense = ApplicationState(root or Path(__file__).resolve().parents[2])
    install_errors(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(LOCAL_ORIGINS),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    application.add_middleware(LocalBoundary)
    application.include_router(dataset_router)
    application.include_router(probability_router)
    application.include_router(models_router)

    @application.get("/", summary="API greeting")
    def greeting():
        return {"message": "MailSense API is running."}

    @application.get("/api/v1/health", tags=["Readiness"], response_model=HealthResponse)
    def health():
        return application.state.mail_sense.health()

    return application


app = create_app()
