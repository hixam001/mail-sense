"""Shared safe JSON errors; request values, paths and tracebacks are never echoed."""

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, status, code, message, details=None):
        self.status, self.code, self.message = status, code, message
        self.details = details or {}
        super().__init__(code)


def error_response(status, code, message, details=None):
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )


def install_errors(app):
    @app.exception_handler(ApiError)
    async def application_error(request, error):
        return error_response(error.status, error.code, error.message, error.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        known = {
            "text",
            "word",
            "scope",
            "model",
            "alpha",
            "confidence",
            "trials",
            "successes",
            "metric",
            "class_label",
            "top_n",
        }
        fields = []
        for item in error.errors()[:20]:
            field = next((value for value in reversed(item["loc"]) if value in known), "request")
            fields.append({"field": field, "type": item["type"]})
        return error_response(
            422, "INVALID_INPUT", "Request parameters are invalid.", {"fields": fields}
        )

    @app.exception_handler(HTTPException)
    async def http_error(request, error):
        code = "NOT_FOUND" if error.status_code == 404 else "REQUEST_REJECTED"
        message = (
            "Requested endpoint was not found."
            if error.status_code == 404
            else ("The local request was rejected.")
        )
        return error_response(error.status_code, code, message)

    @app.exception_handler(Exception)
    async def unexpected_error(request, error):
        return error_response(500, "INTERNAL_ERROR", "An unexpected local error occurred.")
