"""
API endpoints for market anomaly detection and management.

Provides CRUD operations for:
- List anomalies with filters
- Get anomaly by ID
- Dismiss an anomaly
- Get anomaly statistics

Also provides real-time updates via SSE:
"""

import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps.auth import get_current_active_user
from db import AnomalyRepository, PriceSnapshotRepository
from db.database import get_db
from db.schemas import (
    AnomalyDismissRequest,
    AnomalyListResponse,
    AnomalyResponse,
    AnomalyStatsResponse,
    UserResponse,
)
from services.anomaly_service import AnomalyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


def get_anomaly_service(db: AsyncSession) -> AnomalyService:
    """Get anomaly service instance."""
    anomaly_repo = AnomalyRepository(db)
    price_snapshot_repo = PriceSnapshotRepository(db)
    return AnomalyService(
        anomaly_repo=anomaly_repo,
        price_snapshot_repo=price_snapshot_repo,
    )


@router.get("", response_model=AnomalyListResponse)
async def list_anomalies(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    anomaly_type: Optional[str] = Query(None, description="Filter by anomaly type"),
    scope_type: Optional[str] = Query(None, description="Filter by scope type"),
    scope_id: Optional[str] = Query(None, description="Filter by scope ID"),
    limit: int = Query(50, ge=1, le=100, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AnomalyListResponse:
    """List market anomalies with optional filters."""
    anomaly_service = get_anomaly_service(db)
    return await anomaly_service.get_anomalies(
        limit=limit,
        offset=offset,
        severity_filter=severity,
        anomaly_type_filter=anomaly_type,
        scope_type_filter=scope_type,
        scope_id_filter=scope_id,
    )


@router.get("/stats", response_model=AnomalyStatsResponse)
async def get_anomaly_stats(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AnomalyStatsResponse:
    """Get anomaly statistics summary."""
    anomaly_service = get_anomaly_service(db)
    return await anomaly_service.get_anomaly_stats()


@router.get("/{anomaly_id}", response_model=AnomalyResponse)
async def get_anomaly(
    anomaly_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AnomalyResponse:
    """Get a specific anomaly by ID."""
    anomaly_service = get_anomaly_service(db)
    anomaly = await anomaly_service.get_anomaly_by_id(anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return anomaly


@router.post("/{anomaly_id}/dismiss")
async def dismiss_anomaly(
    anomaly_id: str,
    request: AnomalyDismissRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Dismiss an anomaly."""
    anomaly_service = get_anomaly_service(db)
    user_id = current_user.id if current_user else None
    success = await anomaly_service.dismiss_anomaly(
        anomaly_id=anomaly_id,
        dismissed_by=user_id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return {"success": True, "message": f"Anomaly {anomaly_id} dismissed"}


@router.get("/stream")
async def stream_anomalies(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream real-time anomaly updates via Server-Sent Events.

    This endpoint establishes a long-lived connection for pushing
    real-time anomaly detections to connected clients.
    """
    anomaly_service = get_anomaly_service(db)

    async def event_generator():
        """Generate SSE events for new anomalies."""
        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"

        while True:
            try:
                # Get recent undismissed anomalies (critical only for alerts)
                anomalies = await anomaly_service.get_recent_anomalies(
                    limit=10,
                    severity_filter="critical",
                )

                for anomaly in anomalies:
                    yield f"data: {json.dumps(anomaly)}\n\n"

                # Wait before next check
                await asyncio.sleep(5)

            except asyncio.CancelledError:
                logger.info("Anomaly stream connection closed")
                yield f"data: {json.dumps({'type': 'disconnected'})}\n\n"
                break

            except Exception as e:
                logger.error(f"Error in anomaly stream: {e}")
                yield (f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n")
                await asyncio.sleep(10)  # Wait longer on error

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
