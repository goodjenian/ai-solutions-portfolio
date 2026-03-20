import io
import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.observability import add_observability
from utils.json_logging import JsonFormatter


def test_api_request_structured_log_contains_fields():
    app = FastAPI()
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("structured-test")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    add_observability(app, logger)

    @app.get("/ping")
    def _ping():
        return {"ok": True}

    client = TestClient(app)
    client.get("/ping")
    contents = stream.getvalue().strip().splitlines()
    assert any("api_request" in line for line in contents)
    parsed = [json.loads(line) for line in contents if "api_request" in line]
    assert parsed, "no api_request logs"
    entry = parsed[-1]
    assert entry["event"] == "api_request"
    assert isinstance(entry["request_id"], str) and entry["request_id"]
    assert entry["path"] == "/ping"
    assert entry["status"] == 200
    assert isinstance(entry["duration_ms"], float)
