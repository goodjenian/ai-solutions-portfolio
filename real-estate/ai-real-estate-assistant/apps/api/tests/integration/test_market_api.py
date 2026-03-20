"""Integration tests for market API endpoints.

Task #38: Price History & Trends
"""

import pytest

from db.repositories import PriceSnapshotRepository


class TestMarketAPI:
    """Tests for Market API endpoints."""

    @pytest.mark.asyncio
    async def test_get_price_history_empty(self, async_client, auth_headers):
        """Test getting price history for property with no snapshots."""
        response = await async_client.get(
            "/api/v1/market/price-history/nonexistent-property",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["property_id"] == "nonexistent-property"
        assert data["snapshots"] == []
        assert data["total"] == 0
        assert data["trend"] == "insufficient_data"

    @pytest.mark.asyncio
    async def test_get_price_history_with_data(self, async_client, auth_headers, db_session):
        """Test getting price history for property with snapshots."""
        # Create test snapshots
        repo = PriceSnapshotRepository(db_session)
        await repo.create(property_id="test-prop-1", price=500000.0)
        await repo.create(property_id="test-prop-1", price=510000.0)
        await repo.create(property_id="test-prop-1", price=520000.0)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/market/price-history/test-prop-1",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["property_id"] == "test-prop-1"
        assert len(data["snapshots"]) == 3
        assert data["total"] == 3
        assert data["current_price"] == 520000.0
        assert data["trend"] in ["increasing", "decreasing", "stable"]

    @pytest.mark.asyncio
    async def test_get_price_history_with_limit(self, async_client, auth_headers, db_session):
        """Test getting price history with limit parameter."""
        # Create multiple snapshots
        repo = PriceSnapshotRepository(db_session)
        for i in range(10):
            await repo.create(property_id="test-prop-2", price=500000.0 + (i * 10000))
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/market/price-history/test-prop-2?limit=5",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["snapshots"]) == 5
        assert data["total"] == 10  # Total count should reflect all snapshots

    @pytest.mark.asyncio
    async def test_get_market_trends_default(self, async_client, auth_headers):
        """Test getting market trends with default parameters."""
        response = await async_client.get(
            "/api/v1/market/trends",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "interval" in data
        assert "data_points" in data
        assert "trend_direction" in data
        assert "confidence" in data

    @pytest.mark.asyncio
    async def test_get_market_trends_with_filters(self, async_client, auth_headers):
        """Test getting market trends with filter parameters."""
        response = await async_client.get(
            "/api/v1/market/trends?city=Warsaw&interval=month&months_back=6",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Warsaw"
        assert data["interval"] == "month"

    @pytest.mark.asyncio
    async def test_get_market_trends_quarterly(self, async_client, auth_headers):
        """Test getting market trends with quarterly interval."""
        response = await async_client.get(
            "/api/v1/market/trends?interval=quarter",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["interval"] == "quarter"

    @pytest.mark.asyncio
    async def test_get_market_indicators_default(self, async_client, auth_headers):
        """Test getting market indicators with default parameters."""
        response = await async_client.get(
            "/api/v1/market/indicators",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "overall_trend" in data
        assert "total_listings" in data
        assert "new_listings_7d" in data
        assert "price_drops_7d" in data
        assert "hottest_districts" in data
        assert "coldest_districts" in data

    @pytest.mark.asyncio
    async def test_get_market_indicators_with_city(self, async_client, auth_headers):
        """Test getting market indicators for a specific city."""
        response = await async_client.get(
            "/api/v1/market/indicators?city=Warsaw",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Warsaw"

    @pytest.mark.asyncio
    async def test_get_market_indicators_with_price_drops(
        self, async_client, auth_headers, db_session
    ):
        """Test that market indicators show price drops from snapshots."""
        # Create snapshots showing a price drop
        repo = PriceSnapshotRepository(db_session)
        await repo.create(property_id="prop-1", price=500000.0)
        await repo.create(property_id="prop-1", price=450000.0)  # 10% drop
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/market/indicators",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should have at least 1 price drop detected
        assert data["price_drops_7d"] >= 1

    @pytest.mark.asyncio
    async def test_price_history_requires_auth(self, unauth_client):
        """Test that price history endpoint requires authentication."""
        response = await unauth_client.get("/api/v1/market/price-history/test-prop")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_market_trends_requires_auth(self, unauth_client):
        """Test that market trends endpoint requires authentication."""
        response = await unauth_client.get("/api/v1/market/trends")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_market_indicators_requires_auth(self, unauth_client):
        """Test that market indicators endpoint requires authentication."""
        response = await unauth_client.get("/api/v1/market/indicators")

        assert response.status_code == 401
