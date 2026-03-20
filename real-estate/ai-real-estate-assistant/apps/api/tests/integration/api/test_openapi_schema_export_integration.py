from __future__ import annotations

import json
from pathlib import Path

from api.main import app as fastapi_app
from api.openapi_export import export_openapi_schema


def test_openapi_schema_contains_core_routes(tmp_path: Path) -> None:
    out = tmp_path / "openapi.json"
    export_openapi_schema(app=fastapi_app, output_path=out, check=False)

    schema = json.loads(out.read_text(encoding="utf-8"))
    paths = schema["paths"]

    assert "/health" in paths
    assert "/api/v1/search" in paths
    assert "/api/v1/chat" in paths
