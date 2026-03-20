from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from langchain_core.documents import Document

from api.dependencies import get_vector_store
from api.models import ExportPropertiesRequest
from utils.exporters import ExportFormat, PropertyExporter
from vector_store.chroma_store import ChromaPropertyStore

router = APIRouter(tags=["Export"])


def _filename_for_format(export_format: ExportFormat) -> str:
    exporter = PropertyExporter([])
    return exporter.get_filename(export_format, prefix="properties")


def _documents_to_export_rows(documents: List[Document]) -> List[dict]:
    rows: List[dict] = []
    for doc in documents:
        metadata = dict(doc.metadata or {})
        if "id" not in metadata:
            metadata["id"] = "unknown"
        rows.append(metadata)
    return rows


@router.post("/export/properties", tags=["Export"])
async def export_properties(
    request: ExportPropertiesRequest,
    store: Annotated[Optional[ChromaPropertyStore], Depends(get_vector_store)],
):
    if not store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store is not available",
        )

    documents: List[Document]
    if request.property_ids:
        documents = store.get_properties_by_ids(request.property_ids)
    else:
        assert request.search is not None
        results = store.hybrid_search(
            query=request.search.query,
            k=request.search.limit,
            filters=request.search.filters,
            alpha=request.search.alpha,
            lat=request.search.lat,
            lon=request.search.lon,
            radius_km=request.search.radius_km,
            min_lat=request.search.min_lat,
            max_lat=request.search.max_lat,
            min_lon=request.search.min_lon,
            max_lon=request.search.max_lon,
            sort_by=request.search.sort_by.value if request.search.sort_by else None,
            sort_order=(request.search.sort_order.value if request.search.sort_order else None),
        )
        documents = [doc for doc, _score in results]

    rows = _documents_to_export_rows(documents)
    exporter = PropertyExporter(rows)
    filename = _filename_for_format(request.format)

    try:
        if request.format == ExportFormat.CSV:
            content = exporter.export_to_csv(
                columns=request.columns,
                include_header=request.include_header,
                delimiter=request.csv_delimiter,
                decimal=request.csv_decimal,
            )
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        if request.format == ExportFormat.JSON:
            content = exporter.export_to_json(
                pretty=request.pretty,
                include_metadata=request.include_metadata,
                columns=request.columns,
            )
            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        if request.format == ExportFormat.MARKDOWN:
            content = exporter.export_to_markdown(
                include_summary=request.include_summary,
                max_properties=request.max_properties,
            )
            return Response(
                content=content,
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        if request.format == ExportFormat.EXCEL:
            buf = exporter.export_to_excel(
                include_summary=request.include_summary,
                include_statistics=request.include_statistics,
                columns=request.columns,
            )
            return StreamingResponse(
                buf,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        if request.format == ExportFormat.PDF:
            buf = exporter.export_to_pdf()
            return StreamingResponse(
                buf,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported export format")
