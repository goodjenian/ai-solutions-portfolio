from __future__ import annotations

import json
from typing import Any, Iterable


def serialize_chat_sources(
    docs: Iterable[Any],
    *,
    max_items: int,
    max_content_chars: int,
    max_total_bytes: int,
) -> tuple[list[dict[str, Any]], bool]:
    max_items = max(0, int(max_items))
    max_content_chars = max(0, int(max_content_chars))
    max_total_bytes = max(0, int(max_total_bytes))

    sources: list[dict[str, Any]] = []
    total_bytes = 0
    truncated = False

    iterator = iter(docs)
    for doc in iterator:
        # Check max_items limit
        if max_items and len(sources) >= max_items:
            truncated = True
            break

        if doc is None:
            break

        content = getattr(doc, "page_content", "")
        if not isinstance(content, str):
            content = str(content)
        if max_content_chars and len(content) > max_content_chars:
            content = content[:max_content_chars]
            truncated = True

        metadata = getattr(doc, "metadata", {}) or {}
        if not isinstance(metadata, dict):
            metadata = {"value": str(metadata)}

        try:
            json.dumps(metadata, ensure_ascii=False)
            safe_metadata = metadata
        except TypeError:
            safe_metadata = {str(k): str(v) for k, v in metadata.items()}

        item = {"content": content, "metadata": safe_metadata}

        if max_total_bytes:
            encoded = json.dumps(item, ensure_ascii=False).encode("utf-8")
            if total_bytes + len(encoded) > max_total_bytes:
                truncated = True
                break
            total_bytes += len(encoded)

        sources.append(item)

    return sources, truncated


def serialize_web_sources(
    web_sources: Iterable[dict[str, Any]],
    *,
    max_items: int,
    max_content_chars: int,
    max_total_bytes: int,
) -> tuple[list[dict[str, Any]], bool]:
    max_items = max(0, int(max_items))
    max_content_chars = max(0, int(max_content_chars))
    max_total_bytes = max(0, int(max_total_bytes))

    sources: list[dict[str, Any]] = []
    total_bytes = 0
    truncated = False

    iterator = iter(web_sources)
    for raw in iterator:
        # Check max_items limit
        if max_items and len(sources) >= max_items:
            truncated = True
            break

        if raw is None:
            break
        if not isinstance(raw, dict):
            raw = {"value": str(raw)}

        content = str(raw.get("snippet") or raw.get("content") or "").strip()
        if max_content_chars and len(content) > max_content_chars:
            content = content[:max_content_chars]
            truncated = True

        metadata = {k: v for k, v in raw.items() if k not in {"snippet", "content"}}
        try:
            json.dumps(metadata, ensure_ascii=False)
            safe_metadata = metadata
        except TypeError:
            safe_metadata = {str(k): str(v) for k, v in metadata.items()}

        item = {"content": content, "metadata": safe_metadata}

        if max_total_bytes:
            encoded = json.dumps(item, ensure_ascii=False).encode("utf-8")
            if total_bytes + len(encoded) > max_total_bytes:
                truncated = True
                break
            total_bytes += len(encoded)

        sources.append(item)

    return sources, truncated
