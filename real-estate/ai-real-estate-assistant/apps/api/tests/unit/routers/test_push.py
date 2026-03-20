"""
Tests for Push Notification API endpoints.

Task #58: Comprehensive Test Suite Update
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps.auth import get_current_active_user
from api.routers import push
from db.database import get_db


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock()
    user.id = "test-user-123"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_subscription():
    """Create a mock push subscription."""
    sub = MagicMock()
    sub.id = "sub-123"
    sub.user_id = "test-user-123"
    sub.endpoint = "https://fcm.googleapis.com/test"
    sub.p256dh = "test-key"
    sub.auth = "test-auth"
    sub.device_name = "Test Device"
    sub.is_active = True
    sub.created_at = "2024-01-01T00:00:00Z"
    return sub


@pytest.fixture(scope="function")
async def push_client(
    mock_user: MagicMock,
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Create test client for push endpoints."""
    test_app = FastAPI()
    test_app.include_router(push.router, prefix="/api/v1")

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return mock_user

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_active_user] = override_get_current_user

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    test_app.dependency_overrides.clear()


class TestVAPIDPublicKey:
    """Tests for VAPID public key endpoint."""

    @pytest.mark.asyncio
    async def test_get_vapid_public_key(self, push_client: AsyncClient):
        """Verify VAPID endpoint returns public key."""
        response = await push_client.get("/api/v1/push/vapid-public-key")

        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data
        assert "enabled" in data


class TestSubscribe:
    """Tests for push subscription endpoint."""

    @pytest.mark.asyncio
    async def test_subscribe_success(
        self,
        push_client: AsyncClient,
        mock_subscription: MagicMock,
    ):
        """Verify successful subscription."""
        sub_data = {
            "endpoint": "https://fcm.googleapis.com/test",
            "keys": {"p256dh": "test-key", "auth": "test-auth"},
        }

        with patch.object(push.settings, "push_enabled", True):
            with patch("api.routers.push.PushSubscriptionRepository") as repo_cls:
                repo = MagicMock()
                repo.get_by_endpoint = AsyncMock(return_value=None)
                repo.create = AsyncMock(return_value=mock_subscription)
                repo_cls.return_value = repo

                response = await push_client.post(
                    "/api/v1/push/subscribe",
                    json=sub_data,
                )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_subscribe_missing_keys(self, push_client: AsyncClient):
        """Verify error when keys missing."""
        sub_data = {"endpoint": "https://test.com", "keys": {}}

        with patch.object(push.settings, "push_enabled", True):
            response = await push_client.post(
                "/api/v1/push/subscribe",
                json=sub_data,
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_subscribe_disabled(self, push_client: AsyncClient):
        """Verify error when push disabled."""
        sub_data = {
            "endpoint": "https://test.com",
            "keys": {"p256dh": "k", "auth": "a"},
        }

        with patch.object(push.settings, "push_enabled", False):
            response = await push_client.post(
                "/api/v1/push/subscribe",
                json=sub_data,
            )

        assert response.status_code == 503


class TestUnsubscribe:
    """Tests for unsubscription endpoint."""

    @pytest.mark.asyncio
    async def test_unsubscribe_success(
        self,
        push_client: AsyncClient,
        mock_subscription: MagicMock,
    ):
        """Verify successful unsubscription."""
        with patch("api.routers.push.PushSubscriptionRepository") as repo_cls:
            repo = MagicMock()
            repo.get_by_endpoint = AsyncMock(return_value=mock_subscription)
            repo.delete = AsyncMock()
            repo_cls.return_value = repo

            response = await push_client.delete(
                "/api/v1/push/unsubscribe",
                params={"endpoint": "https://test.com"},
            )

        assert response.status_code == 204


class TestListSubscriptions:
    """Tests for listing subscriptions."""

    @pytest.mark.asyncio
    async def test_list_success(
        self,
        push_client: AsyncClient,
        mock_subscription: MagicMock,
    ):
        """Verify listing subscriptions."""
        with patch("api.routers.push.PushSubscriptionRepository") as repo_cls:
            repo = MagicMock()
            repo.get_by_user = AsyncMock(return_value=[mock_subscription])
            repo_cls.return_value = repo

            response = await push_client.get("/api/v1/push/subscriptions")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestDeleteSubscription:
    """Tests for deleting subscription by ID."""

    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        push_client: AsyncClient,
        mock_subscription: MagicMock,
    ):
        """Verify successful deletion."""
        with patch("api.routers.push.PushSubscriptionRepository") as repo_cls:
            repo = MagicMock()
            repo.get_by_id = AsyncMock(return_value=mock_subscription)
            repo.delete = AsyncMock()
            repo_cls.return_value = repo

            response = await push_client.delete("/api/v1/push/subscriptions/sub-123")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_not_found(self, push_client: AsyncClient):
        """Verify 404 for non-existent subscription."""
        with patch("api.routers.push.PushSubscriptionRepository") as repo_cls:
            repo = MagicMock()
            repo.get_by_id = AsyncMock(return_value=None)
            repo_cls.return_value = repo

            response = await push_client.delete("/api/v1/push/subscriptions/nonexistent")

        assert response.status_code == 404
