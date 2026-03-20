from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

HTTP_METHOD_ORDER: list[str] = [
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
    "trace",
]


def load_openapi_schema(schema_path: Path) -> dict[str, Any]:
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"Expected JSON object, got {type(data).__name__}")
    return data


def export_api_reference_markdown(
    *, schema_path: Path, output_path: Path, check: bool = False
) -> None:
    schema = load_openapi_schema(schema_path)
    output_text = serialize_api_reference_markdown(schema)

    if check:
        if not output_path.exists():
            raise SystemExit(f"Generated API reference file missing: {output_path}")
        existing_text = output_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if existing_text != output_text:
            raise SystemExit(
                "Generated API reference drift detected. Regenerate with: "
                "python scripts\\docs\\generate_api_reference.py"
            )
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")


def serialize_api_reference_markdown(schema: dict[str, Any]) -> str:
    title = schema.get("info", {}).get("title", "API")
    version = schema.get("info", {}).get("version", "")

    header = [
        "# API Reference (Generated)",
        "",
        "This file is generated from the committed OpenAPI schema snapshot (`docs/api/openapi.json`).",
        f"- Source title: {title}",
        f"- Source version: {version}" if version else "- Source version: (unknown)",
        "",
        "To regenerate:",
        "",
        "```powershell",
        "python scripts\\docs\\export_openapi.py",
        "python scripts\\docs\\generate_api_reference.py",
        "```",
        "",
        "---",
        "",
    ]

    blocks: list[str] = ["\n".join(header)]
    for path, method, operation in iter_openapi_operations(schema):
        blocks.append(render_operation_block(path=path, method=method, operation=operation))
    return "\n".join(blocks).rstrip() + "\n"


def serialize_endpoints_markdown(schema: dict[str, Any]) -> str:
    blocks: list[str] = []
    for path, method, operation in iter_openapi_operations(schema):
        blocks.append(render_operation_block(path=path, method=method, operation=operation))
    return "\n".join(blocks).rstrip() + "\n"


def iter_openapi_operations(schema: dict[str, Any]) -> Iterable[tuple[str, str, dict[str, Any]]]:
    paths = schema.get("paths", {})
    if not isinstance(paths, dict):
        return

    for path in sorted(paths.keys()):
        item = paths.get(path, {})
        if not isinstance(item, dict):
            continue
        methods = [m for m in item.keys() if isinstance(m, str)]
        for method in _sort_http_methods(methods):
            operation = item.get(method)
            if isinstance(operation, dict):
                yield path, method.lower(), operation


def _sort_http_methods(methods: list[str]) -> list[str]:
    normalized = [m.lower() for m in methods]
    known = [m for m in HTTP_METHOD_ORDER if m in normalized]
    unknown = sorted([m for m in normalized if m not in HTTP_METHOD_ORDER])
    return known + unknown


def render_operation_block(*, path: str, method: str, operation: dict[str, Any]) -> str:
    method_upper = method.upper()
    summary = _normalize_text(operation.get("summary"))
    description = _normalize_text(operation.get("description"))
    tags = operation.get("tags", [])
    tag_text = ", ".join([t for t in tags if isinstance(t, str)])

    lines: list[str] = [f"## {method_upper} {path}", ""]
    if summary:
        lines.extend([f"**Summary**: {summary}", ""])
    if tag_text:
        lines.extend([f"**Tags**: {tag_text}", ""])
    if description:
        lines.extend([description, ""])

    parameters = operation.get("parameters", [])
    if isinstance(parameters, list) and parameters:
        rendered = render_parameters_table(parameters)
        if rendered:
            lines.extend(["**Parameters**", "", rendered, ""])

    request_body = operation.get("requestBody")
    if isinstance(request_body, dict):
        rendered_rb = render_request_body(request_body)
        if rendered_rb:
            lines.extend(["**Request Body**", "", rendered_rb, ""])

    responses = operation.get("responses", {})
    if isinstance(responses, dict) and responses:
        rendered_resp = render_responses(responses)
        if rendered_resp:
            lines.extend(["**Responses**", "", rendered_resp, ""])

    return "\n".join(lines).rstrip() + "\n"


