from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI


def build_openapi_schema(app: FastAPI) -> dict[str, Any]:
    return app.openapi()


def serialize_openapi_schema(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def export_openapi_schema(*, app: FastAPI, output_path: Path, check: bool = False) -> None:
    schema = build_openapi_schema(app)
    output_text = serialize_openapi_schema(schema)

    if check:
        if not output_path.exists():
            raise SystemExit(f"OpenAPI schema file missing: {output_path}")
        existing_text = output_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if existing_text != output_text:
            raise SystemExit(
                "OpenAPI schema drift detected. Regenerate with: python scripts\\export_openapi.py"
            )
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")
