import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.observability import add_observability


def test_unhandled_exception_includes_request_id_header():
    app = FastAPI()
    add_observability(app, logger=logging.getLogger("test"))

    @app.get("/boom")
    def _boom():
        raise RuntimeError("boom")

    client = TestClient(app)
    request_id = "test-req-500"
    r = client.get("/boom", headers={"X-Request-ID": request_id})
    assert r.status_code == 500
    assert r.headers.get("x-request-id") == request_id
    assert r.json()["detail"] == "Internal server error"