def render_parameters_table(parameters: list[dict[str, Any]]) -> str:
    rows: list[tuple[str, str, str, str, str]] = []
    for param in parameters:
        if not isinstance(param, dict):
            continue
        name = str(param.get("name", "")).strip()
        location = str(param.get("in", "")).strip()
        required = "yes" if bool(param.get("required")) else "no"
        schema = param.get("schema", {})
        type_text = schema_type(schema) if isinstance(schema, dict) else ""
        desc = _normalize_text(param.get("description"))
        if not name:
            continue
        rows.append((name, location, type_text, required, desc))

    if not rows:
        return ""

    lines = [
        "| Name | In | Type | Required | Description |",
        "|---|---|---|---|---|",
    ]
    for name, location, type_text, required, desc in rows:
        lines.append(
            f"| {_escape_md(name)} | {_escape_md(location)} | {_escape_md(type_text)} | {required} | {_escape_md(desc)} |"
        )
    return "\n".join(lines)


def render_request_body(request_body: dict[str, Any]) -> str:
    required = "yes" if bool(request_body.get("required")) else "no"
    content = request_body.get("content", {})
    if not isinstance(content, dict) or not content:
        return ""

    lines: list[str] = [f"- Required: {required}"]
    for content_type in sorted([k for k in content.keys() if isinstance(k, str)]):
        media = content.get(content_type, {})
        if not isinstance(media, dict):
            continue
        schema = media.get("schema", {})
        schema_text = schema_type(schema) if isinstance(schema, dict) else ""
        lines.append(f"- {content_type}: {schema_text}".rstrip())
    return "\n".join(lines)


def render_responses(responses: dict[str, Any]) -> str:
    rows: list[tuple[str, str, str]] = []
    for status_code in sorted([k for k in responses.keys() if isinstance(k, str)]):
        resp = responses.get(status_code, {})
        if not isinstance(resp, dict):
            continue
        desc = _normalize_text(resp.get("description"))
        content = resp.get("content", {})
        schema_text = ""
        if isinstance(content, dict) and content:
            json_media = content.get("application/json")
            if isinstance(json_media, dict):
                schema = json_media.get("schema", {})
                if isinstance(schema, dict):
                    schema_text = schema_type(schema)
        rows.append((status_code, desc, schema_text))

    if not rows:
        return ""

    lines = [
        "| Status | Description | Body (application/json) |",
        "|---|---|---|",
    ]
    for status_code, desc, schema_text in rows:
        lines.append(
            f"| {_escape_md(status_code)} | {_escape_md(desc)} | {_escape_md(schema_text)} |"
        )
    return "\n".join(lines)


def schema_type(schema: dict[str, Any]) -> str:
    if "$ref" in schema and isinstance(schema["$ref"], str):
        return _ref_name(schema["$ref"])

    if "oneOf" in schema and isinstance(schema["oneOf"], list):
        return " | ".join([schema_type(s) for s in schema["oneOf"] if isinstance(s, dict)])
    if "anyOf" in schema and isinstance(schema["anyOf"], list):
        return " | ".join([schema_type(s) for s in schema["anyOf"] if isinstance(s, dict)])

    t = schema.get("type")
    if isinstance(t, str):
        if t == "array":
            items = schema.get("items", {})
            if isinstance(items, dict):
                return f"array[{schema_type(items)}]"
            return "array"
        return t

    if "enum" in schema and isinstance(schema["enum"], list):
        enum_values = [repr(v) for v in schema["enum"][:8]]
        more = "…" if len(schema["enum"]) > 8 else ""
        return f"enum({', '.join(enum_values)}{more})"

    return "object"


def _ref_name(ref: str) -> str:
    return ref.split("/")[-1].strip() or ref


def _normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())


def _escape_md(value: str) -> str:
    return value.replace("\n", " ").replace("|", "\\|").strip()
