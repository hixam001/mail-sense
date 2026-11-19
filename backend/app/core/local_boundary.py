"""Bound requests before parsing; log only a method, static route and status."""

import logging
from urllib.parse import urlsplit

from app.api.errors import error_response

LOCAL_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://[::1]:5173",
)
MAX_BODY_BYTES = 512 * 1024
logger = logging.getLogger("mail_sense.requests")


class LocalBoundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {}
        for key, value in scope.get("headers", []):
            headers.setdefault(key.lower(), []).append(value)
        hosts = headers.get(b"host", [])
        origins = headers.get(b"origin", [])
        try:
            host = urlsplit("//" + hosts[0].decode("ascii")).hostname if len(hosts) == 1 else None
        except (ValueError, UnicodeError):
            host = None
        if host not in {"localhost", "127.0.0.1", "::1"}:
            await error_response(400, "INVALID_HOST", "Use the local loopback address.")(
                scope, receive, send
            )
            return
        if origins and (len(origins) != 1 or origins[0].decode("latin1") not in LOCAL_ORIGINS):
            await error_response(403, "ORIGIN_REJECTED", "Use the local MailSense interface.")(
                scope, receive, send
            )
            return
        if len(scope.get("query_string", b"")) > 4096:
            await error_response(414, "QUERY_TOO_LARGE", "Request query exceeds the local limit.")(
                scope, receive, send
            )
            return
        lengths = headers.get(b"content-length", [])
        try:
            length = int(lengths[0]) if lengths else 0
            if len(lengths) > 1 or length < 0:
                raise ValueError
        except ValueError:
            await error_response(400, "INVALID_LENGTH", "Invalid request length.")(
                scope, receive, send
            )
            return
        if length > MAX_BODY_BYTES:
            await error_response(413, "BODY_TOO_LARGE", "Request body exceeds 512 KiB.")(
                scope, receive, send
            )
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > MAX_BODY_BYTES:
                await error_response(413, "BODY_TOO_LARGE", "Request body exceeds 512 KiB.")(
                    scope, receive, send
                )
                return
            if not message.get("more_body", False):
                break
        delivered = False
        started = False
        status = 500

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        async def safe_send(message):
            nonlocal started, status
            if message["type"] == "http.response.start":
                started, status = True, message["status"]
                message["headers"] = list(message.get("headers", [])) + [
                    (b"x-content-type-options", b"nosniff"),
                    (b"cache-control", b"no-store"),
                ]
            await send(message)

        try:
            await self.app(scope, bounded_receive, safe_send)
        except Exception:
            # Do not let server exception logging serialize a request-bearing exception.
            if not started:
                await error_response(500, "INTERNAL_ERROR", "An unexpected local error occurred.")(
                    scope, bounded_receive, safe_send
                )
        finally:
            body.clear()
            route = scope.get("route")
            method = scope.get("method")
            logger.info(
                "%s %s %s",
                method if method in {"GET", "POST", "OPTIONS", "HEAD"} else "OTHER",
                getattr(route, "path", "unmatched"),
                status,
            )
