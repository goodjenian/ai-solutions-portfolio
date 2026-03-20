from __future__ import annotations

from pathlib import Path

import pytest

from api.openapi_markdown import (
    iter_openapi_operations,
    load_openapi_schema,
    serialize_endpoints_markdown,
)


def _extract_endpoints_section(text: str) -> str:
    text = text.replace("\r\n", "\n")
    anchor = "### Endpoints"
    idx = text.find(anchor)
    assert idx != -1, "### Endpoints anchor missing in docs/api/API_REFERENCE.md"
    return text[idx + len(anchor) :].strip()


def test_api_reference_md_endpoints_in_sync_with_openapi_snapshot() -> None:
    # Navigate from apps/api/tests/integration/api/ to repo root (5 levels up)
    repo_root = Path(__file__).resolve().parents[5]
    schema = load_openapi_schema(repo_root / "docs" / "api" / "openapi.json")
    generated = serialize_endpoints_markdown(schema).strip()

    committed = (repo_root / "docs" / "api" / "API_REFERENCE.md").read_text(encoding="utf-8")
    committed_section = _extract_endpoints_section(committed)
    assert committed_section.startswith(generated[:100])
    assert generated in committed_section


def test_iter_openapi_operations_handles_non_dict_paths_gracefully() -> None:
    """Integration test for iter_openapi_operations with non-dict paths.

    This ensures the early return path (line 85) is covered during integration testing.
    The function should return an empty iterator when paths is not a dict.
    """
    schema = {"paths": "not a dict"}
    result = list(iter_openapi_operations(schema))
    assert result == []


def test_load_openapi_schema_raises_type_error_for_invalid_schema(tmp_path: Path) -> None:
    """Integration test for load_openapi_schema type validation.

    This ensures the type check and error path (lines 21-22) are covered during
    integration testing. The function should raise TypeError when JSON is not a dict.
    """
    schema_path = tmp_path / "invalid_schema.json"
    # Write a JSON array instead of object
    schema_path.write_text('["not", "a", "dict"]\n', encoding="utf-8")
    with pytest.raises(TypeError, match="Expected JSON object, got list"):
        load_openapi_schema(schema_path)
