"""Collections API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps.auth import get_current_active_user
from db.database import get_db
from db.models import User
from db.repositories import CollectionRepository
from db.schemas import (
    CollectionCreate,
    CollectionListResponse,
    CollectionResponse,
    CollectionUpdate,
)

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a collection",
    description="Create a new collection to organize favorited properties.",
)
async def create_collection(
    body: CollectionCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Create a new collection."""
    repo = CollectionRepository(session)
    collection = await repo.create(
        user_id=user.id,
        name=body.name,
        description=body.description,
    )

    # Get favorite count (will be 0 for new collection)
    favorite_count = await repo.count_favorites(collection.id)

    response = CollectionResponse.model_validate(collection)
    response.favorite_count = favorite_count
    return response


@router.get(
    "",
    response_model=CollectionListResponse,
    summary="List user's collections",
    description="Get all collections for the current authenticated user.",
)
async def list_collections(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> CollectionListResponse:
    """Get all collections for the current user."""
    repo = CollectionRepository(session)
    collections = await repo.get_by_user(user.id)

    # Build response with favorite counts
    items = []
    for collection in collections:
        count = await repo.count_favorites(collection.id)
        response = CollectionResponse.model_validate(collection)
        response.favorite_count = count
        items.append(response)

    return CollectionListResponse(items=items, total=len(items))


@router.get(
    "/default",
    response_model=CollectionResponse,
    summary="Get or create default collection",
    description="Get the user's default collection, creating one if it doesn't exist.",
)
async def get_default_collection(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Get or create the user's default collection."""
    repo = CollectionRepository(session)
    collection = await repo.get_or_create_default(user.id)

    favorite_count = await repo.count_favorites(collection.id)
    response = CollectionResponse.model_validate(collection)
    response.favorite_count = favorite_count
    return response


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Get a collection",
    description="Get a specific collection by ID.",
)
async def get_collection(
    collection_id: str,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Get a specific collection."""
    repo = CollectionRepository(session)
    collection = await repo.get_by_id(collection_id, user.id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    favorite_count = await repo.count_favorites(collection.id)
    response = CollectionResponse.model_validate(collection)
    response.favorite_count = favorite_count
    return response


@router.put(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Update a collection",
    description="Update a collection's name or description.",
)
async def update_collection(
    collection_id: str,
    body: CollectionUpdate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Update a collection."""
    repo = CollectionRepository(session)
    collection = await repo.get_by_id(collection_id, user.id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    # Prevent modifying default collection's is_default status
    update_data = body.model_dump(exclude_unset=True)
    if "is_default" in update_data:
        del update_data["is_default"]

    collection = await repo.update(collection, **update_data)

    favorite_count = await repo.count_favorites(collection.id)
    response = CollectionResponse.model_validate(collection)
    response.favorite_count = favorite_count
    return response


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a collection",
    description="Delete a collection. Favorites will become uncategorized.",
)
async def delete_collection(
    collection_id: str,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a collection."""
    repo = CollectionRepository(session)
    collection = await repo.get_by_id(collection_id, user.id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    # Prevent deleting default collection
    if collection.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the default collection",
        )

    await repo.delete(collection)
