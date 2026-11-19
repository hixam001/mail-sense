import asyncio
import logging

import pytest
from fastapi.testclient import TestClient

from app.core.local_boundary import LOCAL_ORIGINS, MAX_BODY_BYTES, LocalBoundary
from app.main import create_app
from scripts import serve


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as session:
        yield session


@pytest.mark.parametrize("origin", LOCAL_ORIGINS)
def test_explicit_local_cors(client, origin):
    response = client.options(
        "/api/v1/predict",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-credentials" not in response.headers


@pytest.mark.parametrize("origin", ["https://evil.invalid", "null", "http://localhost:9999"])
def test_foreign_origin_blocked_before_validation(client, origin):
    response = client.post("/api/v1/predict", headers={"Origin": origin}, content=b"invalid")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ORIGIN_REJECTED"
    assert "access-control-allow-origin" not in response.headers


def test_invalid_host_body_query_and_length(client):
    assert client.get("/api/v1/health", headers={"Host": "evil.invalid"}).status_code == 400
    response = client.post("/api/v1/predict", content=b"x" * (MAX_BODY_BYTES + 1))
    assert response.status_code == 413
    assert client.get("/api/v1/health?word=" + "x" * 4100).status_code == 414
    assert client.post("/api/v1/predict", headers={"Content-Length": "-1"}).status_code == 400
    assert client.get("/docs").status_code == 404


def test_streamed_limit_checks_before_application():
    called = False
    responses = []
    messages = iter(
        [
            {"type": "http.request", "body": b"x" * MAX_BODY_BYTES, "more_body": True},
            {"type": "http.request", "body": b"x", "more_body": False},
        ]
    )

    async def application(scope, receive, send):
        nonlocal called
        called = True

    async def receive():
        return next(messages)

    async def send(message):
        responses.append(message)

    asyncio.run(
        LocalBoundary(application)(
            {"type": "http", "headers": [(b"host", b"127.0.0.1")], "query_string": b""},
            receive,
            send,
        )
    )
    assert not called and responses[0]["status"] == 413


def test_input_is_absent_from_success_validation_and_exception_logs(tmp_path, caplog):
    private = "dummysecret@example.invalid"
    app = create_app(tmp_path)

    @app.post("/exception-probe")
    def probe():
        raise RuntimeError(private)

    caplog.set_level(logging.INFO, logger="mail_sense.requests")
    with TestClient(app, base_url="http://127.0.0.1") as client:
        for path, body in [
            ("/api/v1/predict", {"text": private}),
            ("/api/v1/predict", {"text": None}),
            ("/exception-probe", {"text": private}),
        ]:
            response = client.post(path + "?private=" + private, json=body)
            assert private not in response.text
            assert response.headers["cache-control"] == "no-store"
        assert response.status_code == 500
    records = [r for r in caplog.records if r.name == "mail_sense.requests"]
    assert len(records) == 3
    assert private not in " ".join(r.getMessage() for r in records)
    assert all(r.exc_info is None for r in records)


def test_launcher_has_fixed_loopback_and_no_url_access_logs(monkeypatch):
    calls = []
    monkeypatch.setattr(serve.uvicorn, "run", lambda *a, **kw: calls.append((a, kw)))
    serve.main()
    assert calls[0][1] == dict(host="127.0.0.1", port=8000, access_log=False, proxy_headers=False)
