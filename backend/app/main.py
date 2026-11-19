"""Independent API scaffold; analytical endpoints are implemented in later tickets."""

from fastapi import FastAPI

app = FastAPI(
    title="MailSense API",
    description="Local scaffold. Analytics and model endpoints are not implemented yet.",
    version="0.1.0",
)


@app.get("/", summary="Scaffold greeting")
def root() -> dict[str, str]:
    return {"message": "MailSense API scaffold is running."}
