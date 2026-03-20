from __future__ import annotations

import json
from pathlib import Path

from api.main import app as fastapi_app
from api.openapi_export import export_openapi_schema
from api.openapi_markdown import serialize_api_reference_markdown


def test_generated_api_reference_contains_core_routes(tmp_path: Path) -> None:
    out = tmp_path / "openapi.json"
    export_openapi_schema(app=fastapi_app, output_path=out, check=False)

    schema = json.loads(out.read_text(encoding="utf-8"))
    md = serialize_api_reference_markdown(schema)

    assert "## GET /health" in md
    assert "## POST /api/v1/search" in md
    assert "## POST /api/v1/chat" in md
