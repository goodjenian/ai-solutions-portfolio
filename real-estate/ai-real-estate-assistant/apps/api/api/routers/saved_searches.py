"""Saved searches API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps.auth import get_current_active_user
from db.database import get_db
from db.models import User
from db.repositories import SavedSearchRepository
from db.schemas import (
    SavedSearchCreate,
    SavedSearchListResponse,
    SavedSearchResponse,
    SavedSearchUpdate,
)
from notifications.search_adapter import db_to_pydantic

router = APIRouter(prefix="/saved-searches", tags=["Saved Searches"])


@router.post(
    "",
    response_model=SavedSearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a saved search",
    description="Save a search with filters and alert settings.",
)
async def create_saved_search(
    body: SavedSearchCreate,
    request: Request,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> SavedSearchResponse:
    """Save a search with alert settings."""
    repo = SavedSearchRepository(session)
    search = await repo.create(
        user_id=user.id,
        name=body.name,
        description=body.description,
        filters=body.filters,
        alert_frequency=body.alert_frequency,
        notify_on_new=body.notify_on_new,
        notify_on_price_drop=body.notify_on_price_drop,
    )

    # Sync to scheduler for notifications
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler:
        pydantic_search = db_to_pydantic(search)
        scheduler.add_or_update_search(pydantic_search)

    return SavedSearchResponse.model_validate(search)


@router.get(
    "",
    response_model=SavedSearchListResponse,
    summary="List user's saved searches",
    description="Get all saved searches for the current authenticated user.",
)
async def list_saved_searches(
    include_inactive: bool = Query(default=False, description="Include paused/disabled searches"),
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> SavedSearchListResponse:
    """Get all saved searches for the current user."""
    repo = SavedSearchRepository(session)
    searches = await repo.get_by_user(user.id, include_inactive=include_inactive)
    return SavedSearchListResponse(
        items=[SavedSearchResponse.model_validate(s) for s in searches],
        total=len(searches),
    )


@router.get(
    "/{search_id}",
    response_model=SavedSearchResponse,
    summary="Get a saved search",
    description="Get a specific saved search by ID.",
)
async def get_saved_search(
    search_id: str,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> SavedSearchResponse:
    """Get a specific saved search."""
    repo = SavedSearchRepository(session)
    search = await repo.get_by_id(search_id, user.id)
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found",
        )
    return SavedSearchResponse.model_validate(search)


@router.patch(
    "/{search_id}",
    response_model=SavedSearchResponse,
    summary="Update a saved search",
    description="Update a saved search's name, filters, or alert settings.",
)
async def update_saved_search(
    search_id: str,
    body: SavedSearchUpdate,
    request: Request,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> SavedSearchResponse:
    """Update a saved search."""
    repo = SavedSearchRepository(session)
    search = await repo.get_by_id(search_id, user.id)
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found",
        )

    update_data = body.model_dump(exclude_unset=True)
    search = await repo.update(search, **update_data)

    # Sync to scheduler for notifications
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler:
        pydantic_search = db_to_pydantic(search)
        scheduler.add_or_update_search(pydantic_search)

    return SavedSearchResponse.model_validate(search)


@router.delete(
    "/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved search",
    description="Permanently delete a saved search.",
)
async def delete_saved_search(
    search_id: str,
    request: Request,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a saved search."""
    repo = SavedSearchRepository(session)
    search = await repo.get_by_id(search_id, user.id)
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found",
        )
    await repo.delete(search)

    # Sync to scheduler for notifications
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler:
        scheduler.remove_search(search_id)


@router.post(
    "/{search_id}/toggle-alert",
    response_model=SavedSearchResponse,
    summary="Toggle alert for a saved search",
    description="Enable or disable alerts for a saved search.",
)
async def toggle_alert(
    search_id: str,
    request: Request,
    enabled: bool = Query(default=True, description="Enable or disable"),
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> SavedSearchResponse:
    """Enable or disable alerts for a saved search."""
    repo = SavedSearchRepository(session)
    search = await repo.get_by_id(search_id, user.id)
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found",
        )
    search = await repo.update(search, is_active=enabled)

    # Sync to scheduler for notifications
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler:
        pydantic_search = db_to_pydantic(search)
        scheduler.add_or_update_search(pydantic_search)

    return SavedSearchResponse.model_validate(search)


@router.post(
    "/{search_id}/use",
    response_model=SavedSearchResponse,
    summary="Mark search as used",
    description="Increment usage count when user applies a saved search.",
)
async def mark_search_used(
    search_id: str,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> SavedSearchResponse:
    """Increment usage count when user applies saved search."""
    repo = SavedSearchRepository(session)
    search = await repo.get_by_id(search_id, user.id)
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found",
        )
    await repo.increment_usage(search)
    return SavedSearchResponse.model_validate(search)
