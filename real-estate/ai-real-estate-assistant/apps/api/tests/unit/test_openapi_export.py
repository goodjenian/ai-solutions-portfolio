from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI

from api.openapi_export import export_openapi_schema


def test_export_openapi_schema_writes_json(tmp_path: Path) -> None:
    app = FastAPI(title="Test API", version="1.0.0")

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"ok": "true"}

    out = tmp_path / "openapi.json"
    export_openapi_schema(app=app, output_path=out, check=False)

    text = out.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert '"openapi"' in text
    assert '"/ping"' in text


def test_export_openapi_schema_check_missing_file(tmp_path: Path) -> None:
    app = FastAPI(title="Test API", version="1.0.0")
    out = tmp_path / "openapi.json"

    with pytest.raises(SystemExit):
        export_openapi_schema(app=app, output_path=out, check=True)


def test_export_openapi_schema_check_detects_drift(tmp_path: Path) -> None:
    app = FastAPI(title="Test API", version="1.0.0")

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"ok": "true"}

    out = tmp_path / "openapi.json"
    out.write_text('{"not":"openapi"}\n', encoding="utf-8")

    with pytest.raises(SystemExit):
        export_openapi_schema(app=app, output_path=out, check=True)


def test_export_openapi_schema_check_passes_when_in_sync(tmp_path: Path) -> None:
    app = FastAPI(title="Test API", version="1.0.0")

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"ok": "true"}

    out = tmp_path / "openapi.json"
    export_openapi_schema(app=app, output_path=out, check=False)

    export_openapi_schema(app=app, output_path=out, check=True)
